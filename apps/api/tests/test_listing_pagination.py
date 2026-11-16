"""Paginación del listado: GET /products con limit y offset.

La API pagina con offset sobre un orden total (todos los órdenes terminan en el id),
así que recorrer las páginas una tras otra da el listado completo, sin repetidos ni
faltantes. ``has_more`` dice si hay otra página y ``total`` cuántos productos cumplen
los filtros.
"""

from datetime import UTC, datetime
from typing import Any

import httpx
import pytest
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.storage import ObjectStorage
from app.modules.catalog import seed
from app.modules.catalog.models import Product, ProductSort, ProductStatus, SaleMode
from app.modules.catalog.seed import CatalogSeed, ProductSeed, apply_seed, load_seed
from app.modules.media.service import StoredImage
from tests.conftest import FIXTURES

Params = dict[str, str | int | list[str]]

# Publicados en En stock en el seed de fixtures (ver test_listing_filters.py).
FIXTURE_STOCK = 4


async def _listing(client: httpx.AsyncClient, params: Params) -> dict[str, Any]:
    response = await client.get("/products", params=params)
    assert response.status_code == 200, response.text
    listing: dict[str, Any] = response.json()
    return listing


async def _codes(client: httpx.AsyncClient, params: Params) -> list[str]:
    return [p["code"] for p in (await _listing(client, params))["items"]]


async def _all_pages(client: httpx.AsyncClient, params: Params, limit: int) -> list[str]:
    """Recorre el listado de a ``limit`` productos hasta que no hay más."""
    codes: list[str] = []
    while True:
        page = await _listing(client, params | {"limit": limit, "offset": len(codes)})
        codes += [p["code"] for p in page["items"]]
        if not page["has_more"]:
            return codes
        assert page["items"], "has_more con una página vacía"


async def _add_stock_products(
    db_session: AsyncSession, settings: Settings, storage: ObjectStorage, count: int
) -> None:
    """Suma ``count`` remeras publicadas en stock (con talle S), sobre la taxonomía del seed."""
    fixture = load_seed(FIXTURES / "seed.toml")
    extra = CatalogSeed(
        sizes=fixture.sizes,
        categories=fixture.categories,
        collections=fixture.collections,
        products=[
            ProductSeed(
                slug=f"remera-extra-{n:02d}",
                name=f"Remera extra {n:02d}",
                category="remeras",
                collection="marca-a",
                sale_mode=SaleMode.STOCK,
                status=ProductStatus.PUBLISHED,
                price=1000000 + n * 100,
                sizes={"S": True},
            )
            for n in range(count)
        ],
    )
    await apply_seed(db_session, extra, settings.store_config, storage)


def _skip_photo(storage: ObjectStorage, code: str, position: int, data: bytes) -> StoredImage:
    """Foto de prueba sin procesar ni subir: acá solo importa el listado, y así es rápido."""
    base = f"products/{code}/{position + 1}"
    return StoredImage(
        position=position,
        path_full=f"{base}-1600.webp",
        path_thumb=f"{base}-400.webp",
        width=1600,
        height=1600,
    )


@pytest.fixture
async def many(
    db_session: AsyncSession,
    settings: Settings,
    storage: ObjectStorage,
    seeded: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """25 productos en En stock: dos páginas de 20 y algo más."""
    monkeypatch.setattr(seed, "store_product_image", _skip_photo)
    await _add_stock_products(db_session, settings, storage, 25 - FIXTURE_STOCK)


# --- Tamaño de página ---------------------------------------------------------


async def test_first_page_has_twenty_products_by_default(
    client: httpx.AsyncClient, many: None
) -> None:
    page = await _listing(client, {"section": "stock"})

    assert len(page["items"]) == 20
    assert page["has_more"] is True
    assert page["total"] == 25


async def test_last_page_has_the_rest_and_no_more(client: httpx.AsyncClient, many: None) -> None:
    page = await _listing(client, {"section": "stock", "offset": 20})

    assert len(page["items"]) == 5
    assert page["has_more"] is False
    assert page["total"] == 25


async def test_a_page_that_ends_exactly_at_the_end_has_no_more(
    client: httpx.AsyncClient, many: None
) -> None:
    page = await _listing(client, {"section": "stock", "limit": 25})

    assert len(page["items"]) == 25
    assert page["has_more"] is False


async def test_offset_past_the_end_is_an_empty_page_with_facets(
    client: httpx.AsyncClient, many: None
) -> None:
    page = await _listing(client, {"section": "stock", "offset": 100})

    assert page["items"] == []
    assert page["has_more"] is False
    assert page["total"] == 25
    # Las facetas cuentan sobre todo el listado filtrado, no sobre la página.
    assert {"value": "S", "name": "S", "count": 23} in page["facets"]["sizes"]


async def test_total_counts_the_filtered_listing(client: httpx.AsyncClient, many: None) -> None:
    page = await _listing(client, {"section": "stock", "size": "S", "limit": 1})

    assert len(page["items"]) == 1
    assert page["total"] == 23


# --- Páginas consecutivas -----------------------------------------------------


@pytest.mark.parametrize("sort", list(ProductSort))
async def test_consecutive_pages_cover_the_listing_once(
    client: httpx.AsyncClient, many: None, sort: ProductSort
) -> None:
    params: Params = {"section": "stock", "sort": sort.value}
    whole = await _codes(client, params | {"limit": 100})

    paged = await _all_pages(client, params, limit=3)

    assert len(whole) == 25
    assert paged == whole
    assert len(set(paged)) == len(paged)


@pytest.mark.parametrize("sort", list(ProductSort))
async def test_consecutive_pages_are_stable_when_everything_ties(
    client: httpx.AsyncClient, db_session: AsyncSession, many: None, sort: ProductSort
) -> None:
    # Mismo orden manual, fecha y precio para todos: decide el id.
    await db_session.execute(
        update(Product).values(
            sort_order=0, price=1500000, created_at=datetime(2026, 1, 1, tzinfo=UTC)
        )
    )
    params: Params = {"section": "stock", "sort": sort.value}
    whole = await _codes(client, params | {"limit": 100})

    paged = await _all_pages(client, params, limit=3)

    assert paged == whole
    assert len(set(paged)) == 25


@pytest.mark.parametrize(
    "filters",
    [
        {"section": "stock", "category": "remeras"},
        {"section": "stock", "size": "S"},
        {"section": "stock", "category": "remeras", "size": "S", "sort": "price_desc"},
        {"section": "on_order"},
        {},
    ],
)
async def test_consecutive_pages_with_filters(
    client: httpx.AsyncClient, many: None, filters: Params
) -> None:
    whole = await _codes(client, filters | {"limit": 100})

    paged = await _all_pages(client, filters, limit=2)

    assert whole
    assert paged == whole
    assert len(set(paged)) == len(paged)
    assert (await _listing(client, filters | {"limit": 2}))["total"] == len(whole)


# --- Validación ----------------------------------------------------------------


@pytest.mark.parametrize(
    "params",
    [{"limit": 0}, {"limit": 101}, {"limit": "abc"}, {"offset": -1}],
)
async def test_out_of_range_pagination_is_rejected(
    client: httpx.AsyncClient, seeded: None, params: Params
) -> None:
    response = await client.get("/products", params=params)

    assert response.status_code == 422
