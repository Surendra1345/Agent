
import hashlib
import json
import logging
from pathlib import Path
import re
from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from sqlalchemy import select
from sqlalchemy.orm import Session

from agent.config.database import engine
from agent.model.model import Contract, ContractRule
from agent.schemas.schema import InvoiceDetails
from agent.services.contract_db import find_contract_by_name, find_contract_by_hash, save_contract_to_db
from agent.services.contract_extract import extract_contract_details, extract_contract_details_from_pdf
from agent.services.contract_review import review_contract_with_search
from agent.services.document_classify import classify_document
from agent.services.graph_state import AgentState
from agent.services.invoice_db import save_invoice_details_to_db, validate_invoice_details
from agent.services.invoice_extract import extract_invoice_details_from_pdf
from agent.services.llm import MODEL, TEMPERATURE, api_key
from agent.services.text_to_sql import query_contracts_with_llm
from agent.tools.contract_tools import save_contract_tool
from agent.tools.search_tool import search_rulebook_tool
from agent.utils.document_parser import extract_text

BASE_DIR = Path(__file__).resolve().parents[3]
logger = logging.getLogger("graph_agent")

chat_llm = ChatOpenAI(
    model=MODEL,
    temperature=TEMPERATURE,
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1", 
)


# =====================================================================
# Routing (Generic Intent Classification)
# =====================================================================
def router_node(state: AgentState) -> dict:
    return {}


def classify_intent(user_msg: str, has_pending_action: bool = False, has_active_doc: bool = False) -> Literal["save_node", "cancel_node", "sql_agent_node", "general_agent_node"]:
    """Generic natural language intent classifier replacing brittle keyword lists."""
    msg = user_msg.strip()
    if not msg:
        return "general_agent_node"

    clean_lower = msg.lower()

    # Fast-path for clear 1-word confirmation / cancellation
    if has_pending_action:
        if clean_lower in {"yes", "confirm", "approve", "proceed", "save", "save it", "store", "persist"}:
            return "save_node"
        if clean_lower in {"no", "cancel", "stop", "abort", "discard", "reject", "dont save", "don't save"}:
            return "cancel_node"

    prompt = f"""You are a routing intent classifier for an enterprise Construction Contract & Invoice AI Agent.
Analyze the user's natural language message and pick the single best destination node:

1. "sql_agent_node": User wants to query, check, search, count, list, filter, or retrieve contracts or invoices stored in the database.
   Examples: "do we have any invoices in the system?", "are there any contracts above 1 crore?", "show all invoices", "how many contracts do we have?", "check if we have any pending bills", "list all records".

2. "save_node": User explicitly confirms saving/recording/storing the currently reviewed document into the database.
   Examples: "yes save this contract", "please store it in database", "confirm save".

3. "cancel_node": User rejects or cancels an action.
   Examples: "no cancel", "abort", "don't save".

4. "general_agent_node": User is asking about company rules, contract clauses, summarizing a document, construction concepts, legal terms, or general questions.
   Examples: "summarize this contract", "what is retention money?", "get me the rules of the company", "explain liquidated damages", "what can you do?".

Context:
- Has Pending Save Action: {has_pending_action}
- Has Active Document in Session: {has_active_doc}
- User Message: "{msg}"

Respond with ONLY the exact node name: "sql_agent_node", "save_node", "cancel_node", or "general_agent_node".
"""
    try:
        response = chat_llm.invoke([
            SystemMessage(content="You are a routing classifier. Output ONLY the exact node name, nothing else."),
            HumanMessage(content=prompt)
        ])
        decision = response.content.strip().replace('"', '').replace("'", "").lower()
        for valid in ["sql_agent_node", "save_node", "cancel_node", "general_agent_node"]:
            if valid in decision:
                logger.info(f"[Router] Intent classified '{msg[:50]}' -> {valid}")
                return valid
    except Exception as e:
        logger.error(f"Intent classification failed: {e}", exc_info=True)

    return "general_agent_node"


def route_decision(state: AgentState) -> Literal["classifier_node", "save_node", "cancel_node", "sql_agent_node", "general_agent_node"]:
    if state.get("file_path"):
        logger.info(f"[Router] New file uploaded -> classifier_node ({state.get('file_path')})")
        return "classifier_node"

    messages = state.get("messages", [])
    last_msg = (messages[-1].content if messages and hasattr(messages[-1], "content") else str(messages[-1] if messages else "")).strip()

    has_pending = bool(state.get("pending_action"))
    has_active_doc = bool(state.get("contract") or state.get("invoice"))

    return classify_intent(last_msg, has_pending_action=has_pending, has_active_doc=has_active_doc)

