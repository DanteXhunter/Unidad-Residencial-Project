"""Dependencias compartidas: usuario en sesión y protección de rutas."""

import uuid
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User

SESSION_USER_KEY = "user_id"


class RequiresLogin(Exception):
    """Se lanza cuando una ruta protegida no tiene sesión válida.

    ``app.main`` la captura y responde con un redirect a /login, en lugar de
    devolver un 401 que el navegador mostraría como pantalla en blanco.
    """


def login_user(request: Request, user: User) -> None:
    request.session[SESSION_USER_KEY] = str(user.id)


def logout_user(request: Request) -> None:
    request.session.pop(SESSION_USER_KEY, None)


def get_optional_user(
    request: Request, db: Annotated[Session, Depends(get_db)]
) -> User | None:
    """Usuario de la sesión, o None. No lanza excepción."""
    raw_id = request.session.get(SESSION_USER_KEY)
    if not raw_id:
        return None
    try:
        user_id = uuid.UUID(raw_id)
    except (ValueError, TypeError):
        request.session.pop(SESSION_USER_KEY, None)
        return None

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        # La cuenta fue eliminada o desactivada mientras la sesión seguía viva.
        request.session.pop(SESSION_USER_KEY, None)
        return None
    return user


def get_current_user(
    user: Annotated[User | None, Depends(get_optional_user)],
) -> User:
    """Usuario obligatorio: protege todas las rutas del panel."""
    if user is None:
        raise RequiresLogin
    return user


async def get_form_data(request: Request) -> dict[str, str]:
    """Lee el formulario completo como diccionario.

    Es una dependencia asíncrona usada por endpoints síncronos: así FastAPI
    puede leer el cuerpo de la petición sin bloquear, y el endpoint sigue
    ejecutándose en el threadpool (donde SQLAlchemy síncrono es seguro).
    """
    form = await request.form()
    return {key: value for key, value in form.items() if isinstance(value, str)}


CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[Session, Depends(get_db)]
FormData = Annotated[dict[str, str], Depends(get_form_data)]
