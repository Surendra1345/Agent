from datetime import date, timedelta
from decimal import Decimal
import re
from typing import Literal
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from agent.config.database import engine
from agent.model.model import Contract, Invoice
from agent.schemas.schema import (
    InvoiceCreate, InvoiceDetails, InvoiceQueryResult,
    InvoiceResponse, InvoiceValidationResult,
)

InvoiceFilter = Literal["all", "overdue", "upcoming", "pending", "paid", "flagged"]
STOP_WORDS = {"a", "an", "and", "dated", "for", "in", "of", "on", "the"}
GENERIC_WORDS = {"construction", "contract", "agreement", "services", "project"}


def _invoice_to_response(inv: Invoice) -> InvoiceResponse:
    return InvoiceResponse(
        invoice_id=inv.invoice_id, contract_id=inv.contract_id,
        invoice_amount=float(inv.invoice_amount or 0), invoice_tax=float(inv.invoice_tax or 0),
        due_date=inv.due_date, status=inv.status or "Pending",
        paid_date=inv.paid_date, created_at=inv.created_at,
    )


def _name_tokens(value: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", value.lower()) if len(w) > 2 and w not in STOP_WORDS}


def find_contract_for_invoice(
    contract_name: str,
    contract_ref_id: str | None = None,
    project_scope: str | None = None,
    invoice_amount: Decimal | float | None = None,
) -> Contract | None:
    """Find a saved contract using PO/Contract ID, company name, and project scope disambiguation."""
    clean = contract_name.strip()
    if not clean and not contract_ref_id:
        raise ValueError("contract_name or contract_ref_id is required")

    with Session(engine) as session:
        # Tier 1: Match by explicit Contract Reference / PO Number if provided
        if contract_ref_id and contract_ref_id.strip():
            clean_ref = contract_ref_id.strip()
            direct_match = session.scalars(
                select(Contract).where(
                    func.lower(Contract.contract_id) == clean_ref.lower()
                )
            ).first() or session.scalars(
                select(Contract).where(
                    Contract.contract_id.ilike(f"%{clean_ref}%")
                )
            ).first()
            if direct_match:
                return direct_match

        # Tier 2: Exact or partial match on full contract name
        if clean:
            exact = session.scalars(select(Contract).where(func.lower(Contract.contract_name) == clean.lower())).first()
            if exact:
                return exact

        # Tier 3: Token scoring with project scope & financial magnitude disambiguation
        invoice_tokens = _name_tokens(clean) if clean else set()
        scope_tokens = _name_tokens(project_scope) if project_scope else set()
        inv_amt = Decimal(str(invoice_amount)) if invoice_amount is not None else None

        best_contract, best_score, second_score = None, 0.0, 0.0

        for contract in session.scalars(select(Contract)).all():
            if not contract.contract_name:
                continue
            contract_tokens = _name_tokens(contract.contract_name)
            shared = invoice_tokens & contract_tokens
            if not shared and not (scope_tokens & contract_tokens):
                continue

            # Base company name overlap score
            score = 0.0
            if invoice_tokens and contract_tokens:
                score = (len(shared) / len(contract_tokens) * 0.4) + (len(shared) / len(invoice_tokens) * 0.4)
                if shared - GENERIC_WORDS:
                    score += 0.15

            # Scope disambiguation: does this contract match "Road", "Building", "Highway", etc.?
            if scope_tokens:
                scope_shared = scope_tokens & contract_tokens
                if scope_shared:
                    score += 0.35 * (len(scope_shared) / len(scope_tokens))

            # Financial scale proximity: is the contract value in the same ballpark as the invoice?
            if inv_amt and contract.contract_amount:
                c_amt = contract.contract_amount
                if c_amt > 0:
                    diff_ratio = abs(c_amt - inv_amt) / c_amt
                    if diff_ratio <= Decimal("0.10"):  # within 10%
                        score += 0.20
                    elif diff_ratio <= Decimal("0.35"):
                        score += 0.10

            if score > best_score:
                second_score, best_score, best_contract = best_score, score, contract
            elif score > second_score:
                second_score = score

        if best_contract and best_score >= 0.4:
            return best_contract

    return None


def find_contract_by_name(contract_name: str) -> Contract | None:
    """Backward-compatible lookup by name."""
    return find_contract_for_invoice(contract_name=contract_name)


def _validate_invoice_values(
    invoice_id: str, contract_id: str, contract_amount: Decimal, tax_rate: Decimal,
    invoice_amount: Decimal, invoice_tax: Decimal
) -> InvoiceValidationResult:
    expected_tax = (contract_amount * tax_rate / Decimal("100")).quantize(Decimal("0.01"))
    amount_valid, tax_valid = (invoice_amount == contract_amount), (invoice_tax == expected_tax)

    issues = []
    if not amount_valid:
        issues.append(f"Invoice amount {invoice_amount} does not match contract amount {contract_amount}.")
    if not tax_valid:
        issues.append(f"Invoice tax {invoice_tax} does not match expected tax {expected_tax}.")

    return InvoiceValidationResult(
        invoice_id=invoice_id, contract_id=contract_id,
        is_valid=amount_valid and tax_valid,
        amount_valid=amount_valid, tax_valid=tax_valid,
        contract_amount=float(contract_amount), invoice_amount=float(invoice_amount),
        expected_tax=float(expected_tax), invoice_tax=float(invoice_tax),
        status="Valid" if (amount_valid and tax_valid) else "Flagged", issues=issues,
    )


def validate_invoice_details(details: InvoiceDetails) -> tuple[InvoiceValidationResult, str]:
    """Validate extracted invoice details against its matching saved contract."""
    contract = find_contract_for_invoice(
        contract_name=details.contract_name,
        contract_ref_id=details.contract_ref_id,
        project_scope=details.project_scope,
        invoice_amount=Decimal(str(details.invoice_amount)),
    )
    if not contract:
        raise ValueError(f"No saved contract matched invoice contract name: {details.contract_name}")

    val = _validate_invoice_values(
        invoice_id=details.invoice_id, contract_id=contract.contract_id,
        contract_amount=Decimal(str(contract.contract_amount or 0)),
        tax_rate=Decimal(str(contract.tax_rate or 0)),
        invoice_amount=Decimal(str(details.invoice_amount)),
        invoice_tax=Decimal(str(details.invoice_tax)),
    )
    return val, contract.contract_id


def save_invoice_to_db(invoice_data: InvoiceCreate | dict) -> InvoiceResponse:
    """Save or upsert an invoice into PostgreSQL."""
    data = invoice_data.model_dump(mode="python") if isinstance(invoice_data, InvoiceCreate) else invoice_data
    contract_id = data.get("contract_id")
    if not contract_id:
        raise ValueError("contract_id is required")

    with Session(engine) as session:
        if not session.get(Contract, contract_id):
            raise ValueError(f"Contract not found: {contract_id}")

        inv = session.merge(Invoice(
            invoice_id=data["invoice_id"], contract_id=contract_id,
            invoice_amount=Decimal(str(data["invoice_amount"])),
            invoice_tax=Decimal(str(data["invoice_tax"])),
            due_date=data["due_date"], status=data.get("status") or "Pending",
            paid_date=data.get("paid_date"), created_at=date.today(),
        ))
        session.commit()
        return _invoice_to_response(inv)


def save_invoice_details_to_db(details: InvoiceDetails) -> InvoiceResponse:
    """Resolve invoice contract name to contract_id, then save to DB."""
    contract = find_contract_by_name(details.contract_name)
    if not contract:
        raise ValueError(f"No saved contract matched invoice contract name: {details.contract_name}")

    return save_invoice_to_db(InvoiceCreate(
        invoice_id=details.invoice_id, contract_id=contract.contract_id,
        invoice_amount=details.invoice_amount, invoice_tax=details.invoice_tax,
        due_date=details.due_date, status=details.status, paid_date=details.paid_date,
    ))


def get_invoice_by_id(invoice_id: str) -> InvoiceResponse | None:
    """Retrieve an invoice by its invoice_id."""
    with Session(engine) as session:
        inv = session.get(Invoice, invoice_id)
        return _invoice_to_response(inv) if inv else None


def query_invoices(filter_type: InvoiceFilter = "all", days: int | None = None) -> list[InvoiceQueryResult]:
    """Query invoices with status and overdue filters."""
    today, fk = date.today(), filter_type.lower()

    with Session(engine) as session:
        stmt = select(Invoice, Contract).join(Contract, Invoice.contract_id == Contract.contract_id)
        if fk == "overdue":
            stmt = stmt.where(Invoice.due_date < today, Invoice.status != "Paid")
        elif fk == "upcoming":
            stmt = stmt.where(Invoice.due_date >= today, Invoice.due_date <= today + timedelta(days=days or 7))
        elif fk in {"pending", "paid", "flagged"}:
            stmt = stmt.where(Invoice.status.ilike(fk))
        elif fk != "all":
            raise ValueError("filter_type must be one of: all, overdue, upcoming, pending, paid, flagged")

        rows = session.execute(stmt.order_by(Invoice.due_date)).all()

    return [
        InvoiceQueryResult(
            invoice_id=inv.invoice_id, contract_id=inv.contract_id, contract_name=c.contract_name,
            invoice_amount=float(inv.invoice_amount or 0), invoice_tax=float(inv.invoice_tax or 0),
            due_date=inv.due_date, status=inv.status or "Pending", paid_date=inv.paid_date,
            days_overdue=(today - inv.due_date).days if (inv.due_date and inv.due_date < today and inv.status != "Paid") else None,
        ) for inv, c in rows
    ]


def validate_invoice(invoice_id: str) -> InvoiceValidationResult:
    """Validate an existing database invoice against its contract."""
    with Session(engine) as session:
        row = session.execute(
            select(Invoice, Contract).join(Contract, Invoice.contract_id == Contract.contract_id)
            .where(Invoice.invoice_id == invoice_id)
        ).first()
        if not row:
            raise ValueError(f"Invoice not found: {invoice_id}")
        inv, contract = row

    return _validate_invoice_values(
        invoice_id=inv.invoice_id, contract_id=inv.contract_id,
        contract_amount=Decimal(str(contract.contract_amount or 0)),
        tax_rate=Decimal(str(contract.tax_rate or 0)),
        invoice_amount=Decimal(str(inv.invoice_amount or 0)),
        invoice_tax=Decimal(str(inv.invoice_tax or 0)),
    )