# =====================================================================
# Document Classification
# =====================================================================
def classifier_node(state: AgentState) -> dict:
    file_path = state.get("file_path")
    if not file_path:
        return {"output_message": "No file found for classification."}
    doc_type = classify_document(extract_text(file_path)).document_type
    logger.info(f"[Classifier] File '{file_path}' classified as: '{doc_type}'")
    return {"document_type": doc_type}


def route_doc_type(state: AgentState) -> Literal["contract_auditor_node", "invoice_validator_node", "general_agent_node"]:
    doc_type = state.get("document_type")
    return "contract_auditor_node" if doc_type == "contract" else ("invoice_validator_node" if doc_type == "invoice" else "general_agent_node")


# =====================================================================
# Contract Auditor Node
# =====================================================================
def contract_auditor_node(state: AgentState) -> dict:
    file_path, file_url = state.get("file_path"), state.get("file_url")

    # 1. Calculate SHA-256 hash FIRST
    with open(file_path, "rb") as f:
        doc_hash = hashlib.sha256(f.read()).hexdigest()

    # 2. Check cache FIRST
    cached = find_contract_by_hash(doc_hash)
    if cached:
        contract_data = cached["contract"]
        if file_url:
            contract_data["file_url"] = file_url
        flags = cached["flags"]
        logger.info(f"contract document was already reviewed and stored in the DB.")
        return {
            "contract": contract_data,
            "contract_id": cached["contract_id"],
            "review": {"flags": flags, "status": "Cached Review Complete", "summary": f"Retrieved {len(flags)} compliance flags from database cache."},
            "file_url": file_url,
            "file_path": None,
            "invoice": None,
            "validation": None,
            "document_type": "contract",
            "action": "review_contract",
            "pending_action": None,
            "already_saved": True,
            "output_message": f"Contract '{contract_data.get('contract_name')}' already exists in database (ID: {cached['contract_id']}). Loaded {len(flags)} compliance flag(s) from cache without re-running analysis.",
        }

    # 3. Cache MISS -> Only now run PDF extraction + pgvector + LLM
    logger.info("New contract document or updated contract document")
    raw_text = extract_text(file_path)
    contract = extract_contract_details(raw_text)
    contract_data = contract.model_dump(mode="json")
    contract_data["document_hash"] = doc_hash
    if file_url:
        contract_data["file_url"] = file_url

    existing = find_contract_by_name(contract.contract_name)
    existing_id = existing.contract_id if existing else None
    review = review_contract_with_search(contract)
    flags_count = len(review.flags)

    if existing:
        msg = f"Contract '{contract.contract_name}' was reviewed. Recorded in DB (ID: {existing_id}). Found {flags_count} compliance flag(s)."
        pending, already_saved = None, True
    else:
        msg = f"Contract '{contract.contract_name}' review complete. Found {flags_count} flag(s). Would you like to save this contract to the database?"
        pending, already_saved = "confirm_save_contract", False

    return {
        "contract": contract_data,
        "contract_id": existing_id,
        "review": review.model_dump(mode="json"),
        "file_url": file_url,
        "file_path": None,
        "invoice": None,
        "validation": None,
        "document_type": "contract",
        "action": "review_contract",
        "pending_action": pending,
        "already_saved": already_saved,
        "output_message": msg,
    }

            
            


# =====================================================================
# Invoice Validator Node
# =====================================================================
def invoice_validator_node(state: AgentState) -> dict:
    file_path = state.get("file_path")
    invoice = extract_invoice_details_from_pdf(file_path)
    validation, contract_id = validate_invoice_details(invoice)
    issues_count = len(validation.issues)
    msg = f"Invoice '{invoice.invoice_id}' validated against Contract '{contract_id or 'Unknown'}'. Found {issues_count} issue flag(s). Would you like to record this invoice in the database?"

    logger.info(f"invoice validation process is done")
    return {
        "invoice": invoice.model_dump(mode="json"), "contract_id": contract_id,
        "validation": validation.model_dump(mode="json"), "file_path": None,
        "contract": None, "review": None, "document_type": "invoice",
        "action": "validate_invoice", "pending_action": "confirm_save_invoice",
        "already_saved": False, "output_message": msg,
    }


