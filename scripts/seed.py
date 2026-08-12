"""Carga datos de demostración para que la app no se vea vacía en la revisión.

Uso:
    python -m scripts.seed            # crea los datos si la base está vacía
    python -m scripts.seed --reset    # borra TODO y vuelve a crearlos

Ejecuta primero las migraciones:  alembic upgrade head
"""

import argparse
import random
import sys
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import delete, func, select

from app.database import SessionLocal
from app.models import Announcement, Incident, Payment, Resident, Unit, User
from app.models.enums import (
    AnnouncementStatus,
    IncidentPriority,
    IncidentStatus,
    PaymentStatus,
    ResidentStatus,
    UnitStatus,
    UnitType,
    UserRole,
)
from app.security import hash_password

# Semilla fija: los datos generados son siempre los mismos, lo que hace que la
# demostración sea reproducible.
random.seed(2026)

DEMO_ADMIN_EMAIL = "admin@residencial.mx"
DEMO_ADMIN_PASSWORD = "Admin1234"

NOMBRES = [
    "María Fernanda López", "Carlos Alberto Ruiz", "Ana Sofía Márquez",
    "Jorge Luis Hernández", "Patricia Gómez Solís", "Ricardo Ibáñez Cruz",
    "Lucía Ramírez Ortega", "Fernando Castillo Vega", "Daniela Torres Peña",
    "Miguel Ángel Domínguez", "Verónica Salazar Ríos", "Andrés Mendoza Lara",
    "Gabriela Núñez Ávila", "Roberto Cárdenas Muñoz", "Elena Vázquez Rojas",
]

INCIDENCIAS = [
    ("Fuga de agua en cocina", "El inquilino reporta una fuga bajo el fregadero.", IncidentPriority.ALTA, IncidentStatus.EN_PROCESO),
    ("Lámpara dañada en pasillo", "La luminaria del segundo piso no enciende.", IncidentPriority.BAJA, IncidentStatus.PENDIENTE),
    ("Problema en portón eléctrico", "El portón principal no cierra por completo.", IncidentPriority.ALTA, IncidentStatus.PENDIENTE),
    ("Ruido excesivo por las noches", "Vecinos reportan ruido después de las 23:00 h.", IncidentPriority.MEDIA, IncidentStatus.RESUELTA),
    ("Filtración en estacionamiento", "Humedad en el muro norte del sótano.", IncidentPriority.MEDIA, IncidentStatus.EN_PROCESO),
    ("Bomba de agua con falla", "La bomba se detiene de forma intermitente.", IncidentPriority.ALTA, IncidentStatus.RESUELTA),
    ("Basura fuera de horario", "Se deja basura en el pasillo fuera del horario.", IncidentPriority.BAJA, IncidentStatus.RESUELTA),
    ("Cerradura de bodega forzada", "La bodega 3 presenta la cerradura dañada.", IncidentPriority.MEDIA, IncidentStatus.PENDIENTE),
]

AVISOS = [
    ("Mantenimiento de alberca", "La alberca permanecerá cerrada del 15 al 17 de este mes por mantenimiento preventivo.", AnnouncementStatus.PUBLICADO),
    ("Corte temporal de agua", "El próximo martes habrá corte de agua de 9:00 a 14:00 h por reparación de la cisterna.", AnnouncementStatus.PUBLICADO),
    ("Reunión vecinal ordinaria", "Se convoca a la asamblea del mes en el salón de usos múltiples a las 19:00 h.", AnnouncementStatus.PUBLICADO),
    ("Nuevo reglamento de estacionamiento", "A partir del próximo mes cada unidad tendrá un cajón asignado.", AnnouncementStatus.PUBLICADO),
    ("Propuesta de cambio de horario del gimnasio", "Borrador pendiente de aprobación por la mesa directiva.", AnnouncementStatus.BORRADOR),
]


def _wipe(db) -> None:
    """Borra en orden inverso a las dependencias para no violar las FK."""
    for model in (Payment, Incident, Resident, Announcement, Unit, User):
        db.execute(delete(model))
    db.commit()


def _create_users(db) -> tuple[User, User]:
    admin = User(
        full_name="Héctor Ramírez",
        email=DEMO_ADMIN_EMAIL,
        password_hash=hash_password(DEMO_ADMIN_PASSWORD),
        role=UserRole.ADMIN,
    )
    operador = User(
        full_name="Sandra Peralta",
        email="recepcion@residencial.mx",
        password_hash=hash_password("Operador1234"),
        role=UserRole.OPERADOR,
    )
    db.add_all([admin, operador])
    db.flush()
    return admin, operador


def _create_units(db) -> list[Unit]:
    units: list[Unit] = []
    plan = [
        ("A", 1, 4, UnitType.DEPARTAMENTO, Decimal("1500.00")),
        ("A", 2, 4, UnitType.DEPARTAMENTO, Decimal("1650.00")),
        ("B", 2, 4, UnitType.DEPARTAMENTO, Decimal("1650.00")),
        ("C", 1, 4, UnitType.CASA, Decimal("2100.00")),
    ]
    for torre, piso, cantidad, tipo, cuota in plan:
        for numero in range(1, cantidad + 1):
            estado = random.choices(
                [UnitStatus.OCUPADA, UnitStatus.DISPONIBLE, UnitStatus.MANTENIMIENTO],
                weights=[75, 18, 7],
            )[0]
            units.append(
                Unit(
                    unit_number=f"{torre}-{piso}{numero:02d}",
                    type=tipo,
                    status=estado,
                    monthly_fee=cuota,
                )
            )
    db.add_all(units)
    db.flush()
    return units


