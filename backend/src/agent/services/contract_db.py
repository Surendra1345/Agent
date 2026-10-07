import uuid
from datetime import date
from decimal import Decimal
from sqlalchemy import select,insert
from sqlalchemy.orm import Session, selectinload

from agent.config.database import engine
from agent.model.model import Contract, Flag
from agent.schemas.schema import ContractCreate, ContractDetails, ContractResponse


def _generate_contract_id(name: str) -> str:
    """Generate a clean contract_id like C001 or based on hash."""
    clean_name = "".join(c for c in name if c.isalnum()).upper()[:4]
    short_hash = uuid.uuid4().hex[:4].upper()
    return f"C_{clean_name}_{short_hash}"


def save_contract_to_db(
    contract_data: ContractDetails | ContractCreate | dict,
    contract_id: str | None = None,
    document_hash: str | None = None,
    flags: list[dict] | None = None,
) -> ContractResponse:
    """
    Save or update contract details in PostgreSQL contracts table, including document_hash and flags.
    """
    if isinstance(contract_data, dict):
        data = contract_data
    elif isinstance(contract_data, (ContractDetails, ContractCreate)):
        data = contract_data.model_dump(mode="python")
    else:
        raise ValueError("Invalid contract data type")

    cid = contract_id or data.get("contract_id")
    cname = data.get("contract_name", "UNKNOWN")
    if not cid:
        with Session(engine) as session:
            existing = session.scalars(
                select(Contract).where(Contract.contract_name == cname)
            ).first()
            if existing:
                cid = existing.contract_id
            else:
                cid = _generate_contract_id(cname)

    contract_obj = Contract(
        contract_id=cid,
        document_hash=document_hash or data.get("document_hash"),
        contract_name=data.get("contract_name"),
        contract_amount=Decimal(str(data["contract_amount"])) if data.get("contract_amount") is not None else None,
        tax_rate=Decimal(str(data["tax_rate"])) if data.get("tax_rate") is not None else None,
        start_date=data.get("effective_date") or data.get("start_date"),
        end_date=data.get("completion_date") or data.get("end_date"),
        file_url=data.get("file_url"),
    )

    with Session(engine) as session:
        saved_contract = session.merge(contract_obj)
        if flags:
            for f_item in flags:
                desc = f_item.get("description") or f_item.get("issue") or str(f_item)
                flag_obj = Flag(
                    contract_id=cid,
                    description=desc,
                )
                session.add(flag_obj)
        session.commit()

        return ContractResponse(
            contract_id=saved_contract.contract_id,
            contract_name=saved_contract.contract_name or "",
            contract_amount=float(saved_contract.contract_amount) if saved_contract.contract_amount else 0.0,
            tax_rate=float(saved_contract.tax_rate) if saved_contract.tax_rate else 0.0,
            start_date=saved_contract.start_date,
            end_date=saved_contract.end_date,
            file_url=saved_contract.file_url,
            created_at=saved_contract.created_at,
        )


def get_contract_by_id(contract_id: str) -> ContractResponse | None:
    """
    Retrieve contract details from PostgreSQL contracts table by contract_id.
    """
    with Session(engine) as session:
        contract = session.scalars(
            select(Contract).where(Contract.contract_id == contract_id)
        ).first()

        if not contract:
            return None

        return ContractResponse(
            contract_id=contract.contract_id,
            contract_name=contract.contract_name or "",
            contract_amount=float(contract.contract_amount) if contract.contract_amount else 0.0,
            tax_rate=float(contract.tax_rate) if contract.tax_rate else 0.0,
            start_date=contract.start_date,
            end_date=contract.end_date,
            file_url=contract.file_url,
            created_at=contract.created_at,
        )

def find_contract_by_name(contract_name: str) -> ContractResponse | None:
    """Retrieve contract details from PostgreSQL contracts table by exact or case-insensitive contract_name."""
    clean = contract_name.strip()
    if not clean:
        return None
    with Session(engine) as session:
        contract = session.scalars(
            select(Contract).where(Contract.contract_name.ilike(f"%{clean}%"))
        ).first()

        if not contract:
            return None

        return ContractResponse(
            contract_id=contract.contract_id,
            contract_name=contract.contract_name or "",
            contract_amount=float(contract.contract_amount) if contract.contract_amount else 0.0,
            tax_rate=float(contract.tax_rate) if contract.tax_rate else 0.0,
            start_date=contract.start_date,
            end_date=contract.end_date,
            file_url=contract.file_url,
            created_at=contract.created_at,
        )



def find_contract_by_hash(doc_hash: str) -> dict | None:
    """Finds contract by document_hash and returns contract data + saved flags."""
    with Session(engine) as session:
        contract = session.scalars(
            select(Contract).options(selectinload(Contract.flags)).where(Contract.document_hash == doc_hash)
        ).first()
        if not contract:
            return None
        
        flags_data = [
            {"flag_id": f.flag_id, "description": f.description}
            for f in contract.flags
        ]
        return {
            "contract": {
                "contract_id": contract.contract_id,
                "contract_name": contract.contract_name or "",
                "contract_amount": float(contract.contract_amount or 0.0),
                "tax_rate": float(contract.tax_rate or 0.0),
                "start_date": str(contract.start_date) if contract.start_date else None,
                "end_date": str(contract.end_date) if contract.end_date else None,
                "file_url": contract.file_url,
            },
            "flags": flags_data,
            "contract_id": contract.contract_id,
        }

    

def list_contracts_from_db(
    expiring_in_days: int | None = None,
    min_amount: float | None = None,
    max_amount: float | None = None,
) -> list[ContractResponse]:
    """
    List contracts stored in PostgreSQL contracts table with optional filtering.
    """
    from datetime import date, timedelta

    with Session(engine) as session:
        stmt = select(Contract)
        if expiring_in_days is not None:
            today = date.today()
            target_date = today + timedelta(days=expiring_in_days)
            stmt = stmt.where(Contract.end_date >= today, Contract.end_date <= target_date)

        if min_amount is not None:
            stmt = stmt.where(Contract.contract_amount >= Decimal(str(min_amount)))

        if max_amount is not None:
            stmt = stmt.where(Contract.contract_amount <= Decimal(str(max_amount)))

        contracts = session.scalars(stmt).all()
        return [
            ContractResponse(
                contract_id=c.contract_id,
                contract_name=c.contract_name or "",
                contract_amount=float(c.contract_amount) if c.contract_amount else 0.0,
                tax_rate=float(c.tax_rate) if c.tax_rate else 0.0,
                start_date=c.start_date,
                end_date=c.end_date,
                file_url=c.file_url,
                created_at=c.created_at,
            )
            for c in contracts
        ]