# =====================================================================
# SQL Agent Node
# =====================================================================
def sql_agent_node(state: AgentState) -> dict:
    messages = state.get("messages", [])
    last_msg = messages[-1].content if messages and hasattr(messages[-1], "content") else str(messages[-1] if messages else "")
    try:
        rows, sql = query_contracts_with_llm(last_msg)
        logger.info(f"query is done")
        return {"action": "text_to_sql", "sql_query": sql, "sql_results": rows, "sql_error": None, "output_message": f"Query completed. Found {len(rows)} record(s) matching your request."}
    except Exception as exc:
        logger.error(f"sql agent failed", exc_info=True)
        return {"action": "text_to_sql", "sql_query": None, "sql_results": [], "sql_error": str(exc), "output_message": f"Could not execute query: {str(exc)}"}


# =====================================================================
# Persistence Helpers & Save Node
# =====================================================================
def _save_invoice(state: AgentState, invoice_data: dict) -> dict:
    inv_id = invoice_data.get("invoice_id", "UNKNOWN")
    if state.get("already_saved"):
        return {"action": "save_invoice", "invoice": invoice_data, "contract_id": state.get("contract_id"), "pending_action": None, "already_saved": True, "output_message": f"This invoice ('{inv_id}') has already been saved. No duplicate created."}
    try:
        inv_obj = InvoiceDetails.model_validate(invoice_data)
        res = save_invoice_details_to_db(inv_obj)
        logger.info(f"invoice is saved successfully")
        return {"action": "save_invoice", "invoice": invoice_data, "contract_id": state.get("contract_id"), "pending_action": None, "already_saved": True, "save_result": res.model_dump(mode="json"), "output_message": f"Invoice '{inv_obj.invoice_id}' (Status: Pending)."}
    except Exception as exc:
        logger.error(f"Failed to save invoice", exc_info=True)
        return {"action": "save_invoice", "invoice": invoice_data, "output_message": f"Failed to save invoice '{inv_id}': {str(exc)}"}


def _save_contract(state: AgentState, contract_data: dict) -> dict:
    cname = contract_data.get("contract_name") or "Unnamed Contract"
    saved_id = state.get("contract_id") or contract_data.get("contract_id")
    if state.get("already_saved") and saved_id:
        return {"action": "save_contract", "contract": contract_data, "contract_id": saved_id, "pending_action": None, "already_saved": True, "output_message": f"This contract ('{cname}') has already been saved (ID: {saved_id})."}
    try:
        review_data = state.get("review") or {}
        flags_list = review_data.get("flags") or []
        res = save_contract_tool(
            contract_name=cname,
            contract_amount=float(contract_data.get("contract_amount") or 0.0),
            tax_rate=float(contract_data.get("tax_rate") or 0.0),
            effective_date=str(contract_data.get("effective_date")) if contract_data.get("effective_date") else None,
            completion_date=str(contract_data.get("completion_date")) if contract_data.get("completion_date") else None,
            file_url=contract_data.get("file_url") or state.get("file_url"),
            contract_id=state.get("contract_id"),
            document_hash=contract_data.get("document_hash"),
            flags=flags_list,
        )
        cid = res.get("contract_id")
        logger.info("Saved contract details successfully")
        return {"action": "save_contract", "contract": contract_data, "contract_id": cid, "pending_action": None, "already_saved": True, "save_result": res, "output_message": f"Contract '{cname}' saved successfully (Contract ID: {cid})."}
    except Exception as exc:
        logger.error("Failed to save contract details", exc_info=True)
        return {"action": "save_contract", "contract": contract_data, "output_message": f"Failed to save contract '{cname}': {str(exc)}"}


