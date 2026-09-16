from datetime import date

from sqlalchemy import Date, Integer, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from pgvector.sqlalchemy import Vector


class Base(DeclarativeBase):
    pass


class ContractRule(Base):
    __tablename__ = "contract_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

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