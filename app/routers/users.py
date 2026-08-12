"""CRUD de usuarios administrativos."""

import uuid

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.dependencies import CurrentUser, DbSession, FormData
from app.flash import flash
from app.schemas import UserCreateForm, UserUpdateForm, parse_form
from app.services import users as users_service
from app.services.errors import ServiceError
from app.templating import render

router = APIRouter(prefix="/users", tags=["users"])


def _index_context(db, request: Request) -> dict:
    return {
        "users": users_service.list_users(db, search=request.query_params.get("q")),
        "search": request.query_params.get("q", ""),
    }


@router.get("")
def index(request: Request, db: DbSession, user: CurrentUser):
    return render(request, "users/index.html", _index_context(db, request), user=user)


@router.post("/new")
def create(request: Request, db: DbSession, user: CurrentUser, raw: FormData):
    data, errors = parse_form(UserCreateForm, raw)
    if data is not None:
        try:
            nuevo = users_service.create_user(db, data)
            flash(request, f"Usuario {nuevo.full_name} creado correctamente.")
            return RedirectResponse("/users", status_code=303)
        except ServiceError as exc:
            errors = exc.as_form_errors()

    context = _index_context(db, request)
    context |= {"form_errors": errors, "form_data": raw, "open_create": True}
    return render(request, "users/index.html", context, user=user, status_code=422)


@router.get("/{user_id}/edit")
def edit_form(request: Request, db: DbSession, user: CurrentUser, user_id: uuid.UUID):
    target = users_service.get_user(db, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return render(
        request,
        "users/form_modal.html",
        {"target": target, "form_data": None, "form_errors": {}},
        user=user,
    )


@router.post("/{user_id}/edit")
def update(
    request: Request, db: DbSession, user: CurrentUser, user_id: uuid.UUID, raw: FormData
):
    target = users_service.get_user(db, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    data, errors = parse_form(UserUpdateForm, raw)
    if data is not None:
        try:
            users_service.update_user(db, target, data, current_user=user)
            flash(request, f"Usuario {target.full_name} actualizado.")
            return RedirectResponse("/users", status_code=303)
        except ServiceError as exc:
            errors = exc.as_form_errors()

    context = _index_context(db, request)
    context |= {"form_errors": errors, "form_data": raw, "edit_user": target}
    return render(request, "users/index.html", context, user=user, status_code=422)


@router.post("/{user_id}/delete")
def delete(request: Request, db: DbSession, user: CurrentUser, user_id: uuid.UUID):
    target = users_service.get_user(db, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    nombre = target.full_name
    try:
        users_service.delete_user(db, target, current_user=user)
        flash(request, f"Usuario {nombre} eliminado.")
    except ServiceError as exc:
        flash(request, exc.message, "error")
    return RedirectResponse("/users", status_code=303)
