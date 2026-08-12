"""CRUD de pagos y cuotas."""

import uuid
from datetime import date

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.dependencies import CurrentUser, DbSession, FormData
from app.flash import flash
from app.schemas import PaymentForm, parse_form
from app.services import payments as payments_service
from app.services import residents as residents_service
from app.services import units as units_service
from app.services.errors import ServiceError
from app.templating import render

router = APIRouter(prefix="/payments", tags=["payments"])


def _int_or_none(value: str | None) -> int | None:
    try:
        return int(value) if value else None
    except ValueError:
        return None


def _index_context(db, request: Request) -> dict:
    month = _int_or_none(request.query_params.get("month"))
    year = _int_or_none(request.query_params.get("year"))
    return {
        "payments": payments_service.list_payments(
            db, status=request.query_params.get("status"), month=month, year=year
        ),
        "units": units_service.list_units_for_select(db),
        "residents": residents_service.list_residents_for_select(db),
        "years": payments_service.available_years(db) or [date.today().year],
        "status_filter": request.query_params.get("status", ""),
        "month_filter": month,
        "year_filter": year,
        "current_year": date.today().year,
        "current_month": date.today().month,
    }


@router.get("")
def index(request: Request, db: DbSession, user: CurrentUser):
    return render(request, "payments/index.html", _index_context(db, request), user=user)


@router.post("/new")
def create(request: Request, db: DbSession, user: CurrentUser, raw: FormData):
    data, errors = parse_form(PaymentForm, raw)
    if data is not None:
        try:
            payments_service.create_payment(db, data)
            flash(request, "Pago registrado correctamente.")
            return RedirectResponse("/payments", status_code=303)
        except ServiceError as exc:
            errors = exc.as_form_errors()

    context = _index_context(db, request)
    context |= {"form_errors": errors, "form_data": raw, "open_create": True}
    return render(request, "payments/index.html", context, user=user, status_code=422)


@router.get("/{payment_id}/edit")
def edit_form(request: Request, db: DbSession, user: CurrentUser, payment_id: uuid.UUID):
    payment = payments_service.get_payment(db, payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    return render(
        request,
        "payments/form_modal.html",
        {
            "payment": payment,
            "units": units_service.list_units_for_select(db),
            "residents": residents_service.list_residents_for_select(db),
            "form_data": None,
            "form_errors": {},
        },
        user=user,
    )


@router.post("/{payment_id}/edit")
def update(
    request: Request, db: DbSession, user: CurrentUser, payment_id: uuid.UUID, raw: FormData
):
    payment = payments_service.get_payment(db, payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Pago no encontrado")

    data, errors = parse_form(PaymentForm, raw)
    if data is not None:
        try:
            payments_service.update_payment(db, payment, data)
            flash(request, "Pago actualizado.")
            return RedirectResponse("/payments", status_code=303)
        except ServiceError as exc:
            errors = exc.as_form_errors()

    context = _index_context(db, request)
    context |= {"form_errors": errors, "form_data": raw, "edit_payment": payment}
    return render(request, "payments/index.html", context, user=user, status_code=422)


@router.post("/{payment_id}/pay")
def mark_paid(request: Request, db: DbSession, user: CurrentUser, payment_id: uuid.UUID):
    """Acción rápida desde la tabla: marcar como pagado con la fecha de hoy."""
    payment = payments_service.get_payment(db, payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Pago no encontrado")

    try:
        payments_service.mark_as_paid(db, payment)
        flash(request, f"Pago de {payment.unit.unit_number} marcado como pagado.")
    except ServiceError as exc:
        flash(request, exc.message, "error")
    # Destino fijo a propósito: usar el header Referer permitiría un redirect
    # abierto hacia un sitio externo.
    return RedirectResponse("/payments", status_code=303)


@router.post("/{payment_id}/delete")
def delete(request: Request, db: DbSession, user: CurrentUser, payment_id: uuid.UUID):
    payment = payments_service.get_payment(db, payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Pago no encontrado")

    payments_service.delete_payment(db, payment)
    flash(request, "Pago eliminado.")
    return RedirectResponse("/payments", status_code=303)
