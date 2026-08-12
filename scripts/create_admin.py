"""Crea un usuario administrador desde la terminal.

Uso interactivo (la contraseña no se ve al escribirla):
    python -m scripts.create_admin

Uso no interactivo:
    python -m scripts.create_admin --email admin@ejemplo.mx --name "Ada Lovelace"
"""

import argparse
import getpass
import sys

from app.database import SessionLocal
from app.models import User
from app.models.enums import UserRole
from app.security import hash_password
from app.services import users as users_service


def main() -> int:
    parser = argparse.ArgumentParser(description="Crea un usuario administrador.")
    parser.add_argument("--email", help="Correo de la cuenta.")
    parser.add_argument("--name", help="Nombre completo.")
    args = parser.parse_args()

    email = (args.email or input("Correo: ")).strip()
    full_name = (args.name or input("Nombre completo: ")).strip()

    password = getpass.getpass("Contraseña (mínimo 8 caracteres): ")
    if len(password) < 8:
        print("Error: la contraseña debe tener al menos 8 caracteres.")
        return 1
    if password != getpass.getpass("Confirma la contraseña: "):
        print("Error: las contraseñas no coinciden.")
        return 1

    with SessionLocal() as db:
        if users_service.get_by_email(db, email):
            print(f"Error: ya existe un usuario con el correo {email}.")
            return 1

        db.add(
            User(
                full_name=full_name,
                email=email,
                password_hash=hash_password(password),
                role=UserRole.ADMIN,
            )
        )
        db.commit()

    print(f"Administrador {email} creado correctamente.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
