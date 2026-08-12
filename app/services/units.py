"""Reglas de negocio de unidades habitacionales."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Incident, Payment, Resident, Unit
from app.models.enums import UnitStatus
from app.schemas import UnitForm
from app.services.errors import ServiceError


def list_units(
    db: Session, *, search: str | None = None, status: str | None = None
) -> list[Unit]:
    # selectinload evita una consulta por fila al contar residentes en la tabla.
    stmt = (
        select(Unit).options(selectinload(Unit.residents)).order_by(Unit.unit_number)
    )
    if search:
        stmt = stmt.where(Unit.unit_number.ilike(f"%{search}%"))
    if status:
        stmt = stmt.where(Unit.status == status)
    return list(db.scalars(stmt))


def list_units_for_select(db: Session) -> list[Unit]:
    """Unidades ordenadas para alimentar los <select> de otros formularios."""
    return list(db.scalars(select(Unit).order_by(Unit.unit_number)))


def get_unit(db: Session, unit_id: uuid.UUID) -> Unit | None:
    return db.get(Unit, unit_id)


def _assert_unique_number(
    db: Session, unit_number: str, *, exclude_id: uuid.UUID | None = None
) -> None:
    stmt = select(Unit.id).where(func.lower(Unit.unit_number) == unit_number.lower())
    if exclude_id is not None:
        stmt = stmt.where(Unit.id != exclude_id)
    if db.scalar(stmt) is not None:
        raise ServiceError(
            f"Ya existe una unidad con el número {unit_number}.", field="unit_number"
        )


def create_unit(db: Session, data: UnitForm) -> Unit:
    _assert_unique_number(db, data.unit_number)
    unit = Unit(**data.model_dump())
    db.add(unit)
    db.commit()
    db.refresh(unit)
    return unit


def update_unit(db: Session, unit: Unit, data: UnitForm) -> Unit:
    _assert_unique_number(db, data.unit_number, exclude_id=unit.id)
    for field, value in data.model_dump().items():
        setattr(unit, field, value)
    db.commit()
    db.refresh(unit)
    return unit


def delete_unit(db: Session, unit: Unit) -> None:
    """Elimina la unidad solo si no tiene información relacionada.

    Las FK están en RESTRICT, así que la base de datos rechazaría el DELETE de
    todas formas; comprobarlo antes permite dar un mensaje concreto en vez de
    un error de integridad.
    """
    related = {
        "residentes": db.scalar(
            select(func.count()).select_from(Resident).where(Resident.unit_id == unit.id)
        ),
        "pagos": db.scalar(
            select(func.count()).select_from(Payment).where(Payment.unit_id == unit.id)
        ),
        "incidencias": db.scalar(
            select(func.count()).select_from(Incident).where(Incident.unit_id == unit.id)
        ),
    }
    bloqueos = [f"{count} {name}" for name, count in related.items() if count]
    if bloqueos:
        raise ServiceError(
            f"No se puede eliminar la unidad {unit.unit_number} porque tiene "
            f"{', '.join(bloqueos)} asociados. Elimina o reasigna esos registros primero."
        )

    db.delete(unit)
    db.commit()


def count_by_status(db: Session) -> dict[str, int]:
    rows = db.execute(
        select(Unit.status, func.count()).group_by(Unit.status)
    ).all()
    counts = {status.value: 0 for status in UnitStatus}
    for status, total in rows:
        counts[status.value if hasattr(status, "value") else str(status)] = total
    return counts
