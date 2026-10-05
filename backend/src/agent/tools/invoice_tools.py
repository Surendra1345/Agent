from agent.services.invoice_db import (
    query_invoices,
    save_invoice_to_db,
    validate_invoice,
)


def save_invoice_tool(
    invoice_id: str,
    contract_id: str,
    invoice_amount: float,
    invoice_tax: float,
    due_date: str,
    status: str = "Pending",
    paid_date: str | None = None,
) -> dict:
    """
    Save or update an invoice linked to a contract.
    """

    invoice = save_invoice_to_db(
        {
            "invoice_id": invoice_id,
            "contract_id": contract_id,
            "invoice_amount": invoice_amount,
            "invoice_tax": invoice_tax,
            "due_date": due_date,
            "status": status,
            "paid_date": paid_date,
        }
    )

    return invoice.model_dump(mode="json")


def query_invoices_tool(
    filter_type: str = "all",
    days: int | None = None,
) -> list[dict]:
    """
    Query invoices by status or due-date window.
    """

    allowed_filters = {
        "all",
        "overdue",
        "upcoming",
        "pending",
        "paid",
        "flagged",
    }

    if filter_type not in allowed_filters:
        raise ValueError(
            f"Invalid filter_type: {filter_type}. "
            f"Allowed values: {sorted(allowed_filters)}"
        )

    if days is not None and days <= 0:
        raise ValueError("days must be a positive integer")

    invoices = query_invoices(
        filter_type=filter_type,
        days=days,
    )

    return [
        invoice.model_dump(mode="json")
        for invoice in invoices
    ]


def validate_invoice_tool(
    invoice_id: str,
) -> dict:
    """
    Validate invoice amount and tax against the linked contract.
    """

    if not invoice_id or not invoice_id.strip():
        raise ValueError("invoice_id cannot be empty")

    result = validate_invoice(invoice_id)

    return result.model_dump(mode="json")


# ============================================================
# SAVE INVOICE TOOL
# ============================================================

SAVE_INVOICE_TOOL_SPEC = {
    "type": "function",
    "function": {
        "name": "save_invoice_tool",
        "description": (
            "Save or update an invoice linked to a contract."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "invoice_id": {
                    "type": "string",
                    "description": (
                        "Unique invoice ID, "
                        "for example INV001."
                    ),
                },
                "contract_id": {
                    "type": "string",
                    "description": (
                        "Contract ID associated with "
                        "the invoice, for example C001."
                    ),
                },
                "invoice_amount": {
                    "type": "number",
                    "description": (
                        "Amount stated on the invoice."
                    ),
                },
                "invoice_tax": {
                    "type": "number",
                    "description": (
                        "Tax amount stated on the invoice."
                    ),
                },
                "due_date": {
                    "type": "string",
                    "description": (
                        "Invoice due date in YYYY-MM-DD format."
                    ),
                },
                "status": {
                    "type": "string",
                    "enum": [
                        "Pending",
                        "Paid",
                        "Overdue",
                        "Flagged",
                    ],
                    "default": "Pending",
                    "description": "Current invoice status.",
                },
                "paid_date": {
                    "type": [
                        "string",
                        "null",
                    ],
                    "description": (
                        "Payment date in YYYY-MM-DD format. "
                        "Use null if the invoice has not been paid."
                    ),
                },
            },
            "required": [
                "invoice_id",
                "contract_id",
                "invoice_amount",
                "invoice_tax",
                "due_date",
            ],
            "additionalProperties": False,
        },
    },
}


# ============================================================
# QUERY INVOICES TOOL
# ============================================================

QUERY_INVOICES_TOOL_SPEC = {
    "type": "function",
    "function": {
        "name": "query_invoices_tool",
        "description": (
            "Find invoices by status or due-date window. "
            "Can return all, overdue, upcoming, pending, "
            "paid, or flagged invoices."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "filter_type": {
                    "type": "string",
                    "enum": [
                        "all",
                        "overdue",
                        "upcoming",
                        "pending",
                        "paid",
                        "flagged",
                    ],
                    "default": "all",
                    "description": (
                        "Type of invoice query."
                    ),
                },
                "days": {
                    "type": "integer",
                    "minimum": 1,
                    "description": (
                        "Number of days for an upcoming "
                        "invoice search, for example 7."
                    ),
                },
            },
            "additionalProperties": False,
        },
    },
}

# ============================================================
# VALIDATE INVOICE TOOL
# ============================================================

VALIDATE_INVOICE_TOOL_SPEC = {
    "type": "function",
    "function": {
        "name": "validate_invoice_tool",
        "description": (
            "Validate an invoice's amount and tax "
            "against its linked contract."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "invoice_id": {
                    "type": "string",
                    "description": (
                        "Invoice ID to validate, "
                        "for example INV001."
                    ),
                },
            },
            "required": [
                "invoice_id",
            ],
            "additionalProperties": False,
        },
    },
}