"""Orchestrates invoice data extraction: file -> image -> LLM -> validation."""

import base64
import io
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import pymupdf  # PyMuPDF
from dateutil import parser as date_parser
from PIL import Image
from pydantic import ValidationError

from src.llm.clients import LLMError, call_llm
from src.llm.schema import InvoiceExtraction

logger = logging.getLogger(__name__)

SUPPORTED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg"}
MAX_RETRIES = 2  # 1 initial attempt + 1 correction retry

SYSTEM_PROMPT = """Eres un asistente experto en extraer datos de facturas de servicios \
(agua, luz, gas, telecomunicaciones, etc.) a partir de una imagen.
Devuelve EXCLUSIVAMENTE un objeto JSON valido, sin texto adicional, sin markdown y sin explicaciones.
El JSON debe tener exactamente estas claves:
- "fecha_emision": fecha de emision de la factura en formato YYYY-MM-DD. Si no puedes determinarla, usa null.
- "valor_total": valor total a pagar, como numero (sin simbolos de moneda ni separadores de miles). Si no puedes determinarlo, usa null.
- "moneda": codigo o simbolo de la moneda (ej. "COP", "USD", "EUR", "$"). Si no aparece, usa null.
- "proveedor": nombre del proveedor o emisor de la factura. Si no aparece, usa null.
- "numero_factura": numero o folio de la factura. Si no aparece, usa null.

No inventes datos. Si un campo no es visible o no esta presente en la factura, usa null para ese campo."""

USER_PROMPT = "Extrae los datos de la factura de la imagen adjunta y responde solo con el JSON solicitado."


@dataclass
class ExtractionResult:
    success: bool
    data: Optional[dict] = None
    raw_response: Optional[str] = None
    error: Optional[str] = None


def file_to_image_bytes(file_bytes: bytes, filename: str) -> tuple[bytes, str]:
    """Convert the uploaded file (image or PDF) to PNG bytes. Returns (bytes, mime_type)."""
    extension = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

    if extension == "pdf":
        return _pdf_first_page_to_png(file_bytes), "image/png"

    if extension in SUPPORTED_IMAGE_EXTENSIONS:
        try:
            image = Image.open(io.BytesIO(file_bytes))
            image = image.convert("RGB")
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            return buffer.getvalue(), "image/png"
        except Exception as exc:
            raise ValueError(f"No se pudo procesar la imagen: {exc}") from exc

    raise ValueError(f"Formato de archivo no soportado: .{extension}")


def _pdf_first_page_to_png(pdf_bytes: bytes) -> bytes:
    doc = None
    try:
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        if doc.page_count == 0:
            raise ValueError("El PDF no contiene paginas.")
        page = doc.load_page(0)
        # 2x scale improves text legibility for the vision model.
        pixmap = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))
        return pixmap.tobytes("png")
    except Exception as exc:
        raise ValueError(f"No se pudo convertir el PDF a imagen: {exc}") from exc
    finally:
        if doc is not None:
            doc.close()


def normalize_date(raw_date: Optional[str]) -> tuple[Optional[str], bool]:
    """Normalize a date to YYYY-MM-DD.

    Returns (normalized_date, is_valid). If the date can't be parsed, the
    original value is returned with is_valid=False (never fails silently —
    the caller decides how to flag it).
    """
    if raw_date is None:
        return None, False

    raw_date = str(raw_date).strip()
    if not raw_date:
        return None, False

    # Try a strict ISO parse first: SYSTEM_PROMPT already asks the LLM for
    # YYYY-MM-DD, and that format is unambiguous (year comes first). Going
    # straight to dateutil with dayfirst=True would misinterpret already
    # correct ISO dates when day and month are both <= 12 (e.g. it turns
    # "2024-05-01" into 2024-01-05).
    try:
        parsed = datetime.strptime(raw_date, "%Y-%m-%d")
        return parsed.strftime("%Y-%m-%d"), True
    except ValueError:
        pass

    try:
        parsed = date_parser.parse(raw_date, dayfirst=True, fuzzy=True)
        return parsed.strftime("%Y-%m-%d"), True
    except (ValueError, OverflowError, TypeError):
        return raw_date, False


def _strip_markdown_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()
    return cleaned


def _parse_and_validate(raw_text: str) -> InvoiceExtraction:
    cleaned = _strip_markdown_fences(raw_text)
    payload = json.loads(cleaned)
    return InvoiceExtraction.model_validate(payload)


def extract_invoice_data(file_bytes: bytes, filename: str) -> ExtractionResult:
    """Main entry point: processes an invoice file end to end.

    Provider fallback (LLM_PRIMARY / LLM_FALLBACK) is handled internally by
    litellm inside call_llm() — this function only retries against the same
    LLM when the response isn't valid JSON, asking it to fix the format.

    Synchronous function (litellm.completion is synchronous) — the FastAPI
    router must call it via run_in_threadpool to avoid blocking the event loop.
    """
    try:
        image_bytes, mime_type = file_to_image_bytes(file_bytes, filename)
    except ValueError as exc:
        return ExtractionResult(success=False, error=str(exc))

    b64_image = base64.standard_b64encode(image_bytes).decode("utf-8")

    raw_response = None
    last_error = None

    for attempt in range(MAX_RETRIES):
        prompt = USER_PROMPT
        if attempt > 0:
            prompt = (
                f"{USER_PROMPT}\n\n"
                f"Tu respuesta anterior no cumplia el formato JSON solicitado. "
                f"Error de validacion: {last_error}\n"
                "Corrige el formato y responde EXCLUSIVAMENTE con el JSON valido, sin texto adicional."
            )

        try:
            raw_response = call_llm(b64_image, mime_type, SYSTEM_PROMPT, prompt)
        except LLMError as exc:
            return ExtractionResult(success=False, error=str(exc), raw_response=raw_response)

        try:
            invoice = _parse_and_validate(raw_response)
        except (json.JSONDecodeError, ValidationError) as exc:
            last_error = str(exc)
            logger.warning("Attempt %d: invalid JSON from the LLM: %s", attempt + 1, last_error)
            continue

        fecha_normalizada, fecha_valida = normalize_date(invoice.fecha_emision)
        data = {
            "fecha_emision": fecha_normalizada,
            "fecha_emision_valida": fecha_valida,
            "valor_total": invoice.valor_total,
            "moneda": invoice.moneda,
            "proveedor": invoice.proveedor,
            "numero_factura": invoice.numero_factura,
        }
        return ExtractionResult(success=True, data=data, raw_response=raw_response)

    return ExtractionResult(
        success=False,
        error=(
            "El LLM no devolvio un JSON valido tras "
            f"{MAX_RETRIES} intentos. Ultimo error: {last_error}"
        ),
        raw_response=raw_response,
    )
