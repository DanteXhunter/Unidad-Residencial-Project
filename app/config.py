"""Configuración de la aplicación, leída desde variables de entorno / .env."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Residencial Admin"
    database_url: str = "postgresql+psycopg://localhost:5432/residencial_dev"
    secret_key: str = "llave-de-desarrollo-no-usar-en-produccion"
    session_max_age: int = 60 * 60 * 8
    cookie_secure: bool = False

    @property
    def sqlalchemy_url(self) -> str:
        """Normaliza la URL al driver psycopg 3.

        Supabase entrega la cadena como ``postgresql://...``; SQLAlchemy la
        interpretaría con psycopg2, que no está instalado.
        """
        url = self.database_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
