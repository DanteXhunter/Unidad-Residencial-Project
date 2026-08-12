"""Reglas de negocio de pagos y cuotas."""

import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Payment
from app.models.enums import PaymentStatus
from app.schemas import PaymentForm
from app.services.errors import ServiceError

_WITH_RELATIONS = (selectinload(Payment.unit), selectinload(Payment.resident))


def list_payments(
    db: Session,
    *,
    status: str | None = None,
    month: int | None = None,
    year: int | None = None,
    unit_id: uuid.UUID | None = None,
) -> list[Payment]:
    stmt = (
        select(Payment)
        .options(*_WITH_RELATIONS)
        .order_by(Payment.period_year.desc(), Payment.period_month.desc(), Payment.created_at.desc())
    )
    if status:
        stmt = stmt.where(Payment.status == status)
    if month:
        stmt = stmt.where(Payment.period_month == month)
    if year:
        stmt = stmt.where(Payment.period_year == year)
    if unit_id:
        stmt = stmt.where(Payment.unit_id == unit_id)
    return list(db.scalars(stmt))


def get_payment(db: Session, payment_id: uuid.UUID) -> Payment | None:
    return db.get(Payment, payment_id)


def _validate_resident_belongs_to_unit(db: Session, data: PaymentForm) -> None:
    """Evita registrar un pago de un residente que no vive en esa unidad."""
    if data.resident_id is None:
        return
    from app.models import Resident  # import local para evitar ciclo

    resident = db.get(Resident, data.resident_id)
    if resident is None:
        raise ServiceError("El residente seleccionado ya no existe.", field="resident_id")
    if resident.unit_id != data.unit_id:
        raise ServiceError(
            f"{resident.full_name} no está registrado en esa unidad.", field="resident_id"
        )


def create_payment(db: Session, data: PaymentForm) -> Payment:
    _validate_resident_belongs_to_unit(db, data)
    payload = data.model_dump()
    payment = Payment(**payload)
    _sync_payment_date(payment)
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def update_payment(db: Session, payment: Payment, data: PaymentForm) -> Payment:
    _validate_resident_belongs_to_unit(db, data)
    for field, value in data.model_dump().items():
        setattr(payment, field, value)
    _sync_payment_date(payment)
    db.commit()
    db.refresh(payment)
    return payment


def _sync_payment_date(payment: Payment) -> None:
    """Mantiene coherentes estado y fecha de pago."""
    if payment.status == PaymentStatus.PAGADO and payment.payment_date is None:
        payment.payment_date = date.today()
    elif payment.status != PaymentStatus.PAGADO:
        payment.payment_date = None


def mark_as_paid(db: Session, payment: Payment) -> Payment:
    """Acción rápida desde la tabla: marca el pago como pagado con fecha de hoy."""
    if payment.status == PaymentStatus.PAGADO:
        raise ServiceError("Este pago ya estaba marcado como pagado.")
    payment.status = PaymentStatus.PAGADO
    payment.payment_date = date.today()
    db.commit()
    db.refresh(payment)
    return payment


def delete_payment(db: Session, payment: Payment) -> None:
    db.delete(payment)
    db.commit()


def count_by_status(db: Session) -> dict[str, int]:
    rows = db.execute(select(Payment.status, func.count()).group_by(Payment.status)).all()
    counts = {status.value: 0 for status in PaymentStatus}
    for status, total in rows:
        key = status.value if hasattr(status, "value") else str(status)
        counts[key] = total
    return counts


def total_collected(db: Session) -> float:
    return float(
        db.scalar(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(
                Payment.status == PaymentStatus.PAGADO
            )
        )
        or 0
    )


def outstanding_amount(db: Session) -> float:
    return float(
        db.scalar(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(
                Payment.status.in_([PaymentStatus.PENDIENTE, PaymentStatus.VENCIDO])
            )
        )
        or 0
    )


def available_years(db: Session) -> list[int]:
    return [
        year
        for (year,) in db.execute(
            select(Payment.period_year).distinct().order_by(Payment.period_year.desc())
        ).all()
    ]


def recent_payments(db: Session, limit: int = 5) -> list[Payment]:
    return list(
        db.scalars(
            select(Payment)
            .options(*_WITH_RELATIONS)
            .order_by(Payment.created_at.desc())
            .limit(limit)
        )
    )
