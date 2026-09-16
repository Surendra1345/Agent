import json

from agent.services.llm import client, MODEL, MAX_TOKENS, TEMPERATURE
from agent.schemas.schema import ContractDetails
from agent.utils.document_parser import extract_contract_text

def extract_contract_details(contract_text: str) -> ContractDetails:
    """
    Extract structured contract details from raw contract text.
    """

    if not contract_text or not contract_text.strip():
        raise ValueError("Contract text cannot be empty")

    system_prompt = """
You are a contract data extraction assistant.

Extract only the following information from the provided contract:
- contract name
- contract amount
- tax rate
- effective date
- completion date
- file URL, if explicitly present

Rules:
- Use only information present in the contract text.
- Do not invent or assume values.
- Return the result according to the provided JSON schema.
"""

    response = client.chat.completions.create(
        model=MODEL,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
        messages=[
            {
                "role": "system",
                "content": system_prompt + f"\nJSON Schema:\n{json.dumps(ContractDetails.model_json_schema())}",
            },
            {
                "role": "user",
                "content": contract_text,
            },
        ],
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
    """Extract text from PDF and extract contract details."""
    text = extract_contract_text(pdf_path)
    return extract_contract_details(text)