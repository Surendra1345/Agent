from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DocumentClassification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_type: Literal["contract", "invoice"]
    confidence: float = Field(ge=0, le=1)


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


# --------------------------------
# Contract & Invoice Schemas
# --------------------------------

class ContractCreate(BaseModel):
    contract_id: str = Field(description="Unique Contract ID (e.g. C001)")
    contract_name: str
    contract_amount: float = Field(gt=0, description="Agreed payment amount")
    tax_rate: float = Field(ge=0, le=100, description="Tax rate percentage (e.g. 18.0)")
    start_date: date | None = None
    end_date: date | None = None
    file_url: str | None = None


class ContractResponse(ContractCreate):
    model_config = ConfigDict(from_attributes=True)
    created_at: date | None = None


class InvoiceCreate(BaseModel):
    invoice_id: str = Field(description="Unique Invoice ID (e.g. INV001)")
    contract_id: str = Field(description="Parent Contract ID (1:1 link)")
    invoice_amount: float = Field(gt=0, description="Actual invoice amount")
    invoice_tax: float = Field(ge=0, description="Actual invoice tax amount")
    due_date: date
    status: str = Field(default="Pending", description="Pending, Paid, Overdue, or Flagged")
    paid_date: date | None = None


class InvoiceDetails(BaseModel):
    model_config = ConfigDict(extra="ignore")

    invoice_id: str = Field(description="Unique Invoice ID (e.g. INV001)")
    contract_name: str = Field(description="Contract/project name mentioned in the invoice")
    contract_ref_id: str | None = Field(default=None, description="PO Number, Work Order, or Contract ID reference (e.g. C001, PO-2026-004)")
    project_scope: str | None = Field(default=None, description="Project scope, site description, or construction domain (e.g. 'Road Construction', 'Commercial Building')")
    invoice_amount: float = Field(gt=0, description="Actual invoice amount")
    invoice_tax: float = Field(ge=0, description="Actual invoice tax amount")
    due_date: date
    status: str = Field(default="Pending", description="Pending, Paid, Overdue, or Flagged")
    paid_date: date | None = None


class InvoiceResponse(InvoiceCreate):
    model_config = ConfigDict(from_attributes=True)
    created_at: date | None = None


class InvoiceValidationResult(BaseModel):
    invoice_id: str
    contract_id: str
    is_valid: bool
    amount_valid: bool
    tax_valid: bool
    contract_amount: float
    invoice_amount: float
    expected_tax: float
    invoice_tax: float
    status: str
    issues: list[str]


class InvoiceQueryResult(BaseModel):
    invoice_id: str
    contract_id: str
    contract_name: str | None = None
    invoice_amount: float
    invoice_tax: float
    due_date: date
    status: str
    paid_date: date | None = None
    days_overdue: int | None = None

class FlagResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    flag_id: int
    contract_id: str
    description: str
    created_at: date
    updated_at: date

class FlagCreate(BaseModel):
    contract_id: str
    description: str