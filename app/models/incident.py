"""Incidencias reportadas en unidades o en áreas comunes."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, Timestamps, UUIDPrimaryKey, enum_column
from app.models.enums import IncidentPriority, IncidentStatus

if TYPE_CHECKING:
    from app.models.unit import Unit


class Incident(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "incidents"

    # Opcional: una incidencia puede ser de un área común (sin unidad).
    unit_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("units.id", ondelete="RESTRICT"), index=True
    )
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    priority: Mapped[IncidentPriority] = mapped_column(
        enum_column(IncidentPriority, "incident_priority"),
        nullable=False,
        default=IncidentPriority.MEDIA,
        index=True,
    )
    status: Mapped[IncidentStatus] = mapped_column(
        enum_column(IncidentStatus, "incident_status"),
        nullable=False,
        default=IncidentStatus.PENDIENTE,
        index=True,
    )

    unit: Mapped["Unit | None"] = relationship(back_populates="incidents")

    def __repr__(self) -> str:
        return f"<Incident {self.title}>"
