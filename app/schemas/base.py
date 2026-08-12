"""Validación de formularios con Pydantic y traducción de errores al español."""

from typing import TypeVar

from pydantic import BaseModel, ValidationError

TModel = TypeVar("TModel", bound=BaseModel)

# Pydantic emite sus mensajes en inglés; aquí se traducen los tipos de error
# que realmente pueden ocurrir en estos formularios.
_ERROR_MESSAGES = {
    "missing": "Este campo es obligatorio.",
    "string_too_short": "Este campo es obligatorio.",
    "string_too_long": "El texto es demasiado largo.",
    "decimal_parsing": "Ingresa un monto válido.",
    "int_parsing": "Ingresa un número entero válido.",
    "float_parsing": "Ingresa un número válido.",
    "date_from_datetime_parsing": "Ingresa una fecha válida.",
    "date_parsing": "Ingresa una fecha válida.",
    "enum": "Selecciona una opción válida.",
    "greater_than_equal": "El valor no puede ser negativo.",
    "value_error": "Valor no válido.",
}


class FormModel(BaseModel):
    """Base de los formularios: normaliza cadenas vacías a None."""

    model_config = {"str_strip_whitespace": True, "use_enum_values": False}


def parse_form(
    model: type[TModel], raw: dict[str, str]
) -> tuple[TModel | None, dict[str, str]]:
    """Valida los datos crudos del formulario.

    Devuelve ``(instancia, {})`` si todo es válido, o ``(None, errores)`` donde
    ``errores`` mapea nombre de campo -> mensaje en español listo para mostrar.
    """
    cleaned = {key: value for key, value in raw.items() if value != ""}
    try:
        return model.model_validate(cleaned), {}
    except ValidationError as exc:
        errors: dict[str, str] = {}
        for error in exc.errors():
            field = str(error["loc"][0]) if error["loc"] else "__general__"
            errors.setdefault(
                field, _ERROR_MESSAGES.get(error["type"], error.get("msg", "Dato inválido."))
            )
        return None, errors
