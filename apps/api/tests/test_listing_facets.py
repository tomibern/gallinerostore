"""Facetas del listado: los valores de filtro con resultados en la sección.

Cada faceta se cuenta con los demás filtros, no con el suyo, así el visitante
puede sumar valores (O). Una faceta vacía es un filtro que no se muestra.
"""

from typing import Any

import httpx
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, StoreFeatures, get_store_config
from app.core.storage import ObjectStorage
from app.modules.catalog.models import ProductStatus, SaleMode
from app.modules.catalog.seed import (
    CatalogSeed,
    CategorySeed,
    CollectionSeed,
    ProductSeed,
    SizeGroupSeed,
    apply_seed,
)

Params = dict[str, str | list[str]]


async def _facets(client: httpx.AsyncClient, params: Params) -> dict[str, Any]:
    response = await client.get("/products", params=params)
    assert response.status_code == 200, response.text
    facets: dict[str, Any] = response.json()["facets"]
    return facets


def _counts(values: list[dict[str, Any]]) -> list[tuple[str, int]]:
    return [(v["value"], v["count"]) for v in values]


def _with_features(app: FastAPI, settings: Settings, **features: bool) -> None:
    current = settings.store_config.features.model_dump()
    store = settings.store_config.model_copy(
        update={"features": StoreFeatures(**(current | features))}
    )
    app.dependency_overrides[get_store_config] = lambda: store


async def test_stock_facets_list_only_values_with_results(
    client: httpx.AsyncClient, seeded: None
) -> None:
    facets = await _facets(client, {"section": "stock"})

    # Buzos no tiene nada en stock; Abrigos cuenta su hija Camperas.
    assert facets["categories"] == [
        {"value": "remeras", "name": "Remeras", "count": 2, "parent": None},
        {"value": "abrigos", "name": "Abrigos", "count": 1, "parent": None},
        {"value": "camperas", "name": "Camperas", "count": 1, "parent": "abrigos"},
        {"value": "accesorios", "name": "Accesorios", "count": 1, "parent": None},
    ]
    assert _counts(facets["collections"]) == [("marca-a", 3), ("marca-b", 1)]
    assert _counts(facets["tags"]) == [("titular", 1), ("alternativa", 1), ("arquero", 1)]
    # Solo talles disponibles: M solo en remera-completa, XL no en campera-en-stock.
    assert _counts(facets["sizes"]) == [("S", 2), ("M", 1), ("L", 3), ("XL", 1), ("Único", 1)]


async def test_on_order_facets_have_no_sizes(client: httpx.AsyncClient, seeded: None) -> None:
    facets = await _facets(client, {"section": "on_order"})

    assert facets["sizes"] == []
    assert _counts(facets["categories"]) == [
        ("remeras", 1),
        ("abrigos", 3),
        ("buzos", 2),
        ("camperas", 1),
        ("accesorios", 1),
    ]
    assert _counts(facets["tags"]) == [("titular", 1), ("alternativa", 1), ("arquero", 1)]


async def test_each_facet_ignores_its_own_filter_but_not_the_others(
    client: httpx.AsyncClient, seeded: None
) -> None:
    facets = await _facets(client, {"section": "stock", "collection": "marca-b"})

    # La faceta de colección sigue mostrando las dos, para poder sumar marca-a.
    assert _counts(facets["collections"]) == [("marca-a", 3), ("marca-b", 1)]
    # Las demás ya se cruzan con marca-b (solo remera-completa).
    assert _counts(facets["categories"]) == [("remeras", 1)]
    assert _counts(facets["sizes"]) == [("S", 1), ("M", 1), ("L", 1), ("XL", 1)]


async def test_version_facet_follows_the_feature(
    app: FastAPI, client: httpx.AsyncClient, settings: Settings, seeded: None
) -> None:
    # La tienda de prueba tiene las versiones apagadas.
    assert (await _facets(client, {"section": "stock"}))["versions"] == []

    _with_features(app, settings, versions=True)
    facets = await _facets(client, {"section": "stock"})

    assert facets["versions"] == [
        {"value": "clasica", "name": "Clásica", "count": 2},
        {"value": "moderna", "name": "Moderna", "count": 1},
    ]


async def test_collection_facet_is_hidden_when_collections_are_off(
    app: FastAPI, client: httpx.AsyncClient, settings: Settings, seeded: None
) -> None:
    _with_features(app, settings, collections=False)

    assert (await _facets(client, {"section": "stock"}))["collections"] == []


async def test_collection_facet_is_hidden_with_a_single_collection(
    client: httpx.AsyncClient, settings: Settings, db_session: AsyncSession, storage: ObjectStorage
) -> None:
    single = CatalogSeed(
        sizes=[SizeGroupSeed(group="prenda", labels=["M"])],
        categories=[CategorySeed(name="Remeras", slug="remeras", size_group="prenda")],
        collections=[CollectionSeed(name="Única", slug="unica", default=True)],
        products=[
            ProductSeed(
                slug="remera",
                name="Remera",
                category="remeras",
                collection="unica",
                sale_mode=SaleMode.STOCK,
                status=ProductStatus.PUBLISHED,
                price=1000000,
                sizes={"M": True},
            )
        ],
    )
    await apply_seed(db_session, single, settings.store_config, storage)

    assert (await _facets(client, {"section": "stock"}))["collections"] == []


async def test_selected_values_stay_in_their_facet_without_results(
    client: httpx.AsyncClient, seeded: None
) -> None:
    # Ningún producto en stock tiene «arquero» y talle M: sin la fila, el chip para
    # sacar «arquero» desaparecería. Un slug que no existe no se inventa.
    facets = await _facets(
        client, {"section": "stock", "tag": ["arquero", "no-existe"], "size": "M"}
    )

    assert {"value": "arquero", "name": "Arquero", "count": 0} in facets["tags"]
    assert [v["value"] for v in facets["tags"]].count("no-existe") == 0


async def test_selected_category_and_size_stay_without_results(
    client: httpx.AsyncClient, seeded: None
) -> None:
    facets = await _facets(client, {"section": "stock", "category": "camperas", "size": "M"})

    assert {"value": "camperas", "name": "Camperas", "count": 0, "parent": "abrigos"} in facets[
        "categories"
    ]
    facets = await _facets(client, {"section": "stock", "category": "accesorios", "size": "M"})
    assert {"value": "M", "name": "M", "count": 0} in facets["sizes"]
