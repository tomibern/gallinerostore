"""Filtros y orden del listado: GET /products con categoría, versión, colección,
etiqueta, talle y orden.

Varios valores de un mismo filtro se suman (O) y filtros distintos se cruzan (Y).
Un filtro que no aplica (función apagada, talle en Por encargue) se ignora y un
valor que no existe deja el listado vacío: así un link viejo nunca da error.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, StoreFeatures, get_store_config
from app.core.storage import ObjectStorage
from app.modules.catalog.models import Product, ProductStatus, SaleMode
from app.modules.catalog.seed import (
    CatalogSeed,
    CategorySeed,
    ProductSeed,
    SizeGroupSeed,
    apply_seed,
    load_seed,
)
from tests.conftest import FIXTURES

Params = dict[str, str | list[str]]


async def _listing(client: httpx.AsyncClient, params: Params) -> dict[str, Any]:
    response = await client.get("/products", params=params)
    assert response.status_code == 200, response.text
    listing: dict[str, Any] = response.json()
    return listing


async def _slugs(client: httpx.AsyncClient, params: Params) -> list[str]:
    return [p["slug"] for p in (await _listing(client, params))["items"]]


def _with_features(app: FastAPI, settings: Settings, **features: bool) -> None:
    """Cambia las funciones de la tienda para este test."""
    current = settings.store_config.features.model_dump()
    store = settings.store_config.model_copy(
        update={"features": StoreFeatures(**(current | features))}
    )
    app.dependency_overrides[get_store_config] = lambda: store


# --- Categoría ----------------------------------------------------------------


async def test_category_filter_keeps_products_of_that_category(
    client: httpx.AsyncClient, seeded: None
) -> None:
    slugs = await _slugs(client, {"section": "stock", "category": "remeras"})

    assert slugs == ["remera-basica", "remera-completa"]


async def test_level_one_category_includes_its_children(
    client: httpx.AsyncClient, seeded: None
) -> None:
    # Abrigos tiene dos hijas: Buzos y Camperas.
    slugs = await _slugs(client, {"section": "on_order", "category": "abrigos"})

    assert slugs == ["buzo-a-pedido", "buzo-agotado", "campera-a-pedido"]


async def test_level_two_category_keeps_only_its_products(
    client: httpx.AsyncClient, seeded: None
) -> None:
    slugs = await _slugs(client, {"section": "on_order", "category": "buzos"})

    assert slugs == ["buzo-a-pedido", "buzo-agotado"]


async def test_values_of_one_filter_add_up(client: httpx.AsyncClient, seeded: None) -> None:
    slugs = await _slugs(client, {"section": "stock", "category": ["remeras", "accesorios"]})

    assert slugs == ["remera-basica", "remera-completa", "gorra-en-stock"]


async def test_different_filters_intersect(client: httpx.AsyncClient, seeded: None) -> None:
    slugs = await _slugs(
        client, {"section": "stock", "category": "remeras", "collection": "marca-b"}
    )

    assert slugs == ["remera-completa"]


# --- Etiqueta, colección y versión --------------------------------------------


async def test_tag_filter_with_several_tags(client: httpx.AsyncClient, seeded: None) -> None:
    assert await _slugs(client, {"section": "on_order", "tag": "arquero"}) == ["campera-a-pedido"]
    assert await _slugs(client, {"section": "on_order", "tag": ["titular", "arquero"]}) == [
        "buzo-a-pedido",
        "campera-a-pedido",
    ]


async def test_collection_filter(client: httpx.AsyncClient, seeded: None) -> None:
    slugs = await _slugs(client, {"section": "on_order", "collection": "marca-a"})

    assert slugs == ["remera-agotada", "campera-a-pedido"]


async def test_collection_filter_is_ignored_when_collections_are_off(
    app: FastAPI, client: httpx.AsyncClient, settings: Settings, seeded: None
) -> None:
    _with_features(app, settings, collections=False)

    slugs = await _slugs(client, {"section": "on_order", "collection": "marca-a"})

    assert slugs == [
        "buzo-a-pedido",
        "remera-agotada",
        "buzo-agotado",
        "gorra-a-pedido",
        "campera-a-pedido",
    ]


async def test_version_filter_when_versions_are_on(
    app: FastAPI, client: httpx.AsyncClient, settings: Settings, seeded: None
) -> None:
    _with_features(app, settings, versions=True)

    assert await _slugs(client, {"section": "on_order", "version": "clasica"}) == [
        "campera-a-pedido"
    ]
    assert await _slugs(client, {"section": "on_order", "version": ["clasica", "moderna"]}) == [
        "buzo-a-pedido",
        "campera-a-pedido",
    ]


async def test_version_filter_is_ignored_when_versions_are_off(
    client: httpx.AsyncClient, seeded: None
) -> None:
    # La tienda de prueba tiene las versiones apagadas.
    slugs = await _slugs(client, {"section": "stock", "version": "clasica"})

    assert slugs == ["remera-basica", "remera-completa", "campera-en-stock", "gorra-en-stock"]


async def test_unknown_value_gives_an_empty_listing(
    client: httpx.AsyncClient, seeded: None
) -> None:
    listing = await _listing(client, {"section": "stock", "category": "no-existe"})

    assert listing["items"] == []


# --- Talle ----------------------------------------------------------------------


async def test_size_filter_keeps_products_with_that_size_available(
    client: httpx.AsyncClient, seeded: None
) -> None:
    # remera-basica tiene M sin stock y campera-en-stock, XL sin stock.
    assert await _slugs(client, {"section": "stock", "size": "M"}) == ["remera-completa"]
    assert await _slugs(client, {"section": "stock", "size": "XL"}) == ["remera-completa"]
    assert await _slugs(client, {"section": "stock", "size": ["L", "Único"]}) == [
        "remera-basica",
        "remera-completa",
        "campera-en-stock",
        "gorra-en-stock",
    ]


async def test_size_filter_is_ignored_on_order(client: httpx.AsyncClient, seeded: None) -> None:
    slugs = await _slugs(client, {"section": "on_order", "size": "M"})

    assert slugs == [
        "buzo-a-pedido",
        "remera-agotada",
        "buzo-agotado",
        "gorra-a-pedido",
        "campera-a-pedido",
    ]


async def test_size_filter_matches_the_label_in_every_size_group(
    client: httpx.AsyncClient,
    settings: Settings,
    db_session: AsyncSession,
    storage: ObjectStorage,
    seeded: None,
) -> None:
    kids = CatalogSeed(
        sizes=[SizeGroupSeed(group="ninos", labels=["M"])],
        categories=[CategorySeed(name="Niños", slug="ninos", size_group="ninos")],
        collections=load_seed(FIXTURES / "seed.toml").collections,
        products=[
            ProductSeed(
                slug="remera-ninos",
                name="Remera de niños",
                category="ninos",
                collection="marca-a",
                sale_mode=SaleMode.STOCK,
                status=ProductStatus.PUBLISHED,
                price=1000000,
                sizes={"M": True},
            )
        ],
    )
    await apply_seed(db_session, kids, settings.store_config, storage)

    slugs = await _slugs(client, {"section": "stock", "size": "M"})

    assert sorted(slugs) == ["remera-completa", "remera-ninos"]


async def test_size_filter_leaves_out_sold_out_products_in_stock(
    app: FastAPI, client: httpx.AsyncClient, settings: Settings, seeded: None
) -> None:
    # Sin encargues, remera-agotada sigue en En stock, pero no tiene ningún talle disponible.
    _with_features(app, settings, on_order=False)

    slugs = await _slugs(client, {"section": "stock", "size": "S"})

    assert slugs == ["remera-basica", "remera-completa"]


# --- Orden ----------------------------------------------------------------------


async def test_default_sort_is_the_manual_order(client: httpx.AsyncClient, seeded: None) -> None:
    default = await _slugs(client, {"section": "stock"})
    manual = await _slugs(client, {"section": "stock", "sort": "manual"})

    assert (
        default
        == manual
        == [
            "remera-basica",
            "remera-completa",
            "campera-en-stock",
            "gorra-en-stock",
        ]
    )


async def _set(db_session: AsyncSession, slug: str, **values: Any) -> None:
    await db_session.execute(update(Product).where(Product.slug == slug).values(**values))


async def test_manual_order_puts_the_newest_first_on_a_tie(
    client: httpx.AsyncClient, db_session: AsyncSession, seeded: None
) -> None:
    now = datetime.now(UTC)
    await _set(db_session, "remera-basica", sort_order=0, created_at=now - timedelta(days=2))
    await _set(db_session, "remera-completa", sort_order=0, created_at=now - timedelta(days=1))

    slugs = await _slugs(client, {"section": "stock", "sort": "manual"})

    assert slugs[:2] == ["remera-completa", "remera-basica"]


async def test_newest_sort(
    client: httpx.AsyncClient, db_session: AsyncSession, seeded: None
) -> None:
    now = datetime.now(UTC)
    for days, slug in enumerate(
        ["gorra-en-stock", "remera-basica", "campera-en-stock", "remera-completa"]
    ):
        await _set(db_session, slug, created_at=now - timedelta(days=days))

    slugs = await _slugs(client, {"section": "stock", "sort": "newest"})

    assert slugs == ["gorra-en-stock", "remera-basica", "campera-en-stock", "remera-completa"]


async def test_price_sorts(client: httpx.AsyncClient, seeded: None) -> None:
    cheapest_first = ["gorra-en-stock", "remera-basica", "remera-completa", "campera-en-stock"]

    assert await _slugs(client, {"section": "stock", "sort": "price_asc"}) == cheapest_first
    assert await _slugs(client, {"section": "stock", "sort": "price_desc"}) == list(
        reversed(cheapest_first)
    )


async def test_price_sorts_break_ties_in_a_stable_way(
    client: httpx.AsyncClient, db_session: AsyncSession, seeded: None
) -> None:
    # Mismo precio: desempata el orden de carga (el primero cargado va primero en
    # menor precio y último en mayor precio), así la paginación nunca repite ni saltea.
    await _set(db_session, "remera-completa", price=1999900)

    ascending = await _slugs(client, {"section": "stock", "sort": "price_asc"})
    descending = await _slugs(client, {"section": "stock", "sort": "price_desc"})

    assert ascending[1:3] == ["remera-basica", "remera-completa"]
    assert descending[1:3] == ["remera-completa", "remera-basica"]


async def test_unknown_sort_is_rejected(client: httpx.AsyncClient, seeded: None) -> None:
    response = await client.get("/products", params={"sort": "featured"})

    assert response.status_code == 422


@pytest.mark.parametrize("sort", ["manual", "newest", "price_asc", "price_desc"])
async def test_every_sort_keeps_the_filters(
    client: httpx.AsyncClient, seeded: None, sort: str
) -> None:
    slugs = await _slugs(client, {"section": "stock", "category": "remeras", "sort": sort})

    assert sorted(slugs) == ["remera-basica", "remera-completa"]
