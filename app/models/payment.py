"""Pagos y cuotas de mantenimiento."""

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, Timestamps, UUIDPrimaryKey, enum_column
from app.models.enums import MONTHS, PaymentStatus

if TYPE_CHECKING:
    from app.models.resident import Resident
    from app.models.unit import Unit


class Payment(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "payments"
    __table_args__ = (
        # El mes se guarda como entero (no texto) para poder filtrar y ordenar
        # cronológicamente; la etiqueta en español se resuelve en la propiedad.
        CheckConstraint("period_month BETWEEN 1 AND 12", name="period_month_range"),
        CheckConstraint("amount >= 0", name="amount_non_negative"),
    )

    unit_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("units.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    resident_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("residents.id", ondelete="RESTRICT"), index=True
    )
    concept: Mapped[str] = mapped_column(String(120), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    period_month: Mapped[int] = mapped_column(Integer, nullable=False)
    period_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    status: Mapped[PaymentStatus] = mapped_column(
        enum_column(PaymentStatus, "payment_status"),
        nullable=False,
        default=PaymentStatus.PENDIENTE,
        index=True,
    )
    payment_date: Mapped[date | None] = mapped_column(Date)

    unit: Mapped["Unit"] = relationship(back_populates="payments")
    resident: Mapped["Resident | None"] = relationship(back_populates="payments")

    @property
    def period_label(self) -> str:
        return f"{MONTHS.get(self.period_month, '—')} {self.period_year}"

    def __repr__(self) -> str:
        return f"<Payment {self.concept} {self.period_label}>"