def save_node(state: AgentState) -> dict:
    pending, contract_data, invoice_data = state.get("pending_action"), state.get("contract"), state.get("invoice")
    messages = state.get("messages", [])
    last_msg = (messages[-1].content if messages and hasattr(messages[-1], "content") else str(messages[-1] if messages else "")).lower()

    is_explicit_invoice = any(w in last_msg for w in ["invoice", "invoices"])
    is_explicit_contract = any(w in last_msg for w in ["contract", "contracts"])

    # Safety Mismatch Guard: Prevent cross-saving an invoice as a contract or vice versa
    if is_explicit_contract and not is_explicit_invoice:
        if pending == "confirm_save_invoice" or (invoice_data and not contract_data):
            inv_id = (invoice_data or {}).get("invoice_id", "Unknown")
            logger.warning(f"Saving the invoice is blocked because uploaded document is invoice and user is asking to save contract details.")
            return {"action": "general", "pending_action": pending, "output_message": f"You requested to save contract details, but the uploaded document in this session is an invoice ('{inv_id}'). The invoice was NOT saved. If you want to save this invoice, type 'save the invoice' or 'yes'."}
        if not contract_data:
            return {"action": "general", "output_message": "No active contract details found in this session to save. Please upload a contract PDF first."}

    if is_explicit_invoice and not is_explicit_contract:
        if pending == "confirm_save_contract" or (contract_data and not invoice_data):
            cname = (contract_data or {}).get("contract_name", "Unknown")
            logger.warning(f"Saving the contract is blocked because uploaded document is contract and the user is asking to save the invoice details.")
            return {"action": "general", "pending_action": pending, "output_message": f"You requested to save invoice details, but the uploaded document in this session is a contract ('{cname}'). The contract was NOT saved. If you want to save this contract, type 'save the contract' or 'yes'."}
        if not invoice_data:
            return {"action": "general", "output_message": "No active invoice details found in this session to save. Please upload an invoice PDF first."}

    # Resolve target entity
    save_invoice_now = False
    if is_explicit_invoice and invoice_data:
        save_invoice_now = True
    elif is_explicit_contract and contract_data:
        save_invoice_now = False
    elif pending == "confirm_save_invoice" and invoice_data:
        save_invoice_now = True
    elif pending == "confirm_save_contract" and contract_data:
        save_invoice_now = False
    elif invoice_data and not contract_data:
        save_invoice_now = True

    if save_invoice_now and invoice_data:
        return _save_invoice(state, invoice_data)
    if contract_data:
        return _save_contract(state, contract_data)

    return {"action": "general", "output_message": "No active document found in this session to save. Please upload a PDF first."}


# =====================================================================
# Cancel & General Q&A Nodes
# =====================================================================
def cancel_node(state: AgentState) -> dict:
    logger.info("Pending save action cancelled.")
    return {"pending_action": None, "output_message": "Operation cancelled. The document was not saved to the database."}


def _get_company_rules(user_query: str = "") -> str:
    """Retrieve official company contract compliance rules directly from PostgreSQL or via search."""
    q_lower = user_query.lower()
    is_rules_request = any(
        phrase in q_lower
        for phrase in [
            "rule", "rules", "policy", "policies", "guideline", "guidelines",
            "standard", "standards", "compliance", "all rules", "company rules",
            "rules of", "what are the rules", "get me the rules", "list rules",
            "show rules", "tell me the rules", "rulebook"
        ]
    )

    # 1. Broad inquiry -> fetch directly from database for 100% complete accuracy
    if is_rules_request:
        try:
            with Session(engine) as session:
                rows = session.scalars(select(ContractRule).order_by(ContractRule.id)).all()
                if rows:
                    seen = set()
                    rules_text = []
                    for r in rows:
                        key = (r.section or "", (r.content or "").strip()[:60])
                        if key not in seen:
                            seen.add(key)
                            sec = r.section or "Rule"
                            rules_text.append(f"**Rule {sec}**:\n{r.content}")
                    if rules_text:
                        logger.info(f"Retrieved {len(rules_text)} official company rules from PostgreSQL.")
                        return "\n\n---\n\n".join(rules_text)
        except Exception as e:
            logger.error(f"Failed to fetch contract_rules from database: {e}", exc_info=True)

    # 2. Semantic search for targeted policy questions
    if user_query.strip():
        try:
            rules = search_rulebook_tool(user_query, top_k=6)
            if rules:
                return "\n\n---\n\n".join(
                    f"**Rule {r.get('section', 'Rule')}**:\n{r.get('content')}"
                    for r in rules if r.get("content")
                )
        except Exception as e:
            logger.error(f"Semantic search_rulebook_tool failed: {e}", exc_info=True)

    # 3. Fallback: Always provide all company rules if rule search yielded nothing
    try:
        with Session(engine) as session:
            rows = session.scalars(select(ContractRule).order_by(ContractRule.id)).all()
            if rows:
                seen = set()
                rules_text = []
                for r in rows:
                    key = (r.section or "", (r.content or "").strip()[:60])
                    if key not in seen:
                        seen.add(key)
                        rules_text.append(f"**Rule {r.section or 'Rule'}**:\n{r.content}")
                return "\n\n---\n\n".join(rules_text)
    except Exception as e:
        logger.error(f"Fallback retrieval of contract_rules failed: {e}", exc_info=True)

    return ""


