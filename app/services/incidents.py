"""Reglas de negocio de incidencias."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Incident
from app.models.enums import IncidentStatus
from app.schemas import IncidentForm


def list_incidents(
    db: Session, *, priority: str | None = None, status: str | None = None
) -> list[Incident]:
    stmt = (
        select(Incident)
        .options(selectinload(Incident.unit))
        .order_by(Incident.created_at.desc())
    )
    if priority:
        stmt = stmt.where(Incident.priority == priority)
    if status:
        stmt = stmt.where(Incident.status == status)
    return list(db.scalars(stmt))


def get_incident(db: Session, incident_id: uuid.UUID) -> Incident | None:
    return db.get(Incident, incident_id)


def create_incident(db: Session, data: IncidentForm) -> Incident:
    incident = Incident(**data.model_dump())
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident


def update_incident(db: Session, incident: Incident, data: IncidentForm) -> Incident:
    for field, value in data.model_dump().items():
        setattr(incident, field, value)
    db.commit()
    db.refresh(incident)
    return incident


def change_status(db: Session, incident: Incident, status: IncidentStatus) -> Incident:
    """Cambio rápido de estado desde la tabla, sin abrir el formulario."""
    incident.status = status
    db.commit()
    db.refresh(incident)
    return incident


def delete_incident(db: Session, incident: Incident) -> None:
    db.delete(incident)
    db.commit()


def count_open(db: Session) -> int:
    return db.scalar(
        select(func.count())
        .select_from(Incident)
        .where(Incident.status != IncidentStatus.RESUELTA)
    ) or 0


def count_by_status(db: Session) -> dict[str, int]:
    rows = db.execute(select(Incident.status, func.count()).group_by(Incident.status)).all()
    counts = {status.value: 0 for status in IncidentStatus}
    for status, total in rows:
        key = status.value if hasattr(status, "value") else str(status)
        counts[key] = total
    return counts


def recent_incidents(db: Session, limit: int = 5) -> list[Incident]:
    return list(
        db.scalars(
            select(Incident)
            .options(selectinload(Incident.unit))
            .order_by(Incident.created_at.desc())
            .limit(limit)
        )
    )
