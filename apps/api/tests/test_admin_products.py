"""Listado de productos del admin: GET /admin/products con búsqueda, filtro y página.

Trae todos los estados (borradores, ocultos y archivados, que el público no ve), con
la sección y la disponibilidad calculadas con la regla del catálogo público. «Todos»
deja afuera a los archivados.
"""

from typing import Any

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, StoreFeatures, get_store_config
from app.modules.auth.service import create_admin

EMAIL = "admin@tienda.test"
PASSWORD = "una-clave-larga"

Params = dict[str, str | int]

# Los productos del seed de fixtures, por nombre (ver tests/fixtures/seed.toml).
STOCK = {"Remera básica", "Remera completa", "Campera en stock", "Gorra en stock"}
ON_ORDER = {"Buzo a pedido", "Gorra a pedido", "Campera a pedido"}
SOLD_OUT = {"Remera agotada", "Buzo agotado"}
DRAFT = {"Remera en borrador"}
HIDDEN = {"Remera oculta"}
ARCHIVED = {"Buzo archivado"}


@pytest.fixture
async def admin(client: httpx.AsyncClient, db_session: AsyncSession) -> None:
    """Una sesión de admin abierta en el cliente."""
    await create_admin(db_session, EMAIL, PASSWORD)
    response = await client.post(
        "/admin/session",
        json={"email": EMAIL, "password": PASSWORD, "remember": False},
        headers={"X-Requested-With": "fetch"},
    )
    assert response.status_code == 200, response.text


async def _listing(client: httpx.AsyncClient, params: Params | None = None) -> dict[str, Any]:
    response = await client.get("/admin/products", params=params or {})
    assert response.status_code == 200, response.text
    listing: dict[str, Any] = response.json()
    return listing


async def _names(client: httpx.AsyncClient, params: Params) -> set[str]:
    listing = await _listing(client, params | {"limit": 100})
    names = {p["name"] for p in listing["items"]}
    assert listing["total"] == len(names)
    return names


async def _item(client: httpx.AsyncClient, name: str) -> dict[str, Any]:
    items = (await _listing(client, {"filter": "all", "limit": 100}))["items"]
    item: dict[str, Any] = next(p for p in items if p["name"] == name)
    return item


# --- Acceso -------------------------------------------------------------------


async def test_without_a_session_the_listing_is_401(
    client: httpx.AsyncClient, seeded: None
) -> None:
    response = await client.get("/admin/products")

    assert response.status_code == 401


# --- Filtros ------------------------------------------------------------------


async def test_all_has_every_status_but_archived(
    client: httpx.AsyncClient, seeded: None, admin: None
) -> None:
    expected = STOCK | ON_ORDER | SOLD_OUT | DRAFT | HIDDEN

    assert await _names(client, {}) == expected
    assert await _names(client, {"filter": "all"}) == expected


@pytest.mark.parametrize(
    ("product_filter", "expected"),
    [
        # Los de sección siguen la regla pública: un agotado está en Por encargue.
        # Borradores y ocultos también tienen sección.
        ("stock", STOCK | DRAFT | HIDDEN),
        ("on_order", ON_ORDER | SOLD_OUT),
        ("sold_out", SOLD_OUT),
        ("draft", DRAFT),
        ("hidden", HIDDEN),
        ("archived", ARCHIVED),
    ],
)
async def test_each_filter(
    client: httpx.AsyncClient,
    seeded: None,
    admin: None,
    product_filter: str,
    expected: set[str],
) -> None:
    assert await _names(client, {"filter": product_filter}) == expected


async def test_with_on_order_off_a_sold_out_product_stays_in_stock(
    app: FastAPI, settings: Settings, client: httpx.AsyncClient, seeded: None, admin: None
) -> None:
    features = StoreFeatures(**(settings.store_config.features.model_dump() | {"on_order": False}))
    store = settings.store_config.model_copy(update={"features": features})
    app.dependency_overrides[get_store_config] = lambda: store

    assert await _names(client, {"filter": "stock"}) == STOCK | SOLD_OUT | DRAFT | HIDDEN
    assert await _names(client, {"filter": "sold_out"}) == SOLD_OUT
    sold_out = await _item(client, "Remera agotada")
    assert sold_out["section"] == "stock"
    assert sold_out["availability"] == "sold_out"


async def test_an_unknown_filter_is_rejected(
    client: httpx.AsyncClient, seeded: None, admin: None
) -> None:
    response = await client.get("/admin/products", params={"filter": "vendidos"})

    assert response.status_code == 422


# --- Lo que trae cada fila ----------------------------------------------------


