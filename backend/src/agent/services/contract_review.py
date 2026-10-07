import json
from agent.schemas.schema import ContractDetails, ReviewResponse
from agent.services.llm import MAX_TOKENS, MODEL, TEMPERATURE, client
from agent.tools.search_tool import SEARCH_TOOL_SPEC, search_rulebook_tool

REVIEW_SYSTEM_PROMPT = f"""You are an expert construction contract compliance review assistant.
Your task is to review the provided construction contract agreement against company contract rules.
Carefully examine the contract clauses (Scope, Payment Terms, Mobilization Advance, Liability, Termination, Delays, Warranty, Scope Variations, Cost Escalation, Jurisdiction, Confidentiality).
Use the `search_rulebook_tool` to retrieve relevant company rules. Do not invent rules.
Compare the contract clauses against the retrieved rules and flag genuine non-compliant terms.
Note: If a clause or term is present in the contract text (such as mobilization advance or termination notice), do NOT flag it as missing. Only flag clauses that violate company rules.
Once you have evaluated the clauses, output ONLY the JSON object matching the ReviewResponse schema:
{json.dumps(ReviewResponse.model_json_schema())}
"""


def _parse_json_response(content: str) -> dict:
    """Extract and parse JSON object from LLM response content."""
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end > start:
            return json.loads(content[start:end + 1])
        raise ValueError("LLM returned invalid JSON")


def review_contract_with_search(contract: ContractDetails, contract_text: str | None = None, max_steps: int = 4) -> ReviewResponse:
    """Agentic RAG contract review: LLM autonomously searches the rulebook and returns flags."""
    user_content = f"Contract Metadata:\n{contract.model_dump_json(indent=2)}"
    if contract_text and contract_text.strip():
        user_content += f"\n\nFull Contract Agreement Text & Clauses:\n{contract_text.strip()}"

    messages = [
        {"role": "system", "content": REVIEW_SYSTEM_PROMPT},
        {"role": "user", "content": f"Review this contract against company rules:\n{user_content}"},
    ]
    tools = [SEARCH_TOOL_SPEC]

    for step in range(max_steps):
        allow_tools = step < 2
        response = client.chat.completions.create(
            model=MODEL,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            messages=messages,
            tools=tools if allow_tools else None,
            tool_choice="auto" if allow_tools else None,
        )
        msg = response.choices[0].message
        messages.append(msg)

        # Handle tool calls
        if msg.tool_calls:
            for tc in msg.tool_calls:
                args = json.loads(tc.function.arguments)
                tool_output = search_rulebook_tool(
                    query=args.get("query", ""),
                    top_k=args.get("top_k", 3),
                )
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": tc.function.name,
                    "content": json.dumps(tool_output),
                })
        else:
            if not msg.content:
                raise ValueError("LLM returned empty review content")
            data = _parse_json_response(msg.content)
            return ReviewResponse.model_validate(data)

    raise TimeoutError(f"LLM exceeded maximum review steps ({max_steps})")


# Backward compatibility aliases
review_contract = review_contract_with_search
review_contract_with_agentic_tools = review_contract_with_search