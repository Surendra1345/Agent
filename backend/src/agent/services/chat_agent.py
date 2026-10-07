import logging

from langchain_core.messages import HumanMessage
from agent.services.graph_agent import contract_graph

logger = logging.getLogger("chat_agent")


def process_chat(
    message: str,
    file_path: str | None = None,
    file_url: str | None = None,
    session_id: str | None = None,
) -> dict:
    """Unified chat handler orchestrated entirely by LangGraph StateGraph.

    Maintains multi-turn conversation memory, handles autonomous document triage,
    contract auditing, invoice validation, self-correcting SQL analytics, and
    Human-in-the-Loop approval workflows.
    """
    thread_id = session_id or "default_session"
    config = {"configurable": {"thread_id": thread_id}}

    logger.info(f"Invoking contract_graph | thread_id='{thread_id}' | file_path='{file_path}' | message='{message[:80]}'")

    inputs = {
        "messages": [HumanMessage(content=message)] if message else [],
        "session_id": thread_id,
        "file_path": file_path,
    }
    if file_url:
        inputs["file_url"] = file_url

    final_state = contract_graph.invoke(inputs, config=config)

    action = final_state.get("action")
    logger.info(f"Graph execution complete | thread_id='{thread_id}' | action='{action}' | pending_action='{final_state.get('pending_action')}'")
    include_contract = action in ["review_contract", "save_contract"]
    include_invoice = action in ["validate_invoice", "save_invoice"]

    # Format into frontend-ready JSON response payload
    return {
        "message": final_state.get("output_message") or message,
        "action": action,
        "document_type": final_state.get("document_type"),
        "contract": final_state.get("contract") if include_contract else None,
        "contract_id": final_state.get("contract_id"),
        "review": final_state.get("review") if action == "review_contract" else None,
        "invoice": final_state.get("invoice") if include_invoice else None,
        "validation": final_state.get("validation") if action == "validate_invoice" else None,
        "generated_sql": final_state.get("sql_query"),
        "results": final_state.get("sql_results"),
        "pending_action": final_state.get("pending_action"),
        "already_saved": final_state.get("already_saved", False),
        "save_result": final_state.get("save_result"),
    }