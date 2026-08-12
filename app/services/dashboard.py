"""Métricas del panel. Todos los números salen de consultas reales."""

from dataclasses import dataclass, field

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Announcement, Incident, Payment, Resident, Unit
from app.models.enums import IncidentStatus, PaymentStatus, ResidentStatus, UnitStatus
from app.services import incidents as incidents_service
from app.services import payments as payments_service


@dataclass
class DashboardStats:
    total_units: int = 0
    occupied_units: int = 0
    available_units: int = 0
    active_residents: int = 0
    pending_payments: int = 0
    open_incidents: int = 0
    published_announcements: int = 0
    collected_amount: float = 0.0
    outstanding_amount: float = 0.0
    payments_by_status: dict[str, int] = field(default_factory=dict)
    incidents_by_status: dict[str, int] = field(default_factory=dict)

    @property
    def occupancy_rate(self) -> float:
        if not self.total_units:
            return 0.0
        return round(self.occupied_units / self.total_units * 100, 1)


def _count(db: Session, model, *conditions) -> int:
    stmt = select(func.count()).select_from(model)
    if conditions:
        stmt = stmt.where(*conditions)
    return db.scalar(stmt) or 0


def get_stats(db: Session) -> DashboardStats:
    return DashboardStats(
        total_units=_count(db, Unit),
        occupied_units=_count(db, Unit, Unit.status == UnitStatus.OCUPADA),
        available_units=_count(db, Unit, Unit.status == UnitStatus.DISPONIBLE),
        active_residents=_count(db, Resident, Resident.status == ResidentStatus.ACTIVO),
        pending_payments=_count(
            db,
            Payment,
            Payment.status.in_([PaymentStatus.PENDIENTE, PaymentStatus.VENCIDO]),
        ),
        open_incidents=_count(db, Incident, Incident.status != IncidentStatus.RESUELTA),
        published_announcements=_count(
            db, Announcement, Announcement.status == "Publicado"
        ),
        collected_amount=payments_service.total_collected(db),
        outstanding_amount=payments_service.outstanding_amount(db),
        payments_by_status=payments_service.count_by_status(db),
        incidents_by_status=incidents_service.count_by_status(db),
    )


# Colores de la dona de pagos. Verde/ámbar/rojo son convenciones de estado, no
# decoración: se acompañan siempre de la etiqueta escrita para no depender del color.
_DONUT_COLORS = {
    "Pagado": "#059669",
    "Pendiente": "#d97706",
    "Vencido": "#e11d48",
}


def payments_donut(counts: dict[str, int]) -> list[dict]:
    """Segmentos de la gráfica de dona, ya calculados para dibujarlos en SVG.

    El radio 15.9155 hace que la circunferencia mida ~100, así el
    ``stroke-dasharray`` se puede expresar directamente en porcentaje.
    """
    total = sum(counts.values())
    segments: list[dict] = []
    cumulative = 0.0
    for label, value in counts.items():
        percent = (value / total * 100) if total else 0.0
        segments.append(
            {
                "label": label,
                "value": value,
                "percent": round(percent, 1),
                "dash": round(percent, 3),
                "gap": round(100 - percent, 3),
                "offset": round(-cumulative, 3),
                "color": _DONUT_COLORS.get(label, "#94a3b8"),
            }
        )
        cumulative += percent
    return segments


def monthly_collection(db: Session, year: int, months: int = 6) -> list[dict]:
    """Monto cobrado por mes del año indicado, para la gráfica de barras."""
    rows = db.execute(
        select(
            Payment.period_month,
            func.coalesce(func.sum(Payment.amount), 0),
        )
        .where(Payment.period_year == year, Payment.status == PaymentStatus.PAGADO)
        .group_by(Payment.period_month)
        .order_by(Payment.period_month)
    ).all()
    totals = {month: float(amount) for month, amount in rows}

    latest = max(totals) if totals else 12
    start = max(1, latest - months + 1)
    return [
        {"month": month, "total": totals.get(month, 0.0)}
        for month in range(start, latest + 1)
    ]
