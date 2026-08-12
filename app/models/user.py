"""Usuarios administrativos que pueden iniciar sesión en el panel."""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, Timestamps, UUIDPrimaryKey, enum_column
from app.models.enums import UserRole

if TYPE_CHECKING:
    from app.models.announcement import Announcement


class User(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "users"

    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(180), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        enum_column(UserRole, "user_role"), nullable=False, default=UserRole.ADMIN
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    announcements: Mapped[list["Announcement"]] = relationship(
        back_populates="author", passive_deletes=True
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"
