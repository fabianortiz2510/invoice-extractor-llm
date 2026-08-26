"""Punto de entrada de la API FastAPI del extractor de facturas."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.core.database import engine
from src.domains.invoices.router import router as invoices_router

# Registra el modelo en Base.metadata (necesario para Alembic / create_all).
from src.domains.invoices import models as _invoices_models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(title="Invoice Extractor API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}


app.include_router(invoices_router, prefix="/api/v1/invoices", tags=["Invoices"])
