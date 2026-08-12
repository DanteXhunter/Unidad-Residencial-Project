"""Reglas de negocio de usuarios administrativos y autenticación."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import User
from app.models.enums import UserRole
from app.schemas import UserCreateForm, UserUpdateForm
from app.security import hash_password, needs_rehash, verify_password
from app.services.errors import ServiceError


def list_users(db: Session, *, search: str | None = None) -> list[User]:
    stmt = select(User).order_by(User.full_name)
    if search:
        stmt = stmt.where(
            User.full_name.ilike(f"%{search}%") | User.email.ilike(f"%{search}%")
        )
    return list(db.scalars(stmt))


def get_user(db: Session, user_id: uuid.UUID) -> User | None:
    return db.get(User, user_id)


def get_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(func.lower(User.email) == email.lower()))


def authenticate(db: Session, email: str, password: str) -> User | None:
    """Verifica credenciales.

    Devuelve None ante cualquier fallo (correo inexistente, contraseña
    incorrecta o cuenta desactivada) para no revelar cuáles correos existen.
    """
    user = get_by_email(db, email)
    if user is None:
        # Se calcula un hash de todas formas para que el tiempo de respuesta no
        # delate si el correo está registrado (mitiga enumeración por timing).
        hash_password(password)
        return None
    if not verify_password(password, user.password_hash):
        return None
    if not user.is_active:
        return None

    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(password)
        db.commit()
    return user


def _assert_unique_email(
    db: Session, email: str, *, exclude_id: uuid.UUID | None = None
) -> None:
    stmt = select(User.id).where(func.lower(User.email) == email.lower())
    if exclude_id is not None:
        stmt = stmt.where(User.id != exclude_id)
    if db.scalar(stmt) is not None:
        raise ServiceError("Ya existe un usuario con ese correo.", field="email")


def create_user(db: Session, data: UserCreateForm) -> User:
    _assert_unique_email(db, data.email)
    payload = data.model_dump(exclude={"password"})
    user = User(**payload, password_hash=hash_password(data.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user: User, data: UserUpdateForm, *, current_user: User) -> User:
    _assert_unique_email(db, data.email, exclude_id=user.id)

    if user.id == current_user.id and not data.is_active:
        raise ServiceError("No puedes desactivar tu propia cuenta.", field="is_active")

    payload = data.model_dump(exclude={"password"})
    for field, value in payload.items():
        setattr(user, field, value)
    if data.password:
        user.password_hash = hash_password(data.password)

    _assert_admin_remains(db, user)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user: User, *, current_user: User) -> None:
    if user.id == current_user.id:
        raise ServiceError("No puedes eliminar tu propia cuenta.")

    other_admins = db.scalar(
        select(func.count())
        .select_from(User)
        .where(User.id != user.id, User.role == UserRole.ADMIN, User.is_active.is_(True))
    )
    if not other_admins:
        raise ServiceError(
            "No se puede eliminar: quedaría el sistema sin ningún administrador activo."
        )

    # Los avisos que escribió se conservan (la FK está en SET NULL).
    db.delete(user)
    db.commit()


def _assert_admin_remains(db: Session, edited_user: User) -> None:
    """Impide dejar el sistema sin administradores activos."""
    remaining = db.scalar(
        select(func.count())
        .select_from(User)
        .where(User.id != edited_user.id, User.role == UserRole.ADMIN, User.is_active.is_(True))
    )
    edited_counts = edited_user.role == UserRole.ADMIN and edited_user.is_active
    if not remaining and not edited_counts:
        db.rollback()
        raise ServiceError(
            "Debe quedar al menos un administrador activo en el sistema.", field="role"
        )


def count_users(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(User)) or 0
