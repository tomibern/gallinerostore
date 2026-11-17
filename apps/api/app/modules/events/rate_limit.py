"""Límite de frecuencia de los eventos por IP (slowapi), para que el spam no infle las
métricas. La IP solo se usa como clave del contador en memoria: no se guarda."""

import ipaddress
from contextlib import suppress

from fastapi import Request
from slowapi import Limiter

from app.core.config import get_settings

# Generoso: muchos celulares pueden salir por la misma IP pública. Solo frena el spam.
EVENTS_RATE_LIMIT = "120/minute"


def _bucket(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> str:
    """Una IPv4 cuenta sola; una IPv6, con todo su /64 (el cliente rota dentro de él)."""
    if isinstance(ip, ipaddress.IPv6Address):
        return str(ipaddress.ip_network(f"{ip}/64", strict=False))
    return str(ip)


def client_ip(request: Request) -> str:
    """La IP del visitante: la entrada de X-Forwarded-For que agregó el proxy de
    confianza número N contando desde la derecha (N = ``trusted_proxy_hops``). Lo de la
    izquierda lo escribe quien quiera. Sin esa entrada (o si no es una IP), la dirección
    de la conexión."""
    hops = get_settings(request).trusted_proxy_hops
    if hops:
        chain = [
            part.strip()
            for value in request.headers.getlist("x-forwarded-for")
            for part in value.split(",")
            if part.strip()
        ]
        if len(chain) >= hops:
            with suppress(ValueError):
                return _bucket(ipaddress.ip_address(chain[-hops]))
    return request.client.host if request.client else "unknown"


# Todo explícito: slowapi también lee variables RATELIMIT_* del entorno y un .env del
# directorio de trabajo. Los contadores viven en el proceso (un solo worker).
# Cuenta después de validar el cuerpo: un evento inválido (422) no usa cupo, pero
# tampoco guarda nada.
limiter = Limiter(
    key_func=client_ip,
    storage_uri="memory://",
    strategy="fixed-window",
    headers_enabled=False,
)
