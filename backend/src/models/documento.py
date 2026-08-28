from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.core.database import Base
from src.models.base import BaseMixin


class Documento(Base, BaseMixin):
    __tablename__ = "documentos"

    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(50), nullable=False)

    facturas: Mapped[list["Invoice"]] = relationship(back_populates="documento")  # noqa: F821
