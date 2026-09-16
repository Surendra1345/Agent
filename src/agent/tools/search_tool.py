from agent.retriving.retrive import search_rulebook 


def search_rulebook_tool(query: str, top_k: int = 1) -> list[dict]:
    """
    Search the contract rulebook for rules relevant to the given query.

    This function is the tool that will be exposed to the LLM.
    """

    if not query or not query.strip():
        raise ValueError("Query cannot be empty")

    if top_k <= 0:
        raise ValueError("top_k must be a positive integer")

    return search_rulebook(query=query, top_k=top_k)


SEARCH_TOOL_SPEC = {
    "type": "function",
    "function": {
        "name": "search_rulebook_tool",
        "description": "Search the stored contract rules database for rules matching a query (e.g., warranty, tax rate, payment milestones, damages).",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Specific search query (e.g., 'warranty period duration', 'tax rate policy').",
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of top matching rules to return.",
                    "default": 3,
                },
            },
            "required": ["query"],
        },
    },
}