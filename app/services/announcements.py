"""Reglas de negocio de avisos."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Announcement, User
from app.models.enums import AnnouncementStatus
from app.schemas import AnnouncementForm


def list_announcements(db: Session, *, status: str | None = None) -> list[Announcement]:
    stmt = (
        select(Announcement)
        .options(selectinload(Announcement.author))
        .order_by(Announcement.created_at.desc())
    )
    if status:
        stmt = stmt.where(Announcement.status == status)
    return list(db.scalars(stmt))


def get_announcement(db: Session, announcement_id: uuid.UUID) -> Announcement | None:
    return db.get(Announcement, announcement_id)


def _sync_published_at(announcement: Announcement) -> None:
    """Al publicar se sella la fecha; al volver a borrador se limpia."""
    if announcement.status == AnnouncementStatus.PUBLICADO:
        if announcement.published_at is None:
            announcement.published_at = datetime.now(UTC)
    else:
        announcement.published_at = None


def create_announcement(db: Session, data: AnnouncementForm, author: User) -> Announcement:
    announcement = Announcement(**data.model_dump(), author_id=author.id)
    _sync_published_at(announcement)
    db.add(announcement)
    db.commit()
    db.refresh(announcement)
    return announcement


def update_announcement(
    db: Session, announcement: Announcement, data: AnnouncementForm
) -> Announcement:
    for field, value in data.model_dump().items():
        setattr(announcement, field, value)
    _sync_published_at(announcement)
    db.commit()
    db.refresh(announcement)
    return announcement


def delete_announcement(db: Session, announcement: Announcement) -> None:
    db.delete(announcement)
    db.commit()


def count_published(db: Session) -> int:
    return db.scalar(
        select(func.count())
        .select_from(Announcement)
        .where(Announcement.status == AnnouncementStatus.PUBLICADO)
    ) or 0


def recent_announcements(db: Session, limit: int = 4) -> list[Announcement]:
    return list(
        db.scalars(
            select(Announcement)
            .where(Announcement.status == AnnouncementStatus.PUBLICADO)
            .order_by(Announcement.published_at.desc())
            .limit(limit)
        )
    )
