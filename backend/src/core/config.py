"""Configuración de la aplicación leída desde variables de entorno / .env."""

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str

    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    # Origen permitido para CORS (la SPA de Vite corre en este puerto por defecto).
    FRONTEND_URL: str = "http://localhost:5173"


settings = Settings()
