"""Configuración de Jinja2: filtros y variables globales de las plantillas."""

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from fastapi.templating import Jinja2Templates

from app.config import settings
from app.models import enums

TEMPLATES_DIR = Path(__file__).parent / "templates"
STATIC_DIR = Path(__file__).parent / "static"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

_MESES_CORTOS = [
    "ene", "feb", "mar", "abr", "may", "jun",
    "jul", "ago", "sep", "oct", "nov", "dic",
]


def money(value: Decimal | float | int | None) -> str:
    """Formato de moneda mexicana: 1500 -> $1,500.00"""
    if value is None:
        return "—"
    return f"${Decimal(value):,.2f}"


def short_date(value: date | datetime | None) -> str:
    """11 ago 2026"""
    if value is None:
        return "—"
    return f"{value.day} {_MESES_CORTOS[value.month - 1]} {value.year}"


def long_datetime(value: datetime | None) -> str:
    """11 ago 2026, 18:04"""
    if value is None:
        return "—"
    return f"{short_date(value)}, {value:%H:%M}"


def initials(name: str | None) -> str:
    if not name:
        return "?"
    parts = [p for p in name.split() if p]
    return "".join(p[0].upper() for p in parts[:2]) or "?"


templates.env.filters["money"] = money
templates.env.filters["short_date"] = short_date
templates.env.filters["long_datetime"] = long_datetime
templates.env.filters["initials"] = initials

_DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
_MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


def today_label() -> str:
    """martes, 11 de agosto de 2026"""
    hoy = date.today()
    return f"{_DIAS[hoy.weekday()]}, {hoy.day} de {_MESES[hoy.month - 1]} de {hoy.year}"


def render(
    request,
    template_name: str,
    context: dict | None = None,
    *,
    user=None,
    status_code: int = 200,
):
    """Renderiza una plantilla con el contexto común a todas las pantallas.

    Consume los mensajes flash pendientes, así que debe llamarse una sola vez
    por respuesta.
    """
    from app.flash import get_flashes  # import local: evita una dependencia circular

    full_context = {
        "current_user": user,
        "flashes": get_flashes(request),
        "today_label": today_label(),
        **(context or {}),
    }
    return templates.TemplateResponse(
        request, template_name, full_context, status_code=status_code
    )


def enum_options(enum_cls: type) -> list[tuple[str, str]]:
    """Opciones (valor, etiqueta) para los <select> a partir de un enum."""
    return [(member.value, member.value) for member in enum_cls]


def options_from(items, value_attr: str, label_attr: str) -> list[tuple[str, str]]:
    """Opciones (valor, etiqueta) para los <select> a partir de registros."""
    return [(str(getattr(item, value_attr)), str(getattr(item, label_attr))) for item in items]


templates.env.globals.update(
    enum_options=enum_options,
    options_from=options_from,
    app_name=settings.app_name,
    MONTHS=enums.MONTHS,
    UnitType=enums.UnitType,
    UnitStatus=enums.UnitStatus,
    ResidentStatus=enums.ResidentStatus,
    PaymentStatus=enums.PaymentStatus,
    IncidentPriority=enums.IncidentPriority,
    IncidentStatus=enums.IncidentStatus,
    AnnouncementStatus=enums.AnnouncementStatus,
    UserRole=enums.UserRole,
)
