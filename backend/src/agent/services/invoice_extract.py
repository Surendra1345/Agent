import json
from agent.schemas.schema import InvoiceDetails
from agent.services.llm import MAX_TOKENS, MODEL, TEMPERATURE, client
from agent.utils.document_parser import extract_text

INVOICE_SYSTEM_PROMPT = """You are an invoice data extraction assistant.
Extract structured information from the provided invoice text:
- invoice_id: The invoice number (e.g. "BRC/2026/INV-005").
- contract_name: Company/Client name + agreement/project reference from "Bill To" or "Reference".
- contract_ref_id: Any explicit Contract Reference, PO Number, or Work Order ID mentioned (e.g. "C001", "PO-2026-004", "WO-42"), or null if none.
- project_scope: Specific project title, construction domain, or site description if mentioned (e.g. "Road Construction", "Commercial Complex", "Tower Phase 2"), or null if none.
- invoice_amount: Pre-tax invoice amount.
- invoice_tax: Tax amount.
- due_date: Payment due date (YYYY-MM-DD).
- status: Always "Pending". Invoices must always start as Pending regardless of document text.
- paid_date: Always null. Payment status must be updated manually.

Output ONLY valid JSON matching the schema."""


def extract_invoice_details(invoice_text: str) -> InvoiceDetails:
    """Extract structured invoice details from raw invoice text."""
    if not invoice_text or not invoice_text.strip():
        raise ValueError("Invoice text cannot be empty")

    prompt = (
        f"{INVOICE_SYSTEM_PROMPT}\nJSON Schema:\n{json.dumps(InvoiceDetails.model_json_schema())}\n\n"
        f"INVOICE TEXT:\n{invoice_text}"
    )

    response = client.chat.completions.create(
        model=MODEL,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    if not content:
        raise ValueError("LLM returned an empty response")

    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError("LLM returned invalid JSON") from exc

    # Enforce business rule: new invoices always start as Pending
    data["status"] = "Pending"
    data["paid_date"] = None

    return InvoiceDetails.model_validate(data)


def extract_invoice_details_from_pdf(pdf_path: str) -> InvoiceDetails:
    """Extract text from an invoice PDF and extract structured invoice details."""
    text = extract_text(pdf_path)
    return extract_invoice_details(text)