def _create_residents(db, units: list[Unit]) -> list[Resident]:
    ocupadas = [unit for unit in units if unit.status == UnitStatus.OCUPADA]
    residents: list[Resident] = []
    for index, nombre in enumerate(NOMBRES):
        if index >= len(ocupadas):
            break
        unit = ocupadas[index]
        primer_nombre = nombre.split()[0].lower()
        residents.append(
            Resident(
                unit=unit,
                full_name=nombre,
                email=f"{primer_nombre}{index + 1}@correo.mx",
                phone=f"55 {random.randint(1000, 9999)} {random.randint(1000, 9999)}",
                is_owner=random.random() < 0.65,
                status=ResidentStatus.ACTIVO if random.random() < 0.87 else ResidentStatus.INACTIVO,
            )
        )
    db.add_all(residents)
    db.flush()
    return residents


def _create_payments(db, residents: list[Resident]) -> list[Payment]:
    """Genera los últimos 4 meses de cuotas con una mezcla realista de estados."""
    hoy = date.today()
    payments: list[Payment] = []

    for offset in range(3, -1, -1):
        mes = hoy.month - offset
        anio = hoy.year
        while mes <= 0:
            mes += 12
            anio -= 1

        for resident in residents:
            if resident.status == ResidentStatus.INACTIVO:
                continue
            # Los meses viejos están casi todos pagados; el mes en curso no.
            if offset >= 2:
                estado = random.choices(
                    [PaymentStatus.PAGADO, PaymentStatus.VENCIDO], weights=[88, 12]
                )[0]
            elif offset == 1:
                estado = random.choices(
                    [PaymentStatus.PAGADO, PaymentStatus.VENCIDO, PaymentStatus.PENDIENTE],
                    weights=[70, 15, 15],
                )[0]
            else:
                estado = random.choices(
                    [PaymentStatus.PAGADO, PaymentStatus.PENDIENTE], weights=[45, 55]
                )[0]

            fecha_pago = None
            if estado == PaymentStatus.PAGADO:
                fecha_pago = date(anio, mes, min(random.randint(2, 15), 28))

            payments.append(
                Payment(
                    unit=resident.unit,
                    resident=resident,
                    concept="Cuota de mantenimiento",
                    amount=resident.unit.monthly_fee,
                    period_month=mes,
                    period_year=anio,
                    status=estado,
                    payment_date=fecha_pago,
                )
            )

    # Un par de cargos extraordinarios para que la tabla no se vea uniforme.
    if residents:
        payments.append(
            Payment(
                unit=residents[0].unit,
                resident=residents[0],
                concept="Cuota extraordinaria: portón",
                amount=Decimal("850.00"),
                period_month=hoy.month,
                period_year=hoy.year,
                status=PaymentStatus.PENDIENTE,
            )
        )
        payments.append(
            Payment(
                unit=residents[1].unit,
                resident=residents[1],
                concept="Multa por ruido",
                amount=Decimal("400.00"),
                period_month=hoy.month,
                period_year=hoy.year,
                status=PaymentStatus.VENCIDO,
            )
        )

    db.add_all(payments)
    db.flush()
    return payments


def _create_incidents(db, units: list[Unit]) -> None:
    incidents = []
    for index, (titulo, descripcion, prioridad, estado) in enumerate(INCIDENCIAS):
        # Una de cada cuatro se registra como área común (sin unidad).
        unit = None if index % 4 == 3 else random.choice(units)
        incidents.append(
            Incident(
                unit=unit,
                title=titulo,
                description=descripcion,
                priority=prioridad,
                status=estado,
                created_at=datetime.now(UTC) - timedelta(days=index * 3 + 1),
            )
        )
    db.add_all(incidents)


def _create_announcements(db, autor: User) -> None:
    announcements = []
    for index, (titulo, descripcion, estado) in enumerate(AVISOS):
        publicado = (
            datetime.now(UTC) - timedelta(days=index * 4 + 1)
            if estado == AnnouncementStatus.PUBLICADO
            else None
        )
        announcements.append(
            Announcement(
                title=titulo,
                description=descripcion,
                status=estado,
                published_at=publicado,
                author=autor,
                created_at=datetime.now(UTC) - timedelta(days=index * 4 + 2),
            )
        )
    db.add_all(announcements)


def main() -> int:
    parser = argparse.ArgumentParser(description="Carga datos de demostración.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Borra todos los registros existentes antes de cargar los datos.",
    )
    args = parser.parse_args()

    with SessionLocal() as db:
        existentes = db.scalar(select(func.count()).select_from(Unit)) or 0
        if existentes and not args.reset:
            print(
                f"La base ya tiene {existentes} unidades. "
                "Usa --reset si quieres borrarlas y volver a generarlas."
            )
            return 1

        if args.reset:
            print("Borrando datos existentes…")
            _wipe(db)

        admin, _ = _create_users(db)
        units = _create_units(db)
        residents = _create_residents(db, units)
        payments = _create_payments(db, residents)
        _create_incidents(db, units)
        _create_announcements(db, admin)
        db.commit()

    print("\nDatos de demostración creados:")
    print(f"  · {len(units)} unidades")
    print(f"  · {len(residents)} residentes")
    print(f"  · {len(payments)} pagos")
    print(f"  · {len(INCIDENCIAS)} incidencias")
    print(f"  · {len(AVISOS)} avisos")
    print("\nAcceso de demostración:")
    print(f"  Correo:     {DEMO_ADMIN_EMAIL}")
    print(f"  Contraseña: {DEMO_ADMIN_PASSWORD}")
    print("\nCambia esta contraseña antes de exponer la app fuera de tu equipo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
