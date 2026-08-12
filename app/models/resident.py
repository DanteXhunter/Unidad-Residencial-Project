"""Residentes: propietarios e inquilinos asociados a una unidad."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, Timestamps, UUIDPrimaryKey, enum_column
from app.models.enums import ResidentStatus

if TYPE_CHECKING:
    from app.models.payment import Payment
    from app.models.unit import Unit


class Resident(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "residents"

    unit_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("units.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    full_name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(180))
    phone: Mapped[str | None] = mapped_column(String(30))
    is_owner: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[ResidentStatus] = mapped_column(
        enum_column(ResidentStatus, "resident_status"),
        nullable=False,
        default=ResidentStatus.ACTIVO,
        index=True,
    )

    unit: Mapped["Unit"] = relationship(back_populates="residents")
    payments: Mapped[list["Payment"]] = relationship(
        back_populates="resident", passive_deletes="all"
    )

    @property
    def display_label(self) -> str:
        """Etiqueta para los <select>: distingue homónimos por su unidad."""
        if self.unit is not None:
            return f"{self.full_name} — {self.unit.unit_number}"
        return self.full_name

    def __repr__(self) -> str:
        return f"<Resident {self.full_name}>"
