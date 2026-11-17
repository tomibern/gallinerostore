"""Límite de frecuencia de los eventos por IP (slowapi), para que el spam no infle las
métricas. La IP solo se usa como clave del contador en memoria: no se guarda."""

from slowapi import Limiter

from app.core.client_ip import client_ip

# Generoso: muchos celulares pueden salir por la misma IP pública. Solo frena el spam.
EVENTS_RATE_LIMIT = "120/minute"


# Todo explícito: slowapi también lee variables RATELIMIT_* del entorno y un .env del
# directorio de trabajo. Los contadores viven en el proceso (un solo worker).
# Cuenta después de validar el cuerpo: un cuerpo inválido (422 de validación) no usa
# cupo, pero tampoco guarda nada. Un producto o talle inexistente (también 422) sí lo usa.
limiter = Limiter(
    key_func=client_ip,
    storage_uri="memory://",
    strategy="fixed-window",
    headers_enabled=False,
)
