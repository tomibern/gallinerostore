"""Resumen de métricas del admin: `GET /admin/metrics/summary?period=…`.

Los eventos entran por `POST /events` con el reloj fijado, como los manda la web. La
tienda de prueba está en `America/Montevideo` (UTC-3 todo el año): las horas de los
tests son las de la tienda, y «ahora» es el martes 17/11/2026 a las 15:30.
"""

from collections.abc import AsyncIterator
from datetime import UTC
from typing import Any

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.models import Product
from app.modules.events.models import Event, EventType
from tests.metrics_support import (
    NOW,
    admin_browser,
    ask,
    local,
    view_product,
    visit,
)
from tests.support import Clock


@pytest.fixture
async def admin(
    app: FastAPI, db_session: AsyncSession, clock: Clock
) -> AsyncIterator[httpx.AsyncClient]:
    """Un navegador aparte con la sesión del admin iniciada."""
    async with admin_browser(app, db_session) as client:
        yield client


@pytest.fixture
async def code(db_session: AsyncSession, seeded: None) -> str:
    """Código de un producto publicado del seed de prueba."""
    found = await db_session.scalar(select(Product.code).where(Product.slug == "remera-basica"))
    assert found is not None
    return found


async def summary(admin: httpx.AsyncClient, clock: Clock, period: str) -> dict[str, Any]:
    clock.now = NOW.astimezone(UTC)
    response = await admin.get("/admin/metrics/summary", params={"period": period})
    assert response.status_code == 200, response.text
    data: dict[str, Any] = response.json()
    return data


def chart_visits(data: dict[str, Any]) -> dict[str, int]:
    return {point["date"]: point["visits"] for point in data["chart"] if point["visits"]}


async def test_without_a_session_the_summary_is_401(client: httpx.AsyncClient) -> None:
    response = await client.get("/admin/metrics/summary", params={"period": "today"})

    assert response.status_code == 401


async def test_reloading_the_same_page_the_same_day_is_one_visit(
    client: httpx.AsyncClient, admin: httpx.AsyncClient, clock: Clock, code: str
) -> None:
    for minute in (0, 1, 2):
        await visit(client, clock, local(17, 10, minute), session=1)
    await visit(client, clock, local(17, 10, 5), session=1, page="stock")
    await view_product(client, clock, local(17, 10, 6), 1, code)
    await view_product(client, clock, local(17, 10, 7), 1, code)
    await visit(client, clock, local(17, 11), session=2)

    data = await summary(admin, clock, "today")

    # Sesión 1: la home, el listado y el producto. Sesión 2: la home.
    assert data["visits"]["current"] == 4


async def test_days_are_the_store_days_not_utc_days(
    client: httpx.AsyncClient, admin: httpx.AsyncClient, clock: Clock
) -> None:
    # 20:00 y 22:00 del 15 en la tienda: el mismo día, aunque en UTC caen en días distintos.
    await visit(client, clock, local(15, 20), session=1)
    await visit(client, clock, local(15, 22), session=1)
    # Un minuto antes y uno después de la medianoche de la tienda: dos días, dos visitas.
    await visit(client, clock, local(16, 23, 59), session=1)
    await visit(client, clock, local(17, 0, 1), session=1)

    data = await summary(admin, clock, "7d")

    assert data["visits"]["current"] == 3
    assert chart_visits(data) == {"2026-11-15": 1, "2026-11-16": 1, "2026-11-17": 1}


async def test_events_without_a_session_count_one_by_one(
    client: httpx.AsyncClient, admin: httpx.AsyncClient, clock: Clock, db_session: AsyncSession
) -> None:
    """La web siempre manda la sesión, pero un evento viejo sin ella no se deduplica."""
    for minute in (0, 1):
        db_session.add(
            Event(type=EventType.PAGE_VIEW, page="home", created_at=local(17, 9, minute))
        )
    await db_session.flush()

    data = await summary(admin, clock, "today")

    assert data["visits"]["current"] == 2


async def test_every_click_is_an_inquiry_and_the_rate_uses_product_inquiries(
    client: httpx.AsyncClient, admin: httpx.AsyncClient, clock: Clock, code: str
) -> None:
    for session in (1, 2, 3, 4):
        await view_product(client, clock, local(17, 10), session, code)
    await visit(client, clock, local(17, 10), session=1)
    await ask(client, clock, local(17, 11), 1, code)
    await ask(client, clock, local(17, 11, 1), 1, code)  # el mismo clic otra vez: otra consulta
    await ask(client, clock, local(17, 11, 2), 2)  # consulta general

    data = await summary(admin, clock, "today")

    assert data["visits"]["current"] == 5  # cuatro detalles y una página
    assert data["inquiries"]["current"] == 3
    # Consultas de productos (2) dividido visitas a detalles (4).
    assert data["rate"]["current"] == 0.5


async def test_without_product_visits_there_is_no_rate(
    client: httpx.AsyncClient, admin: httpx.AsyncClient, clock: Clock
) -> None:
    await visit(client, clock, local(17, 10), session=1)
    await ask(client, clock, local(17, 11), 1)

    data = await summary(admin, clock, "today")

    assert data["rate"] == {"current": None, "previous": None}


