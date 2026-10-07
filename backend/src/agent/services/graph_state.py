from typing import Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """Unified state for the Construction Contract & Invoice LangGraph ecosystem."""

    # Multi-turn conversation messages with append reducer
    messages: Annotated[list, add_messages]

    # Session tracking
    session_id: str

    # Document details
    file_path: str | None
    file_url: str | None
    document_type: Literal["contract", "invoice"] | None

    # Domain entities
    contract: dict | None
    contract_id: str | None
    invoice: dict | None

    # Reviews and validations
    review: dict | None
    validation: dict | None

    # Natural Language Text-to-SQL
    sql_query: str | None
    sql_results: list[dict] | None
    sql_error: str | None
    sql_retry_count: int

    # Human-in-the-Loop & persistence state
    pending_action: Literal["confirm_save_contract", "confirm_save_invoice"] | None
    action_approved: bool
    already_saved: bool
    save_result: dict | None

    # Output formatting for frontend compatibility
    action: str | None
    output_message: str | None
