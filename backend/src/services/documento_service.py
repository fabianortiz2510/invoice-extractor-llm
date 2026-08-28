from sqlalchemy.ext.asyncio import AsyncSession
from src.models.documento import Documento

class DocumentoService:
    @staticmethod
    async def create(db: AsyncSession, filename: str, mime_type: str) -> Documento:
        documento = Documento(filename=filename, mime_type=mime_type)
        db.add(documento)
        await db.flush()  # assigns documento.id without committing yet
        return documento
