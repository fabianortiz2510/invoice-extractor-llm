"""Data schema the LLM must return, validated with Pydantic."""

import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class InvoiceExtraction(BaseModel):
    """Strict JSON structure requested from the LLM.

    Only `fecha_emision` and `valor_total` are required for the flow; the
    rest are best-effort and may come back as null.
    """

    fecha_emision: Optional[str] = Field(
        default=None, description="Invoice issue date, ideally YYYY-MM-DD"
    )
    valor_total: Optional[float] = Field(
        default=None, description="Total amount due, as a number without currency symbols"
    )
    moneda: Optional[str] = Field(
        default=None, description="Currency code or symbol, e.g. COP, USD, $"
    )
    proveedor: Optional[str] = Field(
        default=None, description="Name of the invoice's provider/issuer"
    )
    numero_factura: Optional[str] = Field(
        default=None, description="Invoice number or reference"
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
        """Accepts numbers or strings like '$1,234.56' and converts them to float."""
        if value is None or value == "":
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if not isinstance(value, str):
            raise ValueError(f"Invalid type for valor_total: {type(value)}")

        cleaned = re.sub(r"[^0-9.,-]", "", value.strip())
        if not cleaned:
            return None

        if "," in cleaned and "." in cleaned:
            if cleaned.rfind(",") > cleaned.rfind("."):
                # comma as decimal separator: 1.234,56 -> 1234.56
                cleaned = cleaned.replace(".", "").replace(",", ".")
            else:
                # dot as decimal separator: 1,234.56 -> 1234.56
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
            raise ValueError(f"Could not convert valor_total to a number: {value!r}") from exc
