"""initial migration: facturas table

Revision ID: version_0
Revises:
Create Date: 2026-08-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "version_0"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "facturas",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("fecha_emision", sa.String(length=10), nullable=True),
        sa.Column("fecha_emision_valida", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("valor_total", sa.Float(), nullable=True),
        sa.Column("moneda", sa.String(length=10), nullable=True),
        sa.Column("proveedor", sa.String(length=255), nullable=True),
        sa.Column("numero_factura", sa.String(length=100), nullable=True),
        sa.Column("raw_llm_response", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("facturas")
