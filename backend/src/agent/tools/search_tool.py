from agent.retrivel.retrive import search_rulebook


def search_rulebook_tool(
    query: str,
    top_k: int = 3,
) -> list[dict]:
    """
    LLM-facing tool for searching relevant rulebook sections.
    """

    if not query or not query.strip():
        raise ValueError("Query cannot be empty")

    if top_k <= 0:
        raise ValueError("top_k must be a positive integer")

    # Call the actual RAG retrieval function
    return search_rulebook(
        query=query,
        top_k=top_k,
    )


SEARCH_TOOL_SPEC = {
    "type": "function",
    "function": {
        "name": "search_rulebook_tool",
        "description": (
            "Search the stored company rulebook for relevant policies "
            "such as warranty periods, payment terms, tax rules, "
            "termination notices, penalties, and liability limits."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "A specific question or topic to search for, "
                        "such as 'workmanship warranty period'."
                    ),
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of matching rulebook sections to return.",
                    "default": 3,
                    "minimum": 1,
                },
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
}