from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.invoice import Invoice


class InvoiceService:
    @staticmethod
    async def create_from_extraction(
        db: AsyncSession, filename: str, data: dict, raw_response: str | None
    ) -> Invoice:
        invoice = Invoice(
            filename=filename,
            fecha_emision=data.get("fecha_emision"),
            fecha_emision_valida=data.get("fecha_emision_valida", False),
            valor_total=data.get("valor_total"),
            moneda=data.get("moneda"),
            proveedor=data.get("proveedor"),
            numero_factura=data.get("numero_factura"),
            raw_llm_response=raw_response,
        )
        db.add(invoice)
        await db.commit()
        await db.refresh(invoice)
        return invoice

    @staticmethod
    async def list_invoices(db: AsyncSession) -> list[Invoice]:
        result = await db.execute(select(Invoice).order_by(Invoice.created_at.desc()))
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(db: AsyncSession, invoice_id: str) -> Invoice | None:
        result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
        return result.scalar_one_or_none()
