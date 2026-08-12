"""Mensajes flash: se guardan en la sesión y se consumen en el siguiente render.

Permiten el patrón POST -> redirect -> GET mostrando "Unidad creada
correctamente" sin exponer el mensaje en la URL.
"""

from typing import Literal

from starlette.requests import Request

FLASH_KEY = "_flashes"
Level = Literal["success", "error", "info"]


def flash(request: Request, message: str, level: Level = "success") -> None:
    request.session.setdefault(FLASH_KEY, []).append({"level": level, "message": message})


def get_flashes(request: Request) -> list[dict]:
    """Devuelve los mensajes pendientes y los elimina de la sesión."""
    return request.session.pop(FLASH_KEY, [])