STOP_WORDS = {"and", "for", "the", "with", "from", "that", "this", "about"}
GENERIC_WORDS = {"construction", "contract", "agreement", "services", "project", "private", "limited", "pvt", "ltd", "summarize", "summary", "clause", "clauses"}


def _resolve_contract_pdf(contract_name: str, file_url: str | None = None) -> Path | None:
    """Finds the local PDF file path for a contract by URL or best token overlap."""
    uploads_dir = BASE_DIR / "uploads" / "contracts"

    # 1. Try file_url directly
    if file_url:
        fname = Path(file_url).name
        candidate = uploads_dir / fname
        if candidate.exists() and candidate.is_file():
            return candidate
        candidate_rel = BASE_DIR / file_url.lstrip("/\\")
        if candidate_rel.exists() and candidate_rel.is_file():
            return candidate_rel

    # 2. Search uploads/contracts/ by highest distinctive token overlap
    if uploads_dir.exists():
        tokens = {w for w in re.findall(r"[a-z0-9]+", contract_name.lower()) if len(w) > 3 and w not in STOP_WORDS and w not in GENERIC_WORDS}
        best_pdf, best_score = None, 0
        for pdf_file in uploads_dir.glob("*.pdf"):
            stem_tokens = set(re.findall(r"[a-z0-9]+", pdf_file.stem.lower())) - GENERIC_WORDS
            overlap = len(tokens & stem_tokens)
            if overlap > best_score:
                best_score = overlap
                best_pdf = pdf_file
        if best_pdf and best_score >= 1:
            return best_pdf

    return None


def _find_contract_for_query(query_text: str):
    """Smart lookup: Matches contract in PostgreSQL or local PDF by specific company and project name."""
    q_tokens = set(re.findall(r"[a-z0-9]+", query_text.lower()))
    best_contract = None
    best_overlap = 0

    # 1. Search PostgreSQL contracts table
    try:
        with Session(engine) as session:
            for c in session.scalars(select(Contract)).all():
                if not c.contract_name:
                    continue
                cname = c.contract_name.lower().strip()
                # Skip meaningless generic names
                if cname in {"construction contract agreement", "string", "contract", "test"}:
                    continue
                c_words = {w for w in re.findall(r"[a-z0-9]+", cname) if len(w) > 3 and w not in STOP_WORDS and w not in GENERIC_WORDS}
                if not c_words:
                    continue
                overlap = len(c_words & q_tokens)
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_contract = {
                        "contract_id": c.contract_id,
                        "contract_name": c.contract_name,
                        "contract_amount": float(c.contract_amount) if c.contract_amount else None,
                        "tax_rate": float(c.tax_rate) if c.tax_rate else None,
                        "start_date": str(c.start_date) if c.start_date else None,
                        "end_date": str(c.end_date) if c.end_date else None,
                        "file_url": c.file_url,
                    }
    except Exception as e:
        logger.error(f"Error querying contracts table: {e}", exc_info=True)

    if best_contract and best_overlap >= 1:
        return best_contract

    # 2. Search local uploads/contracts/ folder
    uploads_dir = BASE_DIR / "uploads" / "contracts"
    if uploads_dir.exists():
        best_pdf, best_pdf_score = None, 0
        for pdf_file in uploads_dir.glob("*.pdf"):
            stem_tokens = set(re.findall(r"[a-z0-9]+", pdf_file.stem.lower())) - GENERIC_WORDS
            overlap = len(stem_tokens & q_tokens)
            if overlap > best_pdf_score:
                best_pdf_score = overlap
                best_pdf = pdf_file
        if best_pdf and best_pdf_score >= 1:
            return best_pdf

    return None


