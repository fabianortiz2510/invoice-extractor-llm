"""Esquema de datos que el LLM debe devolver, validado con Pydantic."""

import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class InvoiceExtraction(BaseModel):
    """Estructura JSON estricta que se le pide al LLM.

    Solo `fecha_emision` y `valor_total` son obligatorios para el flujo;
    el resto son mejores esfuerzos y pueden llegar como null.
    """

    fecha_emision: Optional[str] = Field(
        default=None, description="Fecha de emisión de la factura, idealmente YYYY-MM-DD"
    )
    valor_total: Optional[float] = Field(
        default=None, description="Valor total a pagar, como número sin símbolos de moneda"
    )
    moneda: Optional[str] = Field(
        default=None, description="Código o símbolo de la moneda, ej. COP, USD, $"
    )
    proveedor: Optional[str] = Field(
        default=None, description="Nombre del proveedor o emisor de la factura"
    )
    numero_factura: Optional[str] = Field(
        default=None, description="Número o folio de la factura"
    )

    @field_validator("fecha_emision", "moneda", "proveedor", "numero_factura", mode="before")
    @classmethod
    def _blank_string_to_none(cls, value):
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("valor_total", mode="before")
    @classmethod
    def _coerce_valor_total(cls, value):
        """Acepta números o strings tipo '$1.234,56' y los convierte a float."""
        if value is None or value == "":
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if not isinstance(value, str):
            raise ValueError(f"Tipo inválido para valor_total: {type(value)}")

        cleaned = re.sub(r"[^0-9.,-]", "", value.strip())
        if not cleaned:
            return None

        if "," in cleaned and "." in cleaned:
            if cleaned.rfind(",") > cleaned.rfind("."):
                # coma como separador decimal: 1.234,56 -> 1234.56
                cleaned = cleaned.replace(".", "").replace(",", ".")
            else:
                # punto como separador decimal: 1,234.56 -> 1234.56
                cleaned = cleaned.replace(",", "")
        elif "," in cleaned:
            decimals = cleaned.split(",")[-1]
            if len(decimals) == 2:
                cleaned = cleaned.replace(",", ".")
            else:
                cleaned = cleaned.replace(",", "")

        try:
            return float(cleaned)
        except ValueError as exc:
            raise ValueError(f"No se pudo convertir valor_total a número: {value!r}") from exc