async def test_a_row_has_status_featured_section_and_availability(
    client: httpx.AsyncClient, seeded: None, admin: None
) -> None:
    hidden = await _item(client, "Remera oculta")

    assert hidden["status"] == "hidden"
    assert hidden["featured"] is True
    assert hidden["section"] == "stock"
    assert hidden["availability"] == "in_stock"
    assert hidden["code"].startswith("TP-")
    assert hidden["currency"] == "USD"
    assert hidden["cover"] is None or hidden["cover"]["thumb"].startswith("/media/")


async def test_a_sold_out_product_shows_its_own_sizes_out_of_stock(
    client: httpx.AsyncClient, seeded: None, admin: None
) -> None:
    sold_out = await _item(client, "Remera agotada")

    assert sold_out["status"] == "published"
    assert sold_out["section"] == "on_order"
    assert sold_out["availability"] == "sold_out_on_order"
    assert sold_out["sizes"] == [
        {"label": "S", "status": "out_of_stock"},
        {"label": "M", "status": "out_of_stock"},
    ]


async def test_stock_sizes_keep_the_group_order_and_their_status(
    client: httpx.AsyncClient, seeded: None, admin: None
) -> None:
    product = await _item(client, "Remera básica")

    assert product["sizes"] == [
        {"label": "S", "status": "in_stock"},
        {"label": "M", "status": "out_of_stock"},
        {"label": "L", "status": "in_stock"},
    ]


async def test_an_on_order_product_lists_every_size_of_its_group(
    client: httpx.AsyncClient, seeded: None, admin: None
) -> None:
    public = await client.get("/products", params={"q": "Buzo a pedido"})
    code = public.json()["items"][0]["code"]
    detail = (await client.get(f"/products/{code}")).json()

    product = await _item(client, "Buzo a pedido")

    assert product["availability"] == "on_order"
    assert [s["label"] for s in product["sizes"]] == [s["label"] for s in detail["sizes"]]
    assert {s["status"] for s in product["sizes"]} == {"on_order"}


async def test_section_and_availability_match_the_public_listing(
    client: httpx.AsyncClient, seeded: None, admin: None
) -> None:
    public = (await client.get("/products", params={"limit": 100})).json()["items"]
    admin_items = {p["code"]: p for p in (await _listing(client, {"limit": 100}))["items"]}

    assert public
    for product in public:
        row = admin_items[product["code"]]
        assert (row["section"], row["availability"]) == (
            product["section"],
            product["availability"],
        )


# --- Búsqueda -----------------------------------------------------------------


async def test_search_by_name_finds_every_status(
    client: httpx.AsyncClient, seeded: None, admin: None
) -> None:
    assert await _names(client, {"q": "remera"}) == {
        "Remera básica",
        "Remera completa",
        "Remera agotada",
        "Remera en borrador",
        "Remera oculta",
    }
    assert await _names(client, {"q": "BÁSICA"}) == {"Remera básica"}


async def test_search_by_code(client: httpx.AsyncClient, seeded: None, admin: None) -> None:
    code = (await _item(client, "Remera en borrador"))["code"]

    assert await _names(client, {"q": code}) == {"Remera en borrador"}
    assert await _names(client, {"q": code.lower()}) == {"Remera en borrador"}


async def test_search_combines_with_the_filter(
    client: httpx.AsyncClient, seeded: None, admin: None
) -> None:
    assert await _names(client, {"q": "buzo"}) == {"Buzo a pedido", "Buzo agotado"}
    assert await _names(client, {"q": "buzo", "filter": "archived"}) == {"Buzo archivado"}
    assert await _names(client, {"q": "remera", "filter": "draft"}) == {"Remera en borrador"}
    assert await _names(client, {"q": "gorra", "filter": "sold_out"}) == set()


# --- Paginación ---------------------------------------------------------------


async def test_pages_cover_the_listing_once_and_in_order(
    client: httpx.AsyncClient, seeded: None, admin: None
) -> None:
    whole = [p["code"] for p in (await _listing(client, {"limit": 100}))["items"]]
    codes: list[str] = []
    while True:
        page = await _listing(client, {"limit": 5, "offset": len(codes)})
        assert page["total"] == len(whole)
        codes += [p["code"] for p in page["items"]]
        if not page["has_more"]:
            break
        assert page["items"], "has_more con una página vacía"

    assert codes == whole
    assert len(set(codes)) == len(codes)


async def test_newest_products_come_first(
    client: httpx.AsyncClient, seeded: None, admin: None
) -> None:
    # Todo el seed se carga en el mismo instante: a igual fecha, el último cargado primero.
    codes = [p["code"] for p in (await _listing(client, {"limit": 100}))["items"]]

    assert codes == sorted(codes, key=lambda code: int(code.split("-")[1]), reverse=True)


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 101}, {"offset": -1}])
async def test_out_of_range_pagination_is_rejected(
    client: httpx.AsyncClient, seeded: None, admin: None, params: Params
) -> None:
    response = await client.get("/admin/products", params=params)

    assert response.status_code == 422
