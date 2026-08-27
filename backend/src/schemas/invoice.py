"""Pydantic input/output schemas for the API (distinct from the LLM's schema)."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class InvoiceResponse(BaseModel):
    id: str
    filename: str
    fecha_emision: Optional[str]
    fecha_emision_valida: bool
    valor_total: Optional[float]
    moneda: Optional[str]
    proveedor: Optional[str]
    numero_factura: Optional[str]
    raw_llm_response: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvoiceListItem(BaseModel):
    """Summary version for the history listing (without the raw JSON)."""

    id: str
    filename: str
    fecha_emision: Optional[str]
    fecha_emision_valida: bool
    valor_total: Optional[float]
    moneda: Optional[str]
    proveedor: Optional[str]
    numero_factura: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
