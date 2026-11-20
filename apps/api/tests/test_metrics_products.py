"""Ranking de productos (`GET /admin/metrics/products?period=…&sort=…`) y las cifras de
7 días del listado del admin (`GET /admin/products`).

Los eventos entran por `POST /events` con el reloj fijado, como en el resumen. Las
mismas reglas: una visita es un par (sesión, producto, día de la tienda) y cada clic es
una consulta.
"""

from collections.abc import AsyncIterator
from datetime import UTC
from typing import Any

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.models import Product, ProductStatus
from tests.metrics_support import NOW, admin_browser, ask, local, view_product
from tests.support import Clock

# Productos publicados del seed de prueba (tests/fixtures/seed.toml), por slug.
SLUGS = {
    "a": "remera-basica",
    "b": "remera-completa",
    "c": "buzo-a-pedido",
    "d": "campera-en-stock",
}


@pytest.fixture
async def admin(
    app: FastAPI, db_session: AsyncSession, clock: Clock
) -> AsyncIterator[httpx.AsyncClient]:
    async with admin_browser(app, db_session) as client:
        yield client


@pytest.fixture
async def codes(db_session: AsyncSession, seeded: None) -> dict[str, str]:
    """Código de cada producto de SLUGS, con la misma letra."""
    rows = await db_session.execute(
        select(Product.slug, Product.code).where(Product.slug.in_(SLUGS.values()))
    )
    by_slug = {slug: code for slug, code in rows}
    return {letter: by_slug[slug] for letter, slug in SLUGS.items()}


async def ranking(
    admin: httpx.AsyncClient, clock: Clock, period: str = "7d", sort: str | None = None
) -> dict[str, Any]:
    clock.now = NOW.astimezone(UTC)
    params = {"period": period} | ({"sort": sort} if sort else {})
    response = await admin.get("/admin/metrics/products", params=params)
    assert response.status_code == 200, response.text
    data: dict[str, Any] = response.json()
    return data


def order(data: dict[str, Any], codes: dict[str, str]) -> list[str]:
    """Las letras de los productos del ranking, en su orden."""
    letters = {code: letter for letter, code in codes.items()}
    return [letters[item["code"]] for item in data["items"]]


async def activity(client: httpx.AsyncClient, clock: Clock, codes: dict[str, str]) -> None:
    """A: 4 visitas (la sesión 1 vuelve el mismo día: una sola), 1 consulta por WhatsApp.
    B: 1 visita, 2 consultas por Instagram. C: 2 visitas, ninguna consulta.
    D: ninguna visita, 1 consulta por WhatsApp. Todo hoy."""
    for session in (1, 2, 3, 4):
        await view_product(client, clock, local(17, 10), session, codes["a"])
    await view_product(client, clock, local(17, 10, 30), 1, codes["a"])
    await ask(client, clock, local(17, 11), 1, codes["a"])
    await view_product(client, clock, local(17, 10), 5, codes["b"])
    await ask(client, clock, local(17, 11), 5, codes["b"], channel="instagram")
    await ask(client, clock, local(17, 11, 1), 5, codes["b"], channel="instagram")
    await view_product(client, clock, local(17, 9), 6, codes["c"])
    await view_product(client, clock, local(17, 9), 7, codes["c"])
    await ask(client, clock, local(17, 12), 8, codes["d"], size="L")
    # Ni Remera agotada ni nada más tuvo actividad: no entran al ranking.


# --- Acceso -------------------------------------------------------------------


async def test_without_a_session_the_ranking_is_401(client: httpx.AsyncClient) -> None:
    response = await client.get("/admin/metrics/products", params={"period": "7d"})

    assert response.status_code == 401


# --- Ranking ------------------------------------------------------------------


@pytest.mark.parametrize(
    ("sort", "expected"),
    [
        # Empates: más consultas, después más visitas.
        ("inquiries", ["b", "a", "d", "c"]),
        ("visits", ["a", "c", "b", "d"]),
        # D no tiene visitas: sin tasa, va al final.
        ("rate", ["b", "a", "c", "d"]),
        ("whatsapp", ["a", "d", "b", "c"]),
        ("instagram", ["b", "a", "d", "c"]),
    ],
)
async def test_the_ranking_is_ordered_by_each_column(
    client: httpx.AsyncClient,
    admin: httpx.AsyncClient,
    clock: Clock,
    codes: dict[str, str],
    instagram_on: None,
    sort: str,
    expected: list[str],
) -> None:
    await activity(client, clock, codes)

    data = await ranking(admin, clock, sort=sort)

    assert data["sort"] == sort
    assert order(data, codes) == expected


