"""CRUD de incidencias."""

import uuid

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.dependencies import CurrentUser, DbSession, FormData
from app.flash import flash
from app.models.enums import IncidentStatus
from app.schemas import IncidentForm, parse_form
from app.services import incidents as incidents_service
from app.services import units as units_service
from app.services.errors import ServiceError
from app.templating import render

router = APIRouter(prefix="/incidents", tags=["incidents"])


def _index_context(db, request: Request) -> dict:
    return {
        "incidents": incidents_service.list_incidents(
            db,
            priority=request.query_params.get("priority"),
            status=request.query_params.get("status"),
        ),
        "units": units_service.list_units_for_select(db),
        "priority_filter": request.query_params.get("priority", ""),
        "status_filter": request.query_params.get("status", ""),
    }


@router.get("")
def index(request: Request, db: DbSession, user: CurrentUser):
    return render(request, "incidents/index.html", _index_context(db, request), user=user)


@router.post("/new")
def create(request: Request, db: DbSession, user: CurrentUser, raw: FormData):
    data, errors = parse_form(IncidentForm, raw)
    if data is not None:
        try:
            incidents_service.create_incident(db, data)
            flash(request, "Incidencia registrada correctamente.")
            return RedirectResponse("/incidents", status_code=303)
        except ServiceError as exc:
            errors = exc.as_form_errors()

    context = _index_context(db, request)
    context |= {"form_errors": errors, "form_data": raw, "open_create": True}
    return render(request, "incidents/index.html", context, user=user, status_code=422)


@router.get("/{incident_id}/edit")
def edit_form(request: Request, db: DbSession, user: CurrentUser, incident_id: uuid.UUID):
    incident = incidents_service.get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")
    return render(
        request,
        "incidents/form_modal.html",
        {
            "incident": incident,
            "units": units_service.list_units_for_select(db),
            "form_data": None,
            "form_errors": {},
        },
        user=user,
    )


@router.post("/{incident_id}/edit")
def update(
    request: Request, db: DbSession, user: CurrentUser, incident_id: uuid.UUID, raw: FormData
):
    incident = incidents_service.get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")

    data, errors = parse_form(IncidentForm, raw)
    if data is not None:
        try:
            incidents_service.update_incident(db, incident, data)
            flash(request, "Incidencia actualizada.")
            return RedirectResponse("/incidents", status_code=303)
        except ServiceError as exc:
            errors = exc.as_form_errors()

    context = _index_context(db, request)
    context |= {"form_errors": errors, "form_data": raw, "edit_incident": incident}
    return render(request, "incidents/index.html", context, user=user, status_code=422)


@router.post("/{incident_id}/status")
def change_status(
    request: Request, db: DbSession, user: CurrentUser, incident_id: uuid.UUID, raw: FormData
):
    """Avance rápido del flujo Pendiente -> En proceso -> Resuelta."""
    incident = incidents_service.get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")

    try:
        nuevo_estado = IncidentStatus(raw.get("status", ""))
    except ValueError:
        flash(request, "Estado no válido.", "error")
        return RedirectResponse("/incidents", status_code=303)

    incidents_service.change_status(db, incident, nuevo_estado)
    flash(request, f'Incidencia marcada como "{nuevo_estado}".')
    return RedirectResponse("/incidents", status_code=303)


@router.post("/{incident_id}/delete")
def delete(request: Request, db: DbSession, user: CurrentUser, incident_id: uuid.UUID):
    incident = incidents_service.get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")

    incidents_service.delete_incident(db, incident)
    flash(request, "Incidencia eliminada.")
    return RedirectResponse("/incidents", status_code=303)
