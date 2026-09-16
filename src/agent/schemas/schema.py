from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class ContractDetails(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract_name: str
    contract_amount: float | None = Field(default=None, gt=0)
    tax_rate: float | None = Field(default=None, ge=0, le=100)
    effective_date: date | None = None
    completion_date: date | None = None
    file_url: str | None = None


class Flag(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule_id: str
    severity: str
    issue: str
    contract_value: str | None = None
    required_value: str | None = None
    explanation: str


class ReviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    summary: str
    flags: list[Flag]