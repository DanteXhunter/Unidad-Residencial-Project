"""Clase base declarativa, convención de nombres y mixins compartidos."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, MetaData, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Nombres deterministas para índices y constraints: sin esto Alembic genera
# migraciones con nombres automáticos que cambian entre ejecuciones.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Base declarativa de SQLAlchemy 2.0."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class UUIDPrimaryKey:
    """Llave primaria UUID generada en Python (portable entre motores)."""

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)


class Timestamps:
    """Marcas de tiempo. ``updated_at`` se refresca en cada UPDATE."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


def enum_column(enum_cls: type, name: str, length: int = 24) -> Enum:
    """Columna de catálogo: VARCHAR + CHECK en lugar de un tipo ENUM nativo.

    Los ENUM nativos de Postgres requieren ``ALTER TYPE`` para agregar valores,
    lo que complica las migraciones sin dar ninguna ventaja aquí.
    """
    return Enum(
        enum_cls,
        native_enum=False,
        length=length,
        create_constraint=True,
        name=name,
        values_callable=lambda cls: [member.value for member in cls],
    )
