import json
from agent.schemas.schema import ContractDetails
from agent.services.llm import MAX_TOKENS, MODEL, TEMPERATURE, client
from agent.utils.document_parser import extract_text

EXTRACTION_SYSTEM_PROMPT = """You are a contract data extraction assistant.
Extract structured information from the provided construction contract text:
- contract_name: Primary Company/Client/Owner name + Agreement/Project title (e.g. "Vantage Commercial Spaces - Construction Contract Agreement"). Never output only generic titles.
- contract_amount: Total numerical contract value exclusive of tax.
- tax_rate: Tax percentage (e.g. 18.0 for 18% GST).
- effective_date: Execution or start date (YYYY-MM-DD).
- completion_date: Completion or end date (YYYY-MM-DD).
- file_url: File URL if explicitly present, else null.

Output ONLY valid JSON matching the schema."""


def extract_contract_details(contract_text: str) -> ContractDetails:
    """Extract structured contract details from raw text using the LLM."""
    if not contract_text or not contract_text.strip():
        raise ValueError("Contract text cannot be empty")

    prompt = (
        f"{EXTRACTION_SYSTEM_PROMPT}\nJSON Schema:\n{json.dumps(ContractDetails.model_json_schema())}\n\n"
        f"CONTRACT TEXT:\n{contract_text}"
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

    return ContractDetails.model_validate(data)


def extract_contract_details_from_pdf(pdf_path: str) -> ContractDetails:
    """Extract text from a contract PDF and extract structured contract details."""
    text = extract_text(pdf_path)
    return extract_contract_details(text)