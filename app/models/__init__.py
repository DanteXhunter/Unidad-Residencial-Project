"""Modelos del dominio.

Se importan todos aquí para que ``Base.metadata`` quede completo cuando Alembic
autogenere migraciones.
"""

from app.models.announcement import Announcement
from app.models.base import Base
from app.models.incident import Incident
from app.models.payment import Payment
from app.models.resident import Resident
from app.models.unit import Unit
from app.models.user import User

__all__ = [
    "Announcement",
    "Base",
    "Incident",
    "Payment",
    "Resident",
    "Unit",
    "User",
]
