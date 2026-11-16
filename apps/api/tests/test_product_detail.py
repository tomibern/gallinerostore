"""Detalle de un producto publicado: datos, fotos y talles con su estado.

El código identifica al producto (el link sobrevive a un cambio de nombre). Los
talles ya vienen calculados: en stock, los propios con su estado; un encargue o un
agotado que pasó a Por encargue, todos los del grupo de su categoría, pedibles.
"""

from typing import Any

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, StoreFeatures, get_store_config
from app.modules.catalog.models import Product
from app.modules.settings.seed import apply_settings_seed, load_settings_seed
from tests.conftest import FIXTURES

PRENDA = ["S", "M", "L", "XL"]


async def _code(client: httpx.AsyncClient, slug: str) -> str:
    """El código cambia entre corridas (la secuencia no vuelve atrás): se saca del listado."""
    items = (await client.get("/products")).json()["items"]
    code: str = next(p["code"] for p in items if p["slug"] == slug)
    return code


async def _detail(client: httpx.AsyncClient, slug: str) -> dict[str, Any]:
    response = await client.get(f"/products/{(await _code(client, slug)).lower()}")
    assert response.status_code == 200
    detail: dict[str, Any] = response.json()
    return detail


def _sizes(detail: dict[str, Any]) -> list[tuple[str, str]]:
    return [(s["label"], s["status"]) for s in detail["sizes"]]


async def test_stock_product_shows_its_data_photos_and_sizes(
    client: httpx.AsyncClient, seeded: None
) -> None:
    detail = await _detail(client, "remera-completa")

    assert detail["name"] == "Remera completa"
    assert detail["price"] == 2100000
    assert detail["currency"] == "USD"
    assert detail["section"] == "stock"
    assert detail["availability"] == "in_stock"
    assert detail["category"] == {"slug": "remeras", "name": "Remeras"}
    assert detail["collection"] == {"slug": "marca-b", "name": "Marca B"}
    assert detail["description"] is None
    assert detail["season"] is None
    assert len(detail["images"]) == 3
    assert detail["images"][0]["full"].startswith("/media/")
    assert _sizes(detail) == [(label, "in_stock") for label in PRENDA]
    assert detail["on_order_notice"] is None


async def test_stock_product_shows_only_its_own_sizes_with_out_of_stock_ones(
    client: httpx.AsyncClient, seeded: None
) -> None:
    detail = await _detail(client, "remera-basica")

    # Sin XL (no lo tiene) y M sin stock: tachado, pero elegible.
    assert _sizes(detail) == [("S", "in_stock"), ("M", "out_of_stock"), ("L", "in_stock")]


async def test_on_order_product_offers_every_size_of_its_category_group(
    client: httpx.AsyncClient, seeded: None
) -> None:
    # Categoría de nivel 2 (buzos): hereda el grupo de abrigos.
    detail = await _detail(client, "buzo-a-pedido")

    assert detail["section"] == "on_order"
    assert detail["availability"] == "on_order"
    assert _sizes(detail) == [(label, "on_order") for label in PRENDA]


async def test_sold_out_product_offers_every_size_of_its_group_on_order(
    client: httpx.AsyncClient, seeded: None
) -> None:
    # Solo tiene S y M (sin stock): igual se pide en L y XL.
    detail = await _detail(client, "remera-agotada")

    assert detail["availability"] == "sold_out_on_order"
    assert _sizes(detail) == [(label, "on_order") for label in PRENDA]


async def test_sold_out_with_on_order_turned_off_shows_its_own_sizes_out_of_stock(
    app: FastAPI, client: httpx.AsyncClient, settings: Settings, seeded: None
) -> None:
    store = settings.store_config.model_copy(update={"features": StoreFeatures(on_order=False)})
    app.dependency_overrides[get_store_config] = lambda: store

    detail = await _detail(client, "remera-agotada")

    assert detail["section"] == "stock"
    assert detail["availability"] == "sold_out"
    assert _sizes(detail) == [("S", "out_of_stock"), ("M", "out_of_stock")]
    assert detail["on_order_notice"] is None


@pytest.mark.parametrize(
    ("slug", "expected"),
    [("gorra-en-stock", [("Único", "in_stock")]), ("gorra-a-pedido", [("Único", "on_order")])],
)
async def test_single_size_product_has_one_size(
    client: httpx.AsyncClient, seeded: None, slug: str, expected: list[tuple[str, str]]
) -> None:
    assert _sizes(await _detail(client, slug)) == expected


async def test_code_is_case_insensitive(client: httpx.AsyncClient, seeded: None) -> None:
    code = await _code(client, "remera-basica")

    lower = await client.get(f"/products/{code.lower()}")
    upper = await client.get(f"/products/{code.upper()}")

    assert lower.status_code == upper.status_code == 200
    assert lower.json()["code"] == upper.json()["code"] == code


@pytest.mark.parametrize("slug", ["remera-borrador", "remera-oculta", "buzo-archivado"])
async def test_unpublished_product_is_not_found(
    client: httpx.AsyncClient, db_session: AsyncSession, seeded: None, slug: str
) -> None:
    code = await db_session.scalar(select(Product.code).where(Product.slug == slug))
    assert code is not None

    response = await client.get(f"/products/{code.lower()}")

    assert response.status_code == 404


async def test_unknown_code_is_not_found(client: httpx.AsyncClient, seeded: None) -> None:
    response = await client.get("/products/tp-99999")

    assert response.status_code == 404


async def test_on_order_notice_comes_from_the_store_settings(
    client: httpx.AsyncClient, db_session: AsyncSession, seeded: None
) -> None:
    seed = load_settings_seed(FIXTURES / "seed.toml")
    assert seed is not None
    await apply_settings_seed(db_session, seed)

    on_order = await _detail(client, "buzo-a-pedido")
    sold_out = await _detail(client, "remera-agotada")
    stock = await _detail(client, "remera-completa")

    assert on_order["on_order_notice"] == "Demora a confirmar."
    assert sold_out["on_order_notice"] == "Demora a confirmar."
    assert stock["on_order_notice"] is None


async def test_on_order_notice_is_null_without_store_settings(
    client: httpx.AsyncClient, seeded: None
) -> None:
    assert (await _detail(client, "buzo-a-pedido"))["on_order_notice"] is None


async def test_version_is_shown_only_with_versions_turned_on(
    app: FastAPI, client: httpx.AsyncClient, settings: Settings, seeded: None
) -> None:
    # El fixture tiene las versiones apagadas.
    assert (await _detail(client, "remera-completa"))["version"] is None

    store = settings.store_config.model_copy(update={"features": StoreFeatures(versions=True)})
    app.dependency_overrides[get_store_config] = lambda: store

    assert (await _detail(client, "remera-completa"))["version"] == {
        "slug": "moderna",
        "name": "Moderna",
    }
    assert (await _detail(client, "remera-agotada"))["version"] is None


async def test_collection_is_hidden_with_collections_turned_off(
    app: FastAPI, client: httpx.AsyncClient, settings: Settings, seeded: None
) -> None:
    store = settings.store_config.model_copy(update={"features": StoreFeatures(collections=False)})
    app.dependency_overrides[get_store_config] = lambda: store

    assert (await _detail(client, "remera-completa"))["collection"] is None
