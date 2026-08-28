"""SQLAlchemy model for a processed invoice."""

from sqlalchemy import Boolean, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.models.base import BaseMixin
from src.models.documento import Documento


class Invoice(Base, BaseMixin):
    __tablename__ = "facturas"

    documento_id: Mapped[str] = mapped_column(String(36), ForeignKey("documentos.id"), nullable=False)

    fecha_emision: Mapped[str | None] = mapped_column(String(10), nullable=True)
    fecha_emision_valida: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    valor_total: Mapped[float | None] = mapped_column(Float, nullable=True)
    moneda: Mapped[str | None] = mapped_column(String(10), nullable=True)
    proveedor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    numero_factura: Mapped[str | None] = mapped_column(String(100), nullable=True)

    raw_llm_response: Mapped[str | None] = mapped_column(Text, nullable=True)

    documento: Mapped[Documento] = relationship(back_populates="facturas")

    @property
    def filename(self) -> str:
        return self.documento.filename
