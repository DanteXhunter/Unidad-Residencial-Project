"""Inicio y cierre de sesión."""

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from app.dependencies import DbSession, login_user, logout_user
from app.flash import flash
from app.services import users as users_service
from app.templating import render

router = APIRouter(tags=["auth"])


@router.get("/login")
def login_page(request: Request, db: DbSession):
    """Si ya hay sesión activa, no tiene sentido mostrar el formulario."""
    from app.dependencies import SESSION_USER_KEY

    if request.session.get(SESSION_USER_KEY):
        return RedirectResponse("/dashboard", status_code=303)
    return render(request, "login.html")


@router.post("/login")
def login_submit(
    request: Request,
    db: DbSession,
    email: str = Form(...),
    password: str = Form(...),
):
    user = users_service.authenticate(db, email.strip(), password)
    if user is None:
        # Mensaje genérico a propósito: no revela si el correo existe.
        return render(
            request,
            "login.html",
            {"error": "Correo o contraseña incorrectos.", "email": email},
            status_code=401,
        )

    # Se limpia la sesión anterior antes de iniciar la nueva (evita fijación de sesión).
    request.session.clear()
    login_user(request, user)
    flash(request, f"Bienvenido, {user.full_name.split()[0]}.")
    return RedirectResponse("/dashboard", status_code=303)


@router.post("/logout")
def logout(request: Request):
    logout_user(request)
    flash(request, "Cerraste sesión correctamente.", "info")
    return RedirectResponse("/login", status_code=303)
