"""Destacados: los productos publicados marcados como destacados, para la home."""

from typing import Any

import httpx

# Destacados publicados del fixture, en su orden manual (de las dos secciones).
FEATURED = ["remera-basica", "buzo-a-pedido", "gorra-en-stock"]


async def _slugs(client: httpx.AsyncClient, **params: Any) -> list[str]:
    response = await client.get("/products", params=params)
    assert response.status_code == 200
    return [p["slug"] for p in response.json()["items"]]


async def test_featured_lists_only_published_featured_products_in_manual_order(
    client: httpx.AsyncClient, seeded: None
) -> None:
    # remera-oculta también es destacada, pero no está publicada.
    assert await _slugs(client, featured="true") == FEATURED


async def test_featured_items_carry_their_section_and_availability(
    client: httpx.AsyncClient, seeded: None
) -> None:
    items = (await client.get("/products", params={"featured": "true"})).json()["items"]

    assert {p["slug"]: p["availability"] for p in items} == {
        "remera-basica": "in_stock",
        "buzo-a-pedido": "on_order",
        "gorra-en-stock": "in_stock",
    }


async def test_featured_combines_with_section(client: httpx.AsyncClient, seeded: None) -> None:
    assert await _slugs(client, featured="true", section="on_order") == ["buzo-a-pedido"]


async def test_featured_false_does_not_filter(client: httpx.AsyncClient, seeded: None) -> None:
    assert await _slugs(client, featured="false") == await _slugs(client)


async def test_invalid_featured_is_rejected(client: httpx.AsyncClient, seeded: None) -> None:
    response = await client.get("/products", params={"featured": "quizas"})

    assert response.status_code == 422
