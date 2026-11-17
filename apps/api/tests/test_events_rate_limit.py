"""Límite de frecuencia de `POST /events` por IP.

Todo pasa por Next (ADR 0003), así que la IP del visitante llega en `X-Forwarded-For`.
La izquierda de ese header la escribe quien quiera; vale la entrada que agregó el
último proxy de confianza, contando desde la derecha (ADR 0006).
"""

from typing import Any

import httpx
from fastapi import FastAPI
from limits import parse

from app.core.config import Settings
from app.main import create_app
from app.modules.events.rate_limit import EVENTS_RATE_LIMIT, limiter

LIMIT = parse(EVENTS_RATE_LIMIT).amount
EVENT = {
    "type": "page_view",
    "page": "home",
    "session_id": "0123456789abcdef0123456789abcdef",
    "source": "directo",
    "device": "mobile",
}


async def _post(client: httpx.AsyncClient, forwarded_for: str | None = None) -> int:
    headers = {"X-Forwarded-For": forwarded_for} if forwarded_for is not None else {}
    response = await client.post("/events", json=EVENT, headers=headers)
    return response.status_code


async def _use_up(client: httpx.AsyncClient, forwarded_for: str | None = None) -> None:
    for _ in range(LIMIT):
        assert await _post(client, forwarded_for) == 204


async def test_going_over_the_limit_returns_429(client: httpx.AsyncClient) -> None:
    await _use_up(client, "1.1.1.1")

    response = await client.post("/events", json=EVENT, headers={"X-Forwarded-For": "1.1.1.1"})

    assert response.status_code == 429
    body: dict[str, Any] = response.json()
    assert "detail" in body


async def test_each_forwarded_ip_has_its_own_limit(client: httpx.AsyncClient) -> None:
    await _use_up(client, "1.1.1.1")

    assert await _post(client, "2.2.2.2") == 204


async def test_the_left_of_x_forwarded_for_is_ignored(client: httpx.AsyncClient) -> None:
    """Cambiar lo que manda el cliente no da un cupo nuevo: cuenta el que agregó el proxy."""
    await _use_up(client, "9.9.9.9, 1.1.1.1")

    assert await _post(client, "8.8.8.8, 1.1.1.1") == 429


async def test_without_a_valid_forwarded_ip_the_peer_is_used(client: httpx.AsyncClient) -> None:
    await _use_up(client, "basura")

    assert await _post(client) == 429


async def test_ipv6_addresses_share_the_limit_of_their_64_prefix(
    client: httpx.AsyncClient,
) -> None:
    await _use_up(client, "2001:db8:1:2::1")

    assert await _post(client, "2001:db8:1:2:ffff::9") == 429
    assert await _post(client, "2001:db8:1:3::1") == 204


async def test_without_trusted_proxies_x_forwarded_for_is_ignored(
    app: FastAPI, settings: Settings, client: httpx.AsyncClient
) -> None:
    app.state.settings = settings.model_copy(update={"trusted_proxy_hops": 0})
    await _use_up(client, "1.1.1.1")

    assert await _post(client, "2.2.2.2") == 429


async def test_invalid_events_do_not_use_up_the_limit(client: httpx.AsyncClient) -> None:
    """slowapi cuenta después de validar el cuerpo; un 422 no guarda nada."""
    for _ in range(LIMIT):
        response = await client.post("/events", json={"type": "nada"})
        assert response.status_code == 422

    assert await _post(client) == 204


async def test_the_limit_can_be_turned_off(settings: Settings) -> None:
    """Para el e2e, que manda todo desde la misma IP. El limiter es uno por proceso:
    la fixture `rate_limit` lo vuelve a prender después de cada test."""
    create_app(settings.model_copy(update={"rate_limit_enabled": False}))

    assert limiter.enabled is False
