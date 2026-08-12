"""Punto de entrada de la aplicación.

Arranque en desarrollo:
    uvicorn app.main:app --reload
"""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.dependencies import SESSION_USER_KEY, RequiresLogin
from app.routers import (
    announcements,
    auth,
    dashboard,
    incidents,
    payments,
    residents,
    units,
    users,
)
from app.templating import STATIC_DIR, render

logger = logging.getLogger("residencial")

app = FastAPI(
    title=settings.app_name,
    description="Panel administrativo de unidades residenciales.",
    docs_url=None,  # es una app web, no una API pública
    redoc_url=None,
)

# La sesión viaja en una cookie firmada (no cifrada): solo se guarda el id del
# usuario, nunca datos sensibles.
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    max_age=settings.session_max_age,
    same_site="lax",
    https_only=settings.cookie_secure,
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(units.router)
app.include_router(residents.router)
app.include_router(payments.router)
app.include_router(incidents.router)
app.include_router(announcements.router)
app.include_router(users.router)


@app.get("/", include_in_schema=False)
def root(request: Request):
    if request.session.get(SESSION_USER_KEY):
        return RedirectResponse("/dashboard", status_code=303)
    return RedirectResponse("/login", status_code=303)


@app.exception_handler(RequiresLogin)
def handle_requires_login(request: Request, exc: RequiresLogin):
    """Ruta protegida sin sesión: se manda al login en vez de devolver un 401."""
    return RedirectResponse("/login", status_code=303)


@app.exception_handler(StarletteHTTPException)
def handle_http_exception(request: Request, exc: StarletteHTTPException):
    """404 y demás errores HTTP con una página del mismo diseño que la app."""
    if exc.status_code == 404:
        return render(
            request,
            "errors/404.html",
            {"detail": exc.detail},
            status_code=404,
        )
    return render(
        request,
        "errors/error.html",
        {"status_code": exc.status_code, "detail": exc.detail},
        status_code=exc.status_code,
    )


@app.exception_handler(Exception)
def handle_unexpected_error(request: Request, exc: Exception):
    """Un error inesperado no debe dejar la pantalla en blanco.

    Al usuario se le muestra un mensaje amable; el error real se escribe
    completo en la consola del servidor para poder depurarlo.
    """
    logger.exception("Error no controlado en %s %s", request.method, request.url.path)
    return render(request, "errors/error.html", {"status_code": 500}, status_code=500)
