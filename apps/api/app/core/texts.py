"""Diccionario de textos de la API (por ahora, los emails).

Textos del núcleo en es-AR, neutros: sirven para cualquier tienda. Cada cliente puede
pisar claves en ``config/texts.json``, el mismo archivo de reemplazos que usa la web; cada
lado toma solo las claves que conoce.
"""

import json
import re
from pathlib import Path

CORE_TEXTS: dict[str, str] = {
    "email.passwordReset.subject": "Recuperá tu contraseña del panel de {store}",
    "email.passwordReset.body": (
        "Hola:\n\n"
        "Pediste recuperar la contraseña del panel de {store}. Para elegir una nueva, "
        "entrá a este link:\n\n"
        "{link}\n\n"
        "El link vence en 30 minutos y sirve una sola vez.\n\n"
        "Si no lo pediste, ignorá este email: tu contraseña sigue igual."
    ),
    "email.invitation.subject": "Tu cuenta del panel de {store}",
    "email.invitation.body": (
        "Hola:\n\n"
        "Ya tenés cuenta en el panel de {store}. Para entrar, elegí tu contraseña en "
        "este link:\n\n"
        "{link}\n\n"
        "El link vence en 7 días y sirve una sola vez."
    ),
    "email.passwordChanged.subject": "Cambió tu contraseña del panel de {store}",
    "email.passwordChanged.body": (
        "Hola:\n\n"
        "La contraseña del panel de {store} acaba de cambiar y se cerraron las demás "
        "sesiones.\n\n"
        "Si no fuiste vos, pedí un link para recuperarla desde «Olvidé mi contraseña»:\n\n"
        "{link}"
    ),
}

_VARIABLE = re.compile(r"\{(\w+)\}")


class Texts:
    """``t(clave, **variables)``: el texto del núcleo o su reemplazo, con las variables
    puestas. Una variable que no se pasa queda tal cual."""

    def __init__(self, overrides: object = None) -> None:
        valid = (
            {
                key: value
                for key, value in overrides.items()
                if key in CORE_TEXTS and isinstance(value, str)
            }
            if isinstance(overrides, dict)
            else {}
        )
        self._texts = CORE_TEXTS | valid

    @classmethod
    def from_file(cls, path: Path) -> "Texts":
        """Los reemplazos del cliente, si el archivo existe (es opcional)."""
        if not path.exists():
            return cls()
        return cls(json.loads(path.read_text(encoding="utf-8")))

    def __call__(self, key: str, **variables: str) -> str:
        return _VARIABLE.sub(
            lambda match: variables.get(match.group(1), match.group(0)), self._texts[key]
        )
