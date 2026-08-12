"""Capa de servicios: toda la lógica de negocio vive aquí, no en los routers."""

from app.services.errors import ServiceError

__all__ = ["ServiceError"]