async def test_by_default_the_ranking_goes_by_inquiries(
    client: httpx.AsyncClient,
    admin: httpx.AsyncClient,
    clock: Clock,
    codes: dict[str, str],
    instagram_on: None,
) -> None:
    await activity(client, clock, codes)

    data = await ranking(admin, clock)

    assert data["period"] == "7d"
    assert data["sort"] == "inquiries"
    assert order(data, codes) == ["b", "a", "d", "c"]


async def test_each_product_has_its_rate_and_its_inquiries_by_channel(
    client: httpx.AsyncClient,
    admin: httpx.AsyncClient,
    clock: Clock,
    codes: dict[str, str],
    instagram_on: None,
) -> None:
    await activity(client, clock, codes)

    data = await ranking(admin, clock, period="today")

    rows = {
        item["code"]: (
            item["visits"],
            item["inquiries"],
            item["rate"],
            item["whatsapp"],
            item["instagram"],
        )
        for item in data["items"]
    }
    assert rows == {
        codes["a"]: (4, 1, 0.25, 1, 0),
        codes["b"]: (1, 2, 2.0, 0, 2),
        codes["c"]: (2, 0, 0.0, 0, 0),
        codes["d"]: (0, 1, None, 1, 0),
    }
    assert data["channels"] == ["whatsapp", "instagram"]


async def test_only_the_activity_of_the_period_counts(
    client: httpx.AsyncClient, admin: httpx.AsyncClient, clock: Clock, codes: dict[str, str]
) -> None:
    # El 10/11 queda afuera de los últimos 7 días (11 al 17) y adentro de los 30.
    await view_product(client, clock, local(10, 23, 59), 1, codes["a"])
    await ask(client, clock, local(10, 23, 59), 1, codes["a"])
    await view_product(client, clock, local(11, 0, 1), 2, codes["b"])

    week = await ranking(admin, clock, period="7d")
    month = await ranking(admin, clock, period="30d")

    assert order(week, codes) == ["b"]
    assert order(
        month,
        codes,
    ) == ["a", "b"]
    assert month["items"][0]["inquiries"] == 1


async def test_an_archived_product_with_activity_in_the_period_is_ranked(
    client: httpx.AsyncClient,
    admin: httpx.AsyncClient,
    clock: Clock,
    codes: dict[str, str],
    db_session: AsyncSession,
) -> None:
    await view_product(client, clock, local(16, 10), 1, codes["c"])
    await db_session.execute(
        update(Product).where(Product.code == codes["c"]).values(status=ProductStatus.ARCHIVED)
    )

    data = await ranking(admin, clock)

    assert [(item["code"], item["status"]) for item in data["items"]] == [(codes["c"], "archived")]


async def test_with_instagram_off_and_no_inquiries_there_is_no_instagram_column(
    client: httpx.AsyncClient, admin: httpx.AsyncClient, clock: Clock, codes: dict[str, str]
) -> None:
    await ask(client, clock, local(17, 10), 1, codes["a"])

    data = await ranking(admin, clock)

    assert data["channels"] == ["whatsapp"]


async def test_without_activity_the_ranking_is_empty(
    admin: httpx.AsyncClient, clock: Clock, seeded: None
) -> None:
    data = await ranking(admin, clock, period="today")

    assert data["items"] == []


async def test_an_unknown_sort_is_rejected(admin: httpx.AsyncClient) -> None:
    response = await admin.get("/admin/metrics/products", params={"sort": "price"})

    assert response.status_code == 422


# --- Listado del admin ----------------------------------------------------------


async def test_the_admin_listing_has_the_figures_of_the_last_7_days_of_the_ranking(
    client: httpx.AsyncClient,
    admin: httpx.AsyncClient,
    clock: Clock,
    codes: dict[str, str],
    instagram_on: None,
) -> None:
    await activity(client, clock, codes)
    # Hace 8 días: no entra en ninguna de las dos pantallas.
    await view_product(client, clock, local(10, 12), 9, codes["c"])
    await ask(client, clock, local(10, 12), 9, codes["a"])

    week = await ranking(admin, clock, period="7d")
    response = await admin.get("/admin/products", params={"filter": "all", "limit": 100})
    assert response.status_code == 200, response.text
    listing = {item["code"]: item for item in response.json()["items"]}

    ranked = {item["code"]: item for item in week["items"]}
    for code, item in listing.items():
        expected = ranked.get(code, {"visits": 0, "inquiries": 0})
        assert (item["visits_7d"], item["inquiries_7d"]) == (
            expected["visits"],
            expected["inquiries"],
        ), item["name"]
    assert (listing[codes["a"]]["visits_7d"], listing[codes["a"]]["inquiries_7d"]) == (4, 1)
    assert (listing[codes["c"]]["visits_7d"], listing[codes["c"]]["inquiries_7d"]) == (2, 0)
