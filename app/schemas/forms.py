"""Modelos de validación de cada formulario del panel."""

import uuid
from datetime import date
from decimal import Decimal

from pydantic import Field, field_validator

from app.models.enums import (
    AnnouncementStatus,
    IncidentPriority,
    IncidentStatus,
    PaymentStatus,
    ResidentStatus,
    UnitStatus,
    UnitType,
    UserRole,
)
from app.schemas.base import FormModel


def _checkbox(value: object) -> bool:
    """Un checkbox HTML no envía nada cuando está desmarcado."""
    return str(value).lower() in {"on", "true", "1", "yes"}


class LoginForm(FormModel):
    email: str = Field(min_length=1, max_length=180)
    password: str = Field(min_length=1)


class UnitForm(FormModel):
    unit_number: str = Field(min_length=1, max_length=20)
    type: UnitType
    status: UnitStatus
    monthly_fee: Decimal = Field(ge=0, default=Decimal("0.00"))
    notes: str | None = Field(default=None, max_length=255)


class ResidentForm(FormModel):
    unit_id: uuid.UUID
    full_name: str = Field(min_length=1, max_length=120)
    email: str | None = Field(default=None, max_length=180)
    phone: str | None = Field(default=None, max_length=30)
    is_owner: bool = False
    status: ResidentStatus = ResidentStatus.ACTIVO

    @field_validator("is_owner", mode="before")
    @classmethod
    def _parse_checkbox(cls, value: object) -> bool:
        return _checkbox(value)


class PaymentForm(FormModel):
    unit_id: uuid.UUID
    resident_id: uuid.UUID | None = None
    concept: str = Field(min_length=1, max_length=120)
    amount: Decimal = Field(ge=0)
    period_month: int = Field(ge=1, le=12)
    period_year: int = Field(ge=2000, le=2100)
    status: PaymentStatus = PaymentStatus.PENDIENTE
    payment_date: date | None = None


class IncidentForm(FormModel):
    unit_id: uuid.UUID | None = None
    title: str = Field(min_length=1, max_length=160)
    description: str | None = None
    priority: IncidentPriority = IncidentPriority.MEDIA
    status: IncidentStatus = IncidentStatus.PENDIENTE


class AnnouncementForm(FormModel):
    title: str = Field(min_length=1, max_length=160)
    description: str | None = None
    status: AnnouncementStatus = AnnouncementStatus.BORRADOR


class UserCreateForm(FormModel):
    full_name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=180)
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.ADMIN
    is_active: bool = True

    @field_validator("is_active", mode="before")
    @classmethod
    def _parse_checkbox(cls, value: object) -> bool:
        return _checkbox(value)


class UserUpdateForm(FormModel):
    full_name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=180)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    role: UserRole = UserRole.ADMIN
    is_active: bool = False

    @field_validator("is_active", mode="before")
    @classmethod
    def _parse_checkbox(cls, value: object) -> bool:
        return _checkbox(value)
