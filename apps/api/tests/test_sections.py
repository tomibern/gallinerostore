"""Secciones del catálogo público: En stock y Por encargue, con la regla del agotado.

La sección se calcula, no se guarda: un encargue va a Por encargue; un producto de
stock con algún talle disponible, a En stock; uno agotado (ningún talle
disponible), a Por encargue avisando que se agotó.
"""

from typing import Any

import httpx
from fastapi import FastAPI

from app.core.config import Settings, StoreFeatures, get_store_config

STOCK = ["remera-basica", "remera-completa", "campera-en-stock", "gorra-en-stock"]
ON_ORDER = ["buzo-a-pedido", "remera-agotada", "buzo-agotado", "gorra-a-pedido", "campera-a-pedido"]


async def _section(client: httpx.AsyncClient, section: str) -> list[dict[str, Any]]:
    response = await client.get("/products", params={"section": section})
    assert response.status_code == 200
    products: list[dict[str, Any]] = response.json()["items"]
    return products


def _slugs(products: list[dict[str, Any]]) -> list[str]:
    return [p["slug"] for p in products]


async def test_stock_section_lists_stock_products_with_some_size_available(
    client: httpx.AsyncClient, seeded: None
) -> None:
    products = await _section(client, "stock")

    # En el orden manual del seed. Uno con talles sin stock (remera-basica) sigue en stock.
    assert _slugs(products) == STOCK
    assert {p["section"] for p in products} == {"stock"}
    assert {p["availability"] for p in products} == {"in_stock"}


async def test_on_order_section_lists_on_order_and_sold_out_products(
    client: httpx.AsyncClient, seeded: None
) -> None:
    products = await _section(client, "on_order")

    assert _slugs(products) == ON_ORDER
    assert {p["section"] for p in products} == {"on_order"}
    availability = {p["slug"]: p["availability"] for p in products}
    assert availability == {
        "buzo-a-pedido": "on_order",
        "remera-agotada": "sold_out_on_order",
        "buzo-agotado": "sold_out_on_order",
        "gorra-a-pedido": "on_order",
        "campera-a-pedido": "on_order",
    }


async def test_without_section_lists_every_published_product_once(
    client: httpx.AsyncClient, seeded: None
) -> None:
    products = (await client.get("/products")).json()["items"]

    assert sorted(_slugs(products)) == sorted(STOCK + ON_ORDER)


async def test_unknown_section_is_rejected(client: httpx.AsyncClient, seeded: None) -> None:
    response = await client.get("/products", params={"section": "outlet"})

    assert response.status_code == 422


async def test_sold_out_stays_in_stock_when_on_order_is_turned_off(
    app: FastAPI, client: httpx.AsyncClient, settings: Settings, seeded: None
) -> None:
    store = settings.store_config.model_copy(update={"features": StoreFeatures(on_order=False)})
    app.dependency_overrides[get_store_config] = lambda: store

    stock = await _section(client, "stock")
    on_order = await _section(client, "on_order")

    assert _slugs(stock) == [
        "remera-basica",
        "remera-agotada",
        "remera-completa",
        "campera-en-stock",
        "buzo-agotado",
        "gorra-en-stock",
    ]
    availability = {p["slug"]: p["availability"] for p in stock}
    assert availability["remera-agotada"] == "sold_out"
    assert availability["buzo-agotado"] == "sold_out"
    assert availability["remera-basica"] == "in_stock"
    assert _slugs(on_order) == ["buzo-a-pedido", "gorra-a-pedido", "campera-a-pedido"]
