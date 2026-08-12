"""CRUD de unidades habitacionales."""

import uuid

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.dependencies import CurrentUser, DbSession, FormData
from app.flash import flash
from app.schemas import UnitForm, parse_form
from app.services import units as units_service
from app.services.errors import ServiceError
from app.templating import render

router = APIRouter(prefix="/units", tags=["units"])


def _index_context(db, request: Request) -> dict:
    return {
        "units": units_service.list_units(
            db,
            search=request.query_params.get("q"),
            status=request.query_params.get("status"),
        ),
        "search": request.query_params.get("q", ""),
        "status_filter": request.query_params.get("status", ""),
    }


@router.get("")
def index(request: Request, db: DbSession, user: CurrentUser):
    return render(request, "units/index.html", _index_context(db, request), user=user)


@router.post("/new")
def create(request: Request, db: DbSession, user: CurrentUser, raw: FormData):
    data, errors = parse_form(UnitForm, raw)
    if data is not None:
        try:
            unit = units_service.create_unit(db, data)
            flash(request, f"Unidad {unit.unit_number} creada correctamente.")
            return RedirectResponse("/units", status_code=303)
        except ServiceError as exc:
            errors = exc.as_form_errors()

    # Se vuelve a pintar la lista con el modal abierto y los errores marcados.
    context = _index_context(db, request)
    context |= {"form_errors": errors, "form_data": raw, "open_create": True}
    return render(request, "units/index.html", context, user=user, status_code=422)


@router.get("/{unit_id}/edit")
def edit_form(request: Request, db: DbSession, user: CurrentUser, unit_id: uuid.UUID):
    """Fragmento HTML del modal de edición (lo carga htmx)."""
    unit = units_service.get_unit(db, unit_id)
    if unit is None:
        raise HTTPException(status_code=404, detail="Unidad no encontrada")
    return render(
        request,
        "units/form_modal.html",
        {"unit": unit, "form_data": None, "form_errors": {}},
        user=user,
    )


@router.post("/{unit_id}/edit")
def update(
    request: Request, db: DbSession, user: CurrentUser, unit_id: uuid.UUID, raw: FormData
):
    unit = units_service.get_unit(db, unit_id)
    if unit is None:
        raise HTTPException(status_code=404, detail="Unidad no encontrada")

    data, errors = parse_form(UnitForm, raw)
    if data is not None:
        try:
            units_service.update_unit(db, unit, data)
            flash(request, f"Unidad {unit.unit_number} actualizada.")
            return RedirectResponse("/units", status_code=303)
        except ServiceError as exc:
            errors = exc.as_form_errors()

    context = _index_context(db, request)
    context |= {"form_errors": errors, "form_data": raw, "edit_unit": unit}
    return render(request, "units/index.html", context, user=user, status_code=422)


@router.post("/{unit_id}/delete")
def delete(request: Request, db: DbSession, user: CurrentUser, unit_id: uuid.UUID):
    unit = units_service.get_unit(db, unit_id)
    if unit is None:
        raise HTTPException(status_code=404, detail="Unidad no encontrada")

    numero = unit.unit_number
    try:
        units_service.delete_unit(db, unit)
        flash(request, f"Unidad {numero} eliminada.")
    except ServiceError as exc:
        flash(request, exc.message, "error")
    return RedirectResponse("/units", status_code=303)
