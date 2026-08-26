"""Modelo SQLAlchemy de una factura procesada."""

from sqlalchemy import Boolean, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.models.base import BaseMixin


class Invoice(Base, BaseMixin):
    __tablename__ = "facturas"

    filename: Mapped[str] = mapped_column(String(255), nullable=False)

    fecha_emision: Mapped[str | None] = mapped_column(String(10), nullable=True)
    fecha_emision_valida: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    valor_total: Mapped[float | None] = mapped_column(Float, nullable=True)
    moneda: Mapped[str | None] = mapped_column(String(10), nullable=True)
    proveedor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    numero_factura: Mapped[str | None] = mapped_column(String(100), nullable=True)

    raw_llm_response: Mapped[str | None] = mapped_column(Text, nullable=True)
