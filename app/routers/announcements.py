"""CRUD de avisos."""

import uuid

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.dependencies import CurrentUser, DbSession, FormData
from app.flash import flash
from app.schemas import AnnouncementForm, parse_form
from app.services import announcements as announcements_service
from app.services.errors import ServiceError
from app.templating import render

router = APIRouter(prefix="/announcements", tags=["announcements"])


def _index_context(db, request: Request) -> dict:
    return {
        "announcements": announcements_service.list_announcements(
            db, status=request.query_params.get("status")
        ),
        "status_filter": request.query_params.get("status", ""),
    }


@router.get("")
def index(request: Request, db: DbSession, user: CurrentUser):
    return render(
        request, "announcements/index.html", _index_context(db, request), user=user
    )


@router.post("/new")
def create(request: Request, db: DbSession, user: CurrentUser, raw: FormData):
    data, errors = parse_form(AnnouncementForm, raw)
    if data is not None:
        try:
            announcements_service.create_announcement(db, data, user)
            flash(request, "Aviso creado correctamente.")
            return RedirectResponse("/announcements", status_code=303)
        except ServiceError as exc:
            errors = exc.as_form_errors()

    context = _index_context(db, request)
    context |= {"form_errors": errors, "form_data": raw, "open_create": True}
    return render(request, "announcements/index.html", context, user=user, status_code=422)


@router.get("/{announcement_id}/edit")
def edit_form(
    request: Request, db: DbSession, user: CurrentUser, announcement_id: uuid.UUID
):
    announcement = announcements_service.get_announcement(db, announcement_id)
    if announcement is None:
        raise HTTPException(status_code=404, detail="Aviso no encontrado")
    return render(
        request,
        "announcements/form_modal.html",
        {"announcement": announcement, "form_data": None, "form_errors": {}},
        user=user,
    )


@router.post("/{announcement_id}/edit")
def update(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    announcement_id: uuid.UUID,
    raw: FormData,
):
    announcement = announcements_service.get_announcement(db, announcement_id)
    if announcement is None:
        raise HTTPException(status_code=404, detail="Aviso no encontrado")

    data, errors = parse_form(AnnouncementForm, raw)
    if data is not None:
        try:
            announcements_service.update_announcement(db, announcement, data)
            flash(request, "Aviso actualizado.")
            return RedirectResponse("/announcements", status_code=303)
        except ServiceError as exc:
            errors = exc.as_form_errors()

    context = _index_context(db, request)
    context |= {
        "form_errors": errors,
        "form_data": raw,
        "edit_announcement": announcement,
    }
    return render(request, "announcements/index.html", context, user=user, status_code=422)


@router.post("/{announcement_id}/delete")
def delete(
    request: Request, db: DbSession, user: CurrentUser, announcement_id: uuid.UUID
):
    announcement = announcements_service.get_announcement(db, announcement_id)
    if announcement is None:
        raise HTTPException(status_code=404, detail="Aviso no encontrado")

    announcements_service.delete_announcement(db, announcement)
    flash(request, "Aviso eliminado.")
    return RedirectResponse("/announcements", status_code=303)