def general_agent_node(state: AgentState) -> dict:
    messages = state.get("messages", [])
    last_msg = messages[-1].content if messages and hasattr(messages[-1], "content") else str(messages[-1] if messages else "")

    context = []
    if state.get("contract"):
        context.append(f"Active Contract:\n{json.dumps(state.get('contract'), indent=2)}")
    if state.get("invoice"):
        context.append(f"Active Invoice:\n{json.dumps(state.get('invoice'), indent=2)}")

    # Smart Auto-Fetch: Look up contract by name or file from PostgreSQL/disk
    match = _find_contract_for_query(last_msg)
    if isinstance(match, dict):
        context.append(
            f"Saved Contract Data (PostgreSQL):\n"
            f"- Contract ID: {match.get('contract_id')}\n"
            f"- Name: {match.get('contract_name')}\n"
            f"- Amount: ₹{match.get('contract_amount')}\n"
            f"- Tax Rate: {match.get('tax_rate')}%\n"
            f"- Period: {match.get('start_date')} to {match.get('end_date')}"
        )
        pdf_path = _resolve_contract_pdf(match.get("contract_name", ""), match.get("file_url"))
        if pdf_path:
            logger.info(f"Loaded contract PDF from disk: {pdf_path}")
            context.append(f"Full Contract Agreement Text:\n{extract_text(str(pdf_path))}")
    elif isinstance(match, Path):
        logger.info(f"Loaded contract PDF directly from uploads: {match}")
        context.append(f"Full Contract Agreement Text:\n{extract_text(str(match))}")

    rules_content = _get_company_rules(last_msg)
    if rules_content:
        context.append(f"Official Company Construction Contract Rules & Compliance Policies:\n{rules_content}")

    sys_prompt = (
        "You are ContractAI, an expert enterprise AI agent specialized in construction contracts, contractor invoices, and compliance auditing.\n\n"
        "=== STRICT DOMAIN GUARDRAILS ===\n"
        "1. DOMAIN SCOPE: Your expertise is strictly confined to construction agreements, contractor billing, procurement, compliance rules (R1 to R12), civil engineering contracts, and related commercial/legal topics.\n"
        "2. OUT-OF-DOMAIN REFUSAL: If a user asks a question completely unrelated to this domain (e.g. cooking recipes, sports, creative fiction, video games, general coding unrelated to contracts), POLITELY DECLINE with this exact boundary message:\n"
        "   'I am ContractAI, specialized in construction contracts, contractor invoices, and compliance audits. I cannot assist with topics outside this domain. Please feel free to ask about construction agreements, invoice validations, or company compliance rules.'\n\n"
        "=== OPERATIONAL GUIDELINES ===\n"
        "3. When answering about specific uploaded/stored documents or company rules (R1 to R12), rely on the official information in the Context.\n"
        "4. When a contract's full agreement text is provided in Context, provide a thorough, professional executive summary of the project scope, parties, value, timeline, and key clauses.\n"
        "5. Never refuse a question by claiming lack of documents if the contract text or concept is provided in Context or can be explained conceptually.\n\n"
        "Context:\n" + ("\n\n".join(context) if context else "No specific document attached.")
    )


    resp = chat_llm.invoke([SystemMessage(content=sys_prompt), HumanMessage(content=last_msg)])
    return {"action": "general", "output_message": resp.content}

# =====================================================================
# Workflow Graph
# =====================================================================
def build_contract_graph():
    wf = StateGraph(AgentState)
    for name, node in [("router_node", router_node), ("classifier_node", classifier_node), ("contract_auditor_node", contract_auditor_node), ("invoice_validator_node", invoice_validator_node), ("sql_agent_node", sql_agent_node), ("save_node", save_node), ("cancel_node", cancel_node), ("general_agent_node", general_agent_node)]:
        wf.add_node(name, node)

    wf.set_entry_point("router_node")
    wf.add_conditional_edges("router_node", route_decision, {"classifier_node": "classifier_node", "save_node": "save_node", "cancel_node": "cancel_node", "sql_agent_node": "sql_agent_node", "general_agent_node": "general_agent_node"})
    wf.add_conditional_edges("classifier_node", route_doc_type, {"contract_auditor_node": "contract_auditor_node", "invoice_validator_node": "invoice_validator_node", "general_agent_node": "general_agent_node"})

    for node in ["contract_auditor_node", "invoice_validator_node", "sql_agent_node", "save_node", "cancel_node", "general_agent_node"]:
        wf.add_edge(node, END)

    graph = wf.compile()
    image = graph.get_graph().draw_mermaid_png()
    with open("langgraph_workflow.png","wb") as f:
        f.write(image)

    return wf.compile(checkpointer=MemorySaver())


contract_graph = build_contract_graph()

