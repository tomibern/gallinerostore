"""Ayudas de los tests de métricas: eventos con el reloj fijado y un navegador del admin.

La tienda de prueba está en `America/Montevideo` (UTC-3 todo el año): las horas de los
tests son las de la tienda, y «ahora» es el martes 17/11/2026 a las 15:30.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta, timezone
from typing import Any

import httpx
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.service import create_admin
from tests.support import Clock, http_client

STORE_ZONE = timezone(timedelta(hours=-3))
EMAIL = "admin@tienda.test"
PASSWORD = "una-clave-larga"
ADMIN_HEADERS = {"X-Requested-With": "fetch"}


def local(day: int, hour: int = 12, minute: int = 0, month: int = 11) -> datetime:
    """Una hora de la tienda, en noviembre de 2026 salvo que se diga otro mes."""
    return datetime(2026, month, day, hour, minute, tzinfo=STORE_ZONE)


NOW = local(17, 15, 30)


def session_id(n: int) -> str:
    return f"{n:032x}"


@asynccontextmanager
async def admin_browser(app: FastAPI, db_session: AsyncSession) -> AsyncIterator[httpx.AsyncClient]:
    """Un navegador aparte con la sesión del admin iniciada."""
    await create_admin(db_session, EMAIL, PASSWORD)
    async with http_client(app) as client:
        response = await client.post(
            "/admin/session",
            json={"email": EMAIL, "password": PASSWORD, "remember": False},
            headers=ADMIN_HEADERS,
        )
        assert response.status_code == 200
        yield client


async def visit(
    client: httpx.AsyncClient,
    clock: Clock,
    when: datetime,
    session: int,
    page: str = "home",
    source: str = "directo",
) -> None:
    await _post(clock, client, when, session, source, type="page_view", page=page)


async def view_product(
    client: httpx.AsyncClient, clock: Clock, when: datetime, session: int, code: str
) -> None:
    await _post(clock, client, when, session, "directo", type="product_view", product_code=code)


async def ask(
    client: httpx.AsyncClient,
    clock: Clock,
    when: datetime,
    session: int,
    code: str | None = None,
    channel: str = "whatsapp",
    size: str = "S",
) -> None:
    """Una consulta: por un producto si hay código; si no, general."""
    fields: dict[str, Any] = (
        {"type": "contact_click", "product_code": code, "size": size}
        if code
        else {"type": "general_contact_click", "page": "home"}
    )
    await _post(clock, client, when, session, "directo", channel=channel, **fields)


async def _post(
    clock: Clock,
    client: httpx.AsyncClient,
    when: datetime,
    session: int,
    source: str,
    **fields: Any,
) -> None:
    clock.now = when.astimezone(UTC)
    body = {"session_id": session_id(session), "source": source, "device": "mobile", **fields}
    response = await client.post("/events", json=body)
    assert response.status_code == 204, response.text
