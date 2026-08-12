"""Errores de negocio con mensajes pensados para mostrarse al usuario."""


class ServiceError(Exception):
    """Operación rechazada por una regla de negocio.

    El mensaje se muestra tal cual en la interfaz, así que debe ser claro y
    estar en español. Si ``field`` viene informado, el router lo pinta como
    error de ese campo del formulario en lugar de como alerta general.
    """

    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.field = field

    def as_form_errors(self) -> dict[str, str]:
        return {self.field or "__general__": self.message}
