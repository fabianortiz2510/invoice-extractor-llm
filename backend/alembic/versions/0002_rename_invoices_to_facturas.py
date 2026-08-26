"""rename invoices table to facturas

Revision ID: 0002_rename_facturas
Revises: 0001_initial
Create Date: 2026-08-24

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0002_rename_facturas"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.rename_table("invoices", "facturas")


def downgrade() -> None:
    op.rename_table("facturas", "invoices")
