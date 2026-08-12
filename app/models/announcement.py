"""Avisos publicados por la administración."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, Timestamps, UUIDPrimaryKey, enum_column
from app.models.enums import AnnouncementStatus

if TYPE_CHECKING:
    from app.models.user import User


class Announcement(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "announcements"

    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[AnnouncementStatus] = mapped_column(
        enum_column(AnnouncementStatus, "announcement_status"),
        nullable=False,
        default=AnnouncementStatus.BORRADOR,
        index=True,
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Si se elimina el usuario autor, el aviso se conserva sin autor.
    author_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), index=True
    )

    author: Mapped["User | None"] = relationship(back_populates="announcements")

    def __repr__(self) -> str:
        return f"<Announcement {self.title}>"
