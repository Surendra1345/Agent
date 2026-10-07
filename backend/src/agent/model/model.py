from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Integer, Numeric, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector


class Base(DeclarativeBase):
    pass


class ContractRule(Base):
    __tablename__ = "contract_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    contract_rules: Mapped[str | None] = mapped_column(Text)

    content: Mapped[str] = mapped_column(Text, nullable=False)

    embedding: Mapped[list[float] | None] = mapped_column(Vector(384))

    source: Mapped[str | None] = mapped_column(Text)

    page: Mapped[int | None] = mapped_column(Integer)

    section: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[date | None] = mapped_column(
        Date,
        default=date.today
    )


class Contract(Base):
    __tablename__ = "contracts"

    contract_id: Mapped[str] = mapped_column(Text, primary_key=True)
    document_hash: Mapped[str | None] = mapped_column(Text, nullable=True, index=True) # <-- fixed spelling
    contract_name: Mapped[str | None] = mapped_column(Text)
    contract_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    tax_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    file_url: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[date | None] = mapped_column(Date, default=date.today)

    invoice: Mapped["Invoice | None"] = relationship("Invoice", back_populates="contract", uselist=False, cascade="all, delete-orphan")
    flags: Mapped[list["Flag"]] = relationship("Flag", back_populates="contract", cascade="all, delete-orphan") # <-- added relationship



class Invoice(Base):
    __tablename__ = "invoices"

    invoice_id: Mapped[str] = mapped_column(Text, primary_key=True)
    contract_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("contracts.contract_id"),
        unique=True,
        nullable=False,
    )
    invoice_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    invoice_tax: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    due_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str | None] = mapped_column(Text, default="Pending")
    paid_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[date | None] = mapped_column(Date, default=date.today)

    # Relationship back to Contract
    contract: Mapped["Contract"] = relationship("Contract", back_populates="invoice")

class Flag(Base):
    __tablename__="flags"

    flag_id:Mapped[int]=mapped_column(Integer,primary_key=True,autoincrement=True)
    contract_id:Mapped[str]=mapped_column(Text,ForeignKey("contracts.contract_id"))
    description:Mapped[str]=mapped_column(Text)
    created_at:Mapped[date]=mapped_column(Date,default=date.today)
    updated_at:Mapped[date]=mapped_column(Date,default=date.today)

    contract:Mapped["Contract"]=relationship("Contract",back_populates="flags")