import json

from agent.schemas.schema import DocumentClassification
from agent.services.llm import MAX_TOKENS, MODEL, TEMPERATURE, client


CLASSIFICATION_PROMPT = """
You classify uploaded business documents for a construction management system.

Classify the document as exactly one of:
- contract: an agreement between parties defining scope, terms, dates, or contract value
- invoice: a bill or payment request containing an invoice number, amount, tax, due date, or payment status

Use only evidence in the document text. Return JSON matching the provided schema.
"""


def classify_document(document_text: str) -> DocumentClassification:
    """Classify document text and validate the result with Pydantic."""
    if not document_text or not document_text.strip():
        raise ValueError("Document text cannot be empty")

    response = client.chat.completions.create(
        model=MODEL,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
        messages=[
            {
                "role": "system",
                "content": CLASSIFICATION_PROMPT
                + f"\nJSON Schema:\n{json.dumps(DocumentClassification.model_json_schema())}",
            },
            {"role": "user", "content": document_text},
        ],
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    if not content:
        raise ValueError("LLM returned an empty document classification")

    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError("LLM returned invalid document classification JSON") from exc

    return DocumentClassification.model_validate(data)
