"""Catálogos de estados del dominio.

Se guardan como texto legible en español para que la base de datos sea fácil de
inspeccionar y los reportes no necesiten traducción.
"""

import enum


class LabeledEnum(enum.StrEnum):
    """Enum de texto con utilidades para poblar los <select> de los formularios.

    Hereda de ``StrEnum`` (no de ``str, Enum``) para que ``str(miembro)``
    devuelva la etiqueta y no ``"UnitStatus.OCUPADA"``: así las plantillas
    Jinja pueden imprimir el valor directamente.
    """

    @classmethod
    def values(cls) -> list[str]:
        return [member.value for member in cls]


class UserRole(LabeledEnum):
    ADMIN = "Administrador"
    OPERADOR = "Operador"


class UnitType(LabeledEnum):
    CASA = "Casa"
    DEPARTAMENTO = "Departamento"


class UnitStatus(LabeledEnum):
    OCUPADA = "Ocupada"
    DISPONIBLE = "Disponible"
    MANTENIMIENTO = "Mantenimiento"


class ResidentStatus(LabeledEnum):
    ACTIVO = "Activo"
    INACTIVO = "Inactivo"


class PaymentStatus(LabeledEnum):
    PENDIENTE = "Pendiente"
    PAGADO = "Pagado"
    VENCIDO = "Vencido"


class IncidentPriority(LabeledEnum):
    BAJA = "Baja"
    MEDIA = "Media"
    ALTA = "Alta"


class IncidentStatus(LabeledEnum):
    PENDIENTE = "Pendiente"
    EN_PROCESO = "En proceso"
    RESUELTA = "Resuelta"


class AnnouncementStatus(LabeledEnum):
    BORRADOR = "Borrador"
    PUBLICADO = "Publicado"


MONTHS: dict[int, str] = {
    1: "Enero",
    2: "Febrero",
    3: "Marzo",
    4: "Abril",
    5: "Mayo",
    6: "Junio",
    7: "Julio",
    8: "Agosto",
    9: "Septiembre",
    10: "Octubre",
    11: "Noviembre",
    12: "Diciembre",
}
