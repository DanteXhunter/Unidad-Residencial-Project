"""Unidades habitacionales: casas y departamentos del residencial."""

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, Timestamps, UUIDPrimaryKey, enum_column
from app.models.enums import UnitStatus, UnitType

if TYPE_CHECKING:
    from app.models.incident import Incident
    from app.models.payment import Payment
    from app.models.resident import Resident


class Unit(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "units"

    # UNIQUE: no puede haber dos "A-101" en el residencial.
    unit_number: Mapped[str] = mapped_column(
        String(20), nullable=False, unique=True, index=True
    )
    type: Mapped[UnitType] = mapped_column(
        enum_column(UnitType, "unit_type"), nullable=False, default=UnitType.DEPARTAMENTO
    )
    status: Mapped[UnitStatus] = mapped_column(
        enum_column(UnitStatus, "unit_status"),
        nullable=False,
        default=UnitStatus.DISPONIBLE,
        index=True,
    )
    monthly_fee: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0.00")
    )
    notes: Mapped[str | None] = mapped_column(String(255))

    # passive_deletes="all": impide que SQLAlchemy ponga las FK hijas en NULL
    # antes del DELETE, para que el RESTRICT de la base de datos sí se dispare.
    residents: Mapped[list["Resident"]] = relationship(
        back_populates="unit", passive_deletes="all"
    )
    payments: Mapped[list["Payment"]] = relationship(
        back_populates="unit", passive_deletes="all"
    )
    incidents: Mapped[list["Incident"]] = relationship(
        back_populates="unit", passive_deletes="all"
    )

    def __repr__(self) -> str:
        return f"<Unit {self.unit_number}>"
