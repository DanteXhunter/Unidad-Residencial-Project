"""Reglas de negocio de residentes."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Payment, Resident
from app.models.enums import ResidentStatus
from app.schemas import ResidentForm
from app.services.errors import ServiceError


def list_residents(
    db: Session,
    *,
    search: str | None = None,
    status: str | None = None,
    unit_id: uuid.UUID | None = None,
) -> list[Resident]:
    # selectinload evita el problema N+1 al pintar el número de unidad por fila.
    stmt = (
        select(Resident)
        .options(selectinload(Resident.unit))
        .order_by(Resident.full_name)
    )
    if search:
        stmt = stmt.where(Resident.full_name.ilike(f"%{search}%"))
    if status:
        stmt = stmt.where(Resident.status == status)
    if unit_id:
        stmt = stmt.where(Resident.unit_id == unit_id)
    return list(db.scalars(stmt))


def list_residents_for_select(db: Session) -> list[Resident]:
    return list(
        db.scalars(
            select(Resident)
            .options(selectinload(Resident.unit))
            .order_by(Resident.full_name)
        )
    )


def get_resident(db: Session, resident_id: uuid.UUID) -> Resident | None:
    return db.get(Resident, resident_id)


def create_resident(db: Session, data: ResidentForm) -> Resident:
    resident = Resident(**data.model_dump())
    db.add(resident)
    db.commit()
    db.refresh(resident)
    return resident


def update_resident(db: Session, resident: Resident, data: ResidentForm) -> Resident:
    for field, value in data.model_dump().items():
        setattr(resident, field, value)
    db.commit()
    db.refresh(resident)
    return resident


def delete_resident(db: Session, resident: Resident) -> None:
    pagos = db.scalar(
        select(func.count()).select_from(Payment).where(Payment.resident_id == resident.id)
    )
    if pagos:
        raise ServiceError(
            f"No se puede eliminar a {resident.full_name} porque tiene {pagos} "
            "pago(s) registrados. Elimina o reasigna esos pagos primero."
        )
    db.delete(resident)
    db.commit()


def count_active(db: Session) -> int:
    return db.scalar(
        select(func.count())
        .select_from(Resident)
        .where(Resident.status == ResidentStatus.ACTIVO)
    ) or 0
