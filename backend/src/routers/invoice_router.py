"""REST endpoints for invoices."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.llm.extractor import extract_invoice_data
from src.schemas.invoice import InvoiceListItem, InvoiceResponse
from src.services.invoice_service import InvoiceService

router = APIRouter()

ALLOWED_CONTENT_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}


@router.post("/extract", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def extract_invoice(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Uploads an invoice (PNG/JPG/PDF), extracts it with the configured LLM, and persists it."""
    extension = file.filename.lower().rsplit(".", 1)[-1] if file.filename and "." in file.filename else ""
    if extension not in ALLOWED_CONTENT_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato de archivo no soportado: .{extension}. Usa PNG, JPG o PDF.",
        )

    content = await file.read()

    # extract_invoice_data is synchronous (litellm.completion is synchronous) —
    # run it in a threadpool so it doesn't block FastAPI's event loop.
    result = await run_in_threadpool(extract_invoice_data, content, file.filename)

    if not result.success:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=result.error)

    invoice = await InvoiceService.create_from_extraction(
        db, filename=file.filename, data=result.data, raw_response=result.raw_response
    )
    return invoice


@router.get("", response_model=list[InvoiceListItem])
async def list_invoices(db: AsyncSession = Depends(get_db)):
    """History of processed invoices, most recent first."""
    return await InvoiceService.list_invoices(db)


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(invoice_id: str, db: AsyncSession = Depends(get_db)):
    """Invoice detail, including the LLM's raw response."""
    invoice = await InvoiceService.get_by_id(db, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Factura no encontrada.")
    return invoice