async def test_today_is_compared_with_yesterday_up_to_the_same_time(
    client: httpx.AsyncClient, admin: httpx.AsyncClient, clock: Clock, code: str
) -> None:
    await visit(client, clock, local(17, 9), session=1)
    await visit(client, clock, local(17, 10), session=2)
    await view_product(client, clock, local(17, 10), 2, code)
    await ask(client, clock, local(17, 11), 2, code)
    await visit(client, clock, local(16, 0, 0), session=3)  # ayer, a la medianoche: cuenta
    await view_product(client, clock, local(16, 15, 29), 3, code)  # ayer, antes de las 15:30
    await ask(client, clock, local(16, 15, 29), 3, code)
    await visit(client, clock, local(16, 15, 31), session=4)  # ayer, después de esta hora: no
    await visit(client, clock, local(15, 23, 59), session=5)  # anteayer: no

    data = await summary(admin, clock, "today")

    assert data["visits"] == {"current": 3, "previous": 2, "change": 0.5}
    assert data["inquiries"] == {"current": 1, "previous": 1, "change": 0.0}
    assert data["rate"] == {"current": 1.0, "previous": 1.0}


async def test_seven_days_are_today_and_the_six_before_compared_with_the_seven_before_that(
    client: httpx.AsyncClient, admin: httpx.AsyncClient, clock: Clock
) -> None:
    await visit(client, clock, local(11, 0, 0), session=1)  # primer día del período
    await visit(client, clock, local(10, 15), session=2)  # período anterior, antes de la hora
    await visit(client, clock, local(10, 16), session=3)  # después de esta hora: fuera
    await visit(client, clock, local(4, 0, 0), session=4)  # primer día del anterior
    await visit(client, clock, local(3, 23, 59), session=5)  # fuera

    data = await summary(admin, clock, "7d")

    assert data["visits"] == {"current": 1, "previous": 2, "change": -0.5}
    assert [point["date"] for point in data["chart"]] == [f"2026-11-{day}" for day in range(11, 18)]
    assert all(point["hour"] is None for point in data["chart"])


async def test_thirty_days_chart_has_one_bar_per_day(
    client: httpx.AsyncClient, admin: httpx.AsyncClient, clock: Clock
) -> None:
    await visit(client, clock, local(19, 10, month=10), session=1)
    await visit(client, clock, local(18, 10, month=10), session=2)  # período anterior

    data = await summary(admin, clock, "30d")

    assert len(data["chart"]) == 30
    assert data["chart"][0]["date"] == "2026-10-19"
    assert data["chart"][-1]["date"] == "2026-11-17"
    assert chart_visits(data) == {"2026-10-19": 1}
    assert data["visits"]["previous"] == 1


async def test_today_chart_goes_by_hour_until_now(
    client: httpx.AsyncClient, admin: httpx.AsyncClient, clock: Clock
) -> None:
    await visit(client, clock, local(17, 9, 10), session=1)
    await visit(client, clock, local(17, 9, 50), session=2)
    await visit(client, clock, local(17, 9, 55), session=2)  # recarga: sigue a las 9
    await ask(client, clock, local(17, 14, 5), 1)
    await ask(client, clock, local(17, 14, 6), 1)

    data = await summary(admin, clock, "today")

    chart = data["chart"]
    assert [point["hour"] for point in chart] == list(range(16))  # de 0 a 15 h
    assert {point["date"] for point in chart} == {"2026-11-17"}
    assert {p["hour"]: p["visits"] for p in chart if p["visits"]} == {9: 2}
    assert {p["hour"]: p["inquiries"] for p in chart if p["inquiries"]} == {14: 2}


async def test_inquiries_by_channel(
    client: httpx.AsyncClient, admin: httpx.AsyncClient, clock: Clock, code: str
) -> None:
    await ask(client, clock, local(17, 10), 1, code)
    await ask(client, clock, local(17, 10), 2)
    await ask(client, clock, local(17, 10), 3)
    # Instagram está apagado en la tienda de prueba, pero tuvo consultas: aparece.
    await ask(client, clock, local(17, 10), 4, code, channel="instagram")

    data = await summary(admin, clock, "today")

    assert data["channels"] == [
        {"channel": "whatsapp", "inquiries": 3, "share": 0.75},
        {"channel": "instagram", "inquiries": 1, "share": 0.25},
    ]


async def test_a_channel_that_is_off_and_has_no_inquiries_does_not_appear(
    admin: httpx.AsyncClient, clock: Clock
) -> None:
    data = await summary(admin, clock, "today")

    assert data["channels"] == [{"channel": "whatsapp", "inquiries": 0, "share": None}]


async def test_sources_go_by_volume_with_direct_and_unknown_together(
    client: httpx.AsyncClient, admin: httpx.AsyncClient, clock: Clock
) -> None:
    for session in (1, 2, 3):
        await visit(client, clock, local(17, 10), session, source="bio")
    await visit(client, clock, local(17, 10, 1), session=1, source="bio")  # recarga
    await visit(client, clock, local(17, 10), session=4, source="historia")
    # La misma visita con otro origen después: queda el de su primer evento.
    await visit(client, clock, local(17, 10, 1), session=4, source="bio")
    await visit(client, clock, local(17, 10), session=5, source="directo")
    await visit(client, clock, local(17, 10), session=6, source="directo")

    data = await summary(admin, clock, "today")

    assert data["sources"] == [
        {"source": "bio", "visits": 3, "share": 0.5},
        {"source": None, "visits": 2, "share": pytest.approx(1 / 3)},
        {"source": "historia", "visits": 1, "share": pytest.approx(1 / 6)},
    ]


async def test_events_sent_with_an_admin_session_are_not_saved(
    client: httpx.AsyncClient, admin: httpx.AsyncClient, clock: Clock, db_session: AsyncSession
) -> None:
    await visit(admin, clock, local(17, 10), session=1)
    await ask(admin, clock, local(17, 10), 1)
    await visit(client, clock, local(17, 10), session=2)

    data = await summary(admin, clock, "today")

    assert data["visits"]["current"] == 1
    assert data["inquiries"]["current"] == 0
    assert await db_session.scalar(select(func.count()).select_from(Event)) == 1
