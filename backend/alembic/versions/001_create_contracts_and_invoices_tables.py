"""Create contracts and invoices tables

Revision ID: 001_create_tables
Revises: 
Create Date: 2026-09-16 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001_create_tables"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # 2. Create contracts table
    op.create_table(
        "contracts",
        sa.Column("contract_id", sa.Text(), nullable=False, primary_key=True),
        sa.Column("contract_name", sa.Text(), nullable=True),
        sa.Column("contract_amount", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("tax_rate", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("file_url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.Date(), server_default=sa.text("CURRENT_DATE"), nullable=True),
    )

    # 3. Create invoices table (with 1:1 UNIQUE constraint on contract_id)
    op.create_table(
        "invoices",
        sa.Column("invoice_id", sa.Text(), nullable=False, primary_key=True),
        sa.Column("contract_id", sa.Text(), sa.ForeignKey("contracts.contract_id"), nullable=False, unique=True),
        sa.Column("invoice_amount", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("invoice_tax", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("status", sa.Text(), server_default="Pending", nullable=True),
        sa.Column("paid_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.Date(), server_default=sa.text("CURRENT_DATE"), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("invoices")
    op.drop_table("contracts")
