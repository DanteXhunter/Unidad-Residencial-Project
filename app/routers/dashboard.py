"""Panel principal con métricas del residencial."""

from datetime import date

from fastapi import APIRouter, Request

from app.dependencies import CurrentUser, DbSession
from app.services import announcements as announcements_service
from app.services import dashboard as dashboard_service
from app.services import incidents as incidents_service
from app.services import payments as payments_service
from app.templating import render

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard")
def dashboard(request: Request, db: DbSession, user: CurrentUser):
    stats = dashboard_service.get_stats(db)
    year = date.today().year
    monthly = dashboard_service.monthly_collection(db, year)

    return render(
        request,
        "dashboard.html",
        {
            "stats": stats,
            "donut": dashboard_service.payments_donut(stats.payments_by_status),
            "monthly": monthly,
            "monthly_max": max((row["total"] for row in monthly), default=0) or 1,
            "recent_payments": payments_service.recent_payments(db),
            "recent_incidents": incidents_service.recent_incidents(db),
            "recent_announcements": announcements_service.recent_announcements(db),
            "chart_year": year,
        },
        user=user,
    )
