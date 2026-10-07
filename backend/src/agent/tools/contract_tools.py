from agent.services.contract_db import save_contract_to_db


def save_contract_tool(
    contract_name: str,
    contract_amount: float,
    tax_rate: float,
    effective_date: str | None = None,
    completion_date: str | None = None,
    file_url: str | None = None,
    contract_id: str | None = None,
    document_hash: str | None = None,
    flags: list[dict] | None = None,
) -> dict:
    """
    Save contract details into PostgreSQL contracts table.
    """
    res = save_contract_to_db(
        contract_data={
            "contract_name": contract_name,
            "contract_amount": contract_amount,
            "tax_rate": tax_rate,
            "effective_date": effective_date,
            "completion_date": completion_date,
            "file_url": file_url,
            "document_hash": document_hash,
        },
        contract_id=contract_id,
        document_hash=document_hash,
        flags=flags,
    )
    return res.model_dump(mode="json")


# OpenAI Tool Schema for LLM Tool Calling
SAVE_CONTRACT_TOOL_SPEC = {
    "type": "function",
    "function": {
        "name": "save_contract_tool",
        "description": "Save or persist extracted contract details into PostgreSQL contracts table.",
        "parameters": {
            "type": "object",
            "properties": {
                "contract_name": {"type": "string", "description": "Name of the contract"},
                "contract_amount": {"type": "number", "description": "Total agreed contract amount"},
                "tax_rate": {"type": "number", "description": "Applicable tax rate percentage (e.g. 18.0)"},
                "effective_date": {"type": "string", "description": "Contract start/effective date (YYYY-MM-DD)"},
                "completion_date": {"type": "string", "description": "Contract completion date (YYYY-MM-DD)"},
                "file_url": {"type": "string", "description": "File path or URL of contract document"},
                "contract_id": {"type": "string", "description": "Optional unique Contract ID (e.g. C001)"},
            },
            "required": ["contract_name", "contract_amount", "tax_rate"],
        },
    },
}

