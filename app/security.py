"""Hash y verificación de contraseñas.

Se usa Argon2id (ganador del Password Hashing Competition y recomendación
actual de OWASP). Las contraseñas nunca se guardan en texto plano.
"""

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

_hasher = PasswordHasher()


def hash_password(plain_password: str) -> str:
    return _hasher.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Devuelve True si la contraseña coincide. Nunca lanza excepción."""
    try:
        return _hasher.verify(password_hash, plain_password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def needs_rehash(password_hash: str) -> bool:
    """True si el hash usa parámetros viejos y conviene regenerarlo."""
    try:
        return _hasher.check_needs_rehash(password_hash)
    except InvalidHashError:
        return True
