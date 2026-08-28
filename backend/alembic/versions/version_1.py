"""split facturas into documentos + facturas

Revision ID: version_1
Revises: version_0
Create Date: 2026-08-27

"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "version_1"
down_revision: Union[str, None] = "version_0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "documentos",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=50), nullable=False),
    )

    op.add_column("facturas", sa.Column("documento_id", sa.String(length=36), nullable=True))

    # Backfill: create one "documentos" row per existing "facturas" row, reusing
    # its current filename and created_at. mime_type is unknown for these old
    # rows (it didn't exist yet), so it defaults to application/octet-stream.
    conn = op.get_bind()
    facturas = conn.execute(sa.text("SELECT id, filename, created_at FROM facturas")).fetchall()
    for row in facturas:
        documento_id = str(uuid.uuid4())
        conn.execute(
            sa.text(
                "INSERT INTO documentos (id, filename, mime_type, created_at) "
                "VALUES (:id, :filename, :mime_type, :created_at)"
            ),
            {
                "id": documento_id,
                "filename": row.filename,
                "mime_type": "application/octet-stream",
                "created_at": row.created_at,
            },
        )
        conn.execute(
            sa.text("UPDATE facturas SET documento_id = :documento_id WHERE id = :factura_id"),
            {"documento_id": documento_id, "factura_id": row.id},
        )

    op.alter_column("facturas", "documento_id", nullable=False)
    op.create_foreign_key(
        "fk_facturas_documento_id", "facturas", "documentos", ["documento_id"], ["id"]
    )
    op.drop_column("facturas", "filename")


def downgrade() -> None:
    op.add_column("facturas", sa.Column("filename", sa.String(length=255), nullable=True))

    conn = op.get_bind()
    conn.execute(
        sa.text(
            "UPDATE facturas SET filename = documentos.filename "
            "FROM documentos WHERE facturas.documento_id = documentos.id"
        )
    )

    op.drop_constraint("fk_facturas_documento_id", "facturas", type_="foreignkey")
    op.drop_column("facturas", "documento_id")
    op.drop_table("documentos")
