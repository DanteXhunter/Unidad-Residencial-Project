"""CRUD de residentes."""

import uuid

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.dependencies import CurrentUser, DbSession, FormData
from app.flash import flash
from app.schemas import ResidentForm, parse_form
from app.services import residents as residents_service
from app.services import units as units_service
from app.services.errors import ServiceError
from app.templating import render

router = APIRouter(prefix="/residents", tags=["residents"])


def _index_context(db, request: Request) -> dict:
    return {
        "residents": residents_service.list_residents(
            db,
            search=request.query_params.get("q"),
            status=request.query_params.get("status"),
        ),
        # El <select> de unidades se alimenta de la base: nunca se escribe el id a mano.
        "units": units_service.list_units_for_select(db),
        "search": request.query_params.get("q", ""),
        "status_filter": request.query_params.get("status", ""),
    }


@router.get("")
def index(request: Request, db: DbSession, user: CurrentUser):
    return render(request, "residents/index.html", _index_context(db, request), user=user)


@router.post("/new")
def create(request: Request, db: DbSession, user: CurrentUser, raw: FormData):
    data, errors = parse_form(ResidentForm, raw)
    if data is not None:
        try:
            resident = residents_service.create_resident(db, data)
            flash(request, f"Residente {resident.full_name} registrado correctamente.")
            return RedirectResponse("/residents", status_code=303)
        except ServiceError as exc:
            errors = exc.as_form_errors()

    context = _index_context(db, request)
    context |= {"form_errors": errors, "form_data": raw, "open_create": True}
    return render(request, "residents/index.html", context, user=user, status_code=422)


@router.get("/{resident_id}/edit")
def edit_form(request: Request, db: DbSession, user: CurrentUser, resident_id: uuid.UUID):
    resident = residents_service.get_resident(db, resident_id)
    if resident is None:
        raise HTTPException(status_code=404, detail="Residente no encontrado")
    return render(
        request,
        "residents/form_modal.html",
        {
            "resident": resident,
            "units": units_service.list_units_for_select(db),
            "form_data": None,
            "form_errors": {},
        },
        user=user,
    )


@router.post("/{resident_id}/edit")
def update(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    resident_id: uuid.UUID,
    raw: FormData,
):
    resident = residents_service.get_resident(db, resident_id)
    if resident is None:
        raise HTTPException(status_code=404, detail="Residente no encontrado")

    data, errors = parse_form(ResidentForm, raw)
    if data is not None:
        try:
            residents_service.update_resident(db, resident, data)
            flash(request, f"Datos de {resident.full_name} actualizados.")
            return RedirectResponse("/residents", status_code=303)
        except ServiceError as exc:
            errors = exc.as_form_errors()

    context = _index_context(db, request)
    context |= {"form_errors": errors, "form_data": raw, "edit_resident": resident}
    return render(request, "residents/index.html", context, user=user, status_code=422)


@router.post("/{resident_id}/delete")
def delete(request: Request, db: DbSession, user: CurrentUser, resident_id: uuid.UUID):
    resident = residents_service.get_resident(db, resident_id)
    if resident is None:
        raise HTTPException(status_code=404, detail="Residente no encontrado")

    nombre = resident.full_name
    try:
        residents_service.delete_resident(db, resident)
        flash(request, f"Residente {nombre} eliminado.")
    except ServiceError as exc:
        flash(request, exc.message, "error")
    return RedirectResponse("/residents", status_code=303)
