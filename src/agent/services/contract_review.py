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


def review_contract_with_agentic_tools(
    contract: ContractDetails,
    max_steps: int = 5,
) -> ReviewResponse:
    """
    Autonomous LLM Agentic Review:
    The LLM receives contract details and decides dynamically when to call search_rulebook_tool.
    Python executes tool calls against pgvector and feeds results back to the LLM.
    """
    system_prompt = f"""
You are a construction contract review assistant.

Your task is to review the provided contract details against company policy rules stored in our pgvector database.

You have access to `search_rulebook_tool`.

Instructions:
1. Look at the contract details provided.
2. If you need policy rules to evaluate compliance (e.g., warranty limits, payment terms, delay penalties, tax rules, liability caps), call `search_rulebook_tool` with a targeted query.
3. You may call `search_rulebook_tool` multiple times with different search queries if needed.
4. Once you have retrieved all necessary rules and evaluated compliance, output your final answer as a JSON object matching this schema:
{json.dumps(ReviewResponse.model_json_schema())}

Rules for final output:
- Identify only issues where the contract differs from or violates a retrieved rule.
- Do not invent rules or contract values.
- Output valid JSON matching the schema with status, summary, and flags.
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": f"Please review this contract:\n{json.dumps(contract.model_dump(mode='json'))}",
        },
    ]

    tools = [SEARCH_TOOL_SPEC]

    for step in range(max_steps):
        response = client.chat.completions.create(
            model=MODEL,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )

        response_message = response.choices[0].message
        messages.append(response_message)

        if response_message.tool_calls:
            print(f"\n[LLM Agent] Step {step + 1}: LLM decided to call {len(response_message.tool_calls)} tool(s)...")
            for tool_call in response_message.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)

                print(f"   -> LLM calling '{func_name}' with query: '{func_args.get('query')}'")

                if func_name == "search_rulebook_tool":
                    tool_output = search_rulebook_tool(
                        query=func_args.get("query"),
                        top_k=func_args.get("top_k", 3),
                    )
                else:
                    tool_output = {"error": f"Unknown tool {func_name}"}

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": func_name,
                    "content": json.dumps(tool_output),
                })
        else:
            content = response_message.content
            if not content:
                raise ValueError("LLM returned empty final content")

            first_brace = content.find("{")
            last_brace = content.rfind("}")
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                json_str = content[first_brace : last_brace + 1]
            else:
                json_str = content

            data = json.loads(json_str)
            return ReviewResponse.model_validate(data)

    raise TimeoutError("LLM exceeded max agentic tool loop steps")


def review_contract_with_search(
    contract: ContractDetails,
) -> ReviewResponse:
    """Retrieve relevant rulebook chunks using dynamic LLM tool calling."""
    return review_contract_with_agentic_tools(contract)


if __name__ == "__main__":
    from agent.services.contract_extract import extract_contract_details_from_pdf

    pdf_path = r"C:\Users\User\Downloads\construction_agreement_skyline.pdf"
    if Path(pdf_path).is_file():
        print(f"Extracting details from {pdf_path}...")
        contract = extract_contract_details_from_pdf(pdf_path)
        print("\nReviewing contract using autonomous LLM search tool...")
        result = review_contract_with_search(contract)
        print("\nReview Result:\n", result.model_dump_json(indent=2))