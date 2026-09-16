import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agent.services.llm import client, MODEL, MAX_TOKENS, TEMPERATURE
from agent.tools.search_tool import search_rulebook_tool, SEARCH_TOOL_SPEC
from agent.schemas.schema import ContractDetails, ReviewResponse
from agent.services.contract_extract import extract_contract_details


def review_contract(
    contract: ContractDetails,
    rules: list[dict],
) -> ReviewResponse:
    """
    Review an extracted contract against relevant contract rules.
    """

    if not rules:
        raise ValueError("No contract rules provided")

    system_prompt = """
You are a construction contract review assistant.

Your task is to compare the provided contract details and
retrieved contract rules.

Identify only issues where the contract differs from or violates
a retrieved rule.

For every issue:
- identify the rule_id
- assign a severity
- describe the issue
- provide the contract value when available
- provide the required value when available
- explain why the issue was flagged

Rules:
- Use only the provided contract and rules.
- Do not invent rules.
- Do not invent contract values.
- Do not flag something merely because it is not mentioned.
- If there are no issues, return an empty flags list.
- Return the result according to the provided JSON schema.
"""

    user_prompt = {
        "contract": contract.model_dump(mode="json"),
        "rules": rules,
    }

    response = client.chat.completions.create(
        model=MODEL,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
        messages=[
            {
                "role": "system",
                "content": system_prompt + f"\nJSON Schema:\n{json.dumps(ReviewResponse.model_json_schema())}",
            },
            {
                "role": "user",
                "content": json.dumps(user_prompt),
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

    return ReviewResponse.model_validate(data)


def review_contract_with_search(
    contract: ContractDetails,
    contract_text: str = "",
    top_k: int = 3,
) -> ReviewResponse:
    """
    Retrieve relevant rulebook chunks using targeted queries based on contract details,
    then review the contract against retrieved rules.
    """
    # Create targeted query strings for vector retrieval instead of embedding raw full text
    queries = [
        "contract amount tax rate payment terms milestone",
        "warranty period defect liability duration",
        "liquidated damages delay penalty completion date",
        "termination notice period governing law jurisdiction",
    ]

    seen_ids = set()
    aggregated_rules = []

    for q in queries:
        fetched = search_rulebook_tool(q, top_k=top_k)
        for rule in fetched:
            rule_key = (rule.get("rule_id"), rule.get("content")[:50])
            if rule_key not in seen_ids:
                seen_ids.add(rule_key)
                aggregated_rules.append(rule)

    if not aggregated_rules:
        # Fallback to general search if no targeted rules matched
        aggregated_rules = search_rulebook_tool("contract terms rules", top_k=5)

    return review_contract(contract, aggregated_rules)


if __name__ == "__main__":
    contract = ContractDetails(
        contract_name="Construction Services Agreement",
        contract_amount=8500000,
        tax_rate=18,
        effective_date="2026-03-01",
        completion_date="2026-12-15",
        file_url=None,
    )

    rules = [
        {
            "rule_id": "R1",
            "section": "Warranty",
            "content": "Warranty period must be 12 months.",
            "source": "rulebook.pdf",
            "page": 5,
            "distance": 0.12,
        }
    ]

    result = review_contract(contract, rules)

    print(result.model_dump_json(indent=2))