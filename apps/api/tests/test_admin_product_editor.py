"""Editor de producto del admin: GET /admin/catalog-options, POST /admin/products y
GET/PATCH /admin/products/{code}.

El código lo asigna la API al crear y no cambia. Un encargue no tiene talles propios;
al pasar a stock, o al cambiar de categoría a otro grupo de talles siendo de stock,
quedan todos los talles del grupo, disponibles. Los errores son por campo (``loc``).
"""

from typing import Any

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.service import create_admin
from app.modules.catalog.models import Category, Collection, Size

EMAIL = "admin@tienda.test"
PASSWORD = "una-clave-larga"
CSRF = {"X-Requested-With": "fetch"}

# Del seed de fixtures (tests/fixtures/seed.toml y store.toml).
PREFIX = "TP-"
CLOTHES = ["S", "M", "L", "XL"]  # grupo «prenda»: remeras, abrigos, buzos, camperas


@pytest.fixture
async def admin(client: httpx.AsyncClient, db_session: AsyncSession) -> None:
    """Una sesión de admin abierta en el cliente."""
    await create_admin(db_session, EMAIL, PASSWORD)
    response = await client.post(
        "/admin/session",
        json={"email": EMAIL, "password": PASSWORD, "remember": False},
        headers=CSRF,
    )
    assert response.status_code == 200, response.text


async def _code(client: httpx.AsyncClient, name: str) -> str:
    response = await client.get("/admin/products", params={"q": name, "filter": "all"})
    assert response.status_code == 200, response.text
    code: str = next(p["code"] for p in response.json()["items"] if p["name"] == name)
    return code


async def _create(client: httpx.AsyncClient, **body: Any) -> httpx.Response:
    return await client.post("/admin/products", json=body, headers=CSRF)


async def _created(client: httpx.AsyncClient, **body: Any) -> dict[str, Any]:
    response = await _create(client, **body)
    assert response.status_code == 201, response.text
    product: dict[str, Any] = response.json()
    return product


async def _patch(client: httpx.AsyncClient, code: str, /, **body: Any) -> httpx.Response:
    return await client.patch(f"/admin/products/{code}", json=body, headers=CSRF)


async def _patched(client: httpx.AsyncClient, code: str, /, **body: Any) -> dict[str, Any]:
    response = await _patch(client, code, **body)
    assert response.status_code == 200, response.text
    product: dict[str, Any] = response.json()
    return product


async def _get(client: httpx.AsyncClient, code: str) -> dict[str, Any]:
    response = await client.get(f"/admin/products/{code}")
    assert response.status_code == 200, response.text
    product: dict[str, Any] = response.json()
    return product


def _sizes(product: dict[str, Any]) -> dict[str, bool]:
    return {size["label"]: size["in_stock"] for size in product["sizes"]}


def _error_locs(response: httpx.Response) -> list[list[str | int]]:
    assert response.status_code == 422, response.text
    return [error["loc"] for error in response.json()["detail"]]


# --- Acceso -------------------------------------------------------------------


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/admin/catalog-options"),
        ("POST", "/admin/products"),
        ("GET", "/admin/products/TP-001"),
        ("PATCH", "/admin/products/TP-001"),
    ],
)
async def test_without_a_session_it_is_401(
    client: httpx.AsyncClient, seeded: None, method: str, path: str
) -> None:
    body = {"name": "Algo", "category": "remeras"} if method != "GET" else None
    response = await client.request(method, path, json=body, headers=CSRF)

    assert response.status_code == 401


async def test_writing_without_the_csrf_header_is_403(
    client: httpx.AsyncClient, seeded: None, admin: None
) -> None:
    response = await client.post("/admin/products", json={"name": "Algo", "category": "remeras"})

    assert response.status_code == 403


# --- Opciones -----------------------------------------------------------------


async def test_catalog_options(client: httpx.AsyncClient, seeded: None, admin: None) -> None:
    response = await client.get("/admin/catalog-options")

    assert response.status_code == 200, response.text
    options = response.json()
    assert [(c["slug"], c["parent"], c["size_group"]) for c in options["categories"]] == [
        ("remeras", None, "prenda"),
        ("abrigos", None, "prenda"),
        ("buzos", "abrigos", "prenda"),
        ("camperas", "abrigos", "prenda"),
        ("accesorios", None, "accesorio"),
    ]
    assert [c["slug"] for c in options["collections"]] == ["marca-a", "marca-b"]
    assert options["default_collection"] == "marca-a"
    assert [v["slug"] for v in options["versions"]] == ["clasica", "moderna"]
    assert [t["slug"] for t in options["tags"]] == ["titular", "alternativa", "arquero"]
    assert options["sizes"] == {"prenda": CLOTHES, "accesorio": ["Único"]}
    assert set(options["features"]) == {"collections", "versions", "on_order"}


# --- Crear --------------------------------------------------------------------


async def test_create_assigns_a_code_and_starts_as_a_draft(
    client: httpx.AsyncClient, seeded: None, admin: None
) -> None:
    first = await _created(client, name="  Remera nueva  ", category="remeras")
    second = await _created(client, name="Otra remera", category="remeras")

    assert first["code"].startswith(PREFIX)
    assert int(second["code"].removeprefix(PREFIX)) == int(first["code"].removeprefix(PREFIX)) + 1
    assert first["status"] == "draft"
    assert first["name"] == "Remera nueva"
    # Sin más datos: de stock con todos los talles disponibles, precio 0 y la colección
    # por defecto.
    assert first["sale_mode"] == "stock"
    assert _sizes(first) == dict.fromkeys(CLOTHES, True)
    assert first["price"] == 0
    assert first["collection"] == "marca-a"
    assert await _get(client, first["code"].lower()) == first


async def test_create_with_every_field(
    client: httpx.AsyncClient, seeded: None, admin: None
) -> None:
    product = await _created(
        client,
        name="Campera completa",
        category="camperas",
        collection="marca-b",
        version="moderna",
        season="2025/26",
        tags=["arquero", "titular"],
        description="Tela técnica.",
        price=4500000,
        sale_mode="stock",
        sizes=[{"label": "M", "in_stock": False}],
    )

    assert product | {"code": None} == {
        "code": None,
        "name": "Campera completa",
        "status": "draft",
        "category": "camperas",
        "collection": "marca-b",
        "version": "moderna",
        "season": "2025/26",
        # En el orden de las opciones.
        "tags": ["titular", "arquero"],
        "description": "Tela técnica.",
        "price": 4500000,
        "currency": "USD",
        "sale_mode": "stock",
        "sizes": [
            {"label": "S", "in_stock": True},
            {"label": "M", "in_stock": False},
            {"label": "L", "in_stock": True},
            {"label": "XL", "in_stock": True},
        ],
    }


async def test_create_on_order_has_no_sizes(
    client: httpx.AsyncClient, seeded: None, admin: None
) -> None:
    product = await _created(client, name="Buzo nuevo", category="buzos", sale_mode="on_order")

    assert product["sale_mode"] == "on_order"
    assert product["sizes"] == []


async def test_a_new_product_shows_up_in_the_admin_listing(
    client: httpx.AsyncClient, seeded: None, admin: None
) -> None:
    product = await _created(client, name="Gorra recién creada", category="accesorios")

    response = await client.get("/admin/products", params={"filter": "draft"})
    item = next(p for p in response.json()["items"] if p["code"] == product["code"])
    assert item["name"] == "Gorra recién creada"
    assert item["sizes"] == [{"label": "Único", "status": "in_stock"}]


async def test_with_a_single_collection_it_is_the_default(
    client: httpx.AsyncClient, db_session: AsyncSession, admin: None
) -> None:
    db_session.add_all(
        [
            Category(name="Remeras", slug="remeras", size_group="prenda"),
            Size(label="Único", size_group="prenda"),
            Collection(name="La única", slug="la-unica", is_default=False),
        ]
    )
    await db_session.flush()

    product = await _created(client, name="Remera", category="remeras")
    options = (await client.get("/admin/catalog-options")).json()

    assert product["collection"] == "la-unica"
    assert options["default_collection"] == "la-unica"


# --- Validaciones -------------------------------------------------------------


async def test_create_needs_name_and_category(
    client: httpx.AsyncClient, seeded: None, admin: None
) -> None:
    response = await _create(client, name="   ", category="")

    assert _error_locs(response) == [["body", "name"], ["body", "category"]]


@pytest.mark.parametrize(
    ("body", "loc"),
    [
        ({"name": "x" * 201}, ["body", "name"]),
        ({"name": None}, ["body", "name"]),
        ({"category": None}, ["body", "category"]),
        ({"category": "no-existe"}, ["body", "category"]),
        ({"collection": "no-existe"}, ["body", "collection"]),
        ({"version": "no-existe"}, ["body", "version"]),
        ({"tags": ["titular", "no-existe"]}, ["body", "tags", 1]),
        ({"season": "x" * 41}, ["body", "season"]),
        ({"description": "x" * 5001}, ["body", "description"]),
        ({"price": -1}, ["body", "price"]),
        ({"price": "mucho"}, ["body", "price"]),
        ({"price": None}, ["body", "price"]),
        ({"sale_mode": "regalado"}, ["body", "sale_mode"]),
        ({"sizes": [{"label": "Único", "in_stock": True}]}, ["body", "sizes", 0, "label"]),
        ({"code": "TP-999"}, ["body", "code"]),
    ],
)
async def test_each_invalid_field_has_its_error(
    client: httpx.AsyncClient,
    seeded: None,
    admin: None,
    body: dict[str, Any],
    loc: list[str | int],
) -> None:
    code = await _code(client, "Remera básica")
    before = await _get(client, code)

    response = await _patch(client, code, **body)

    assert _error_locs(response) == [loc]
    assert await _get(client, code) == before


async def test_several_problems_come_together(
    client: httpx.AsyncClient, seeded: None, admin: None
) -> None:
    response = await _create(
        client, name="Algo", category="no-existe", collection="tampoco", tags=["nada"]
    )

    assert _error_locs(response) == [
        ["body", "category"],
        ["body", "collection"],
        ["body", "tags", 0],
    ]


async def test_an_invalid_create_does_not_use_up_a_code(
    client: httpx.AsyncClient, seeded: None, admin: None
) -> None:
    first = await _created(client, name="Una", category="remeras")
    await _create(client, name="Mala", category="no-existe")
    second = await _created(client, name="Otra", category="remeras")

    assert int(second["code"].removeprefix(PREFIX)) == int(first["code"].removeprefix(PREFIX)) + 1


async def test_an_unknown_code_is_404(client: httpx.AsyncClient, seeded: None, admin: None) -> None:
    assert (await client.get("/admin/products/TP-999")).status_code == 404
    assert (await _patch(client, "TP-999", name="Algo")).status_code == 404


# --- Editar -------------------------------------------------------------------


async def test_edit_each_field(client: httpx.AsyncClient, seeded: None, admin: None) -> None:
    code = await _code(client, "Remera básica")

    product = await _patched(
        client,
        code.lower(),
        name="Remera básica 2026",
        collection="marca-b",
        version="moderna",
        season="2026",
        tags=["alternativa"],
        description="Nueva descripción.",
        price=2100000,
    )

    assert product["code"] == code
    assert product["name"] == "Remera básica 2026"
    assert product["collection"] == "marca-b"
    assert product["version"] == "moderna"
    assert product["season"] == "2026"
    assert product["tags"] == ["alternativa"]
    assert product["description"] == "Nueva descripción."
    assert product["price"] == 2100000
    assert await _get(client, code) == product
    # El catálogo público ve el cambio (sigue publicado).
    public = (await client.get(f"/products/{code}")).json()
    assert public["name"] == "Remera básica 2026"
    assert public["price"] == 2100000


async def test_what_is_not_sent_does_not_change(
    client: httpx.AsyncClient, seeded: None, admin: None
) -> None:
    code = await _code(client, "Remera básica")
    before = await _get(client, code)

    after = await _patched(client, code, price=100)

    assert after == before | {"price": 100}


async def test_null_or_blank_clears_the_optional_fields(
    client: httpx.AsyncClient, seeded: None, admin: None
) -> None:
    code = await _code(client, "Remera básica")
    await _patched(client, code, season="2025", description="Algo")

    product = await _patched(client, code, version=None, season="  ", description=None, tags=[])

    assert product["version"] is None
    assert product["season"] is None
    assert product["description"] is None
    assert product["tags"] == []


async def test_the_code_never_changes(client: httpx.AsyncClient, seeded: None, admin: None) -> None:
    code = await _code(client, "Remera básica")

    await _patched(client, code, name="Otro nombre", category="camperas")

    assert (await _get(client, code))["code"] == code


async def test_mark_sizes_in_stock_or_out_of_stock(
    client: httpx.AsyncClient, seeded: None, admin: None
) -> None:
    code = await _code(client, "Remera básica")  # S, M sin stock y L

    product = await _patched(
        client,
        code,
        sizes=[{"label": "S", "in_stock": False}, {"label": "M", "in_stock": True}],
    )

    assert _sizes(product) == {"S": False, "M": True, "L": True}


async def test_marking_a_size_of_the_group_it_did_not_have_adds_it(
    client: httpx.AsyncClient, seeded: None, admin: None
) -> None:
    code = await _code(client, "Remera básica")

    product = await _patched(client, code, sizes=[{"label": "XL", "in_stock": True}])

    assert _sizes(product) == {"S": True, "M": False, "L": True, "XL": True}


# --- Talles al cambiar de modo y de grupo -------------------------------------


async def test_to_on_order_deletes_the_sizes(
    client: httpx.AsyncClient, seeded: None, admin: None
) -> None:
    code = await _code(client, "Remera básica")

    product = await _patched(client, code, sale_mode="on_order")

    assert product["sizes"] == []
    # En el detalle público, un encargue ofrece todos los talles del grupo.
    public = (await client.get(f"/products/{code}")).json()
    assert [size["label"] for size in public["sizes"]] == CLOTHES
    assert {size["status"] for size in public["sizes"]} == {"on_order"}


async def test_to_stock_creates_every_size_of_the_group_available(
    client: httpx.AsyncClient, seeded: None, admin: None
) -> None:
    code = await _code(client, "Buzo a pedido")

    product = await _patched(client, code, sale_mode="stock")

    assert _sizes(product) == dict.fromkeys(CLOTHES, True)


async def test_to_stock_with_sizes_applies_them_after_creating_the_group(
    client: httpx.AsyncClient, seeded: None, admin: None
) -> None:
    code = await _code(client, "Buzo a pedido")

    product = await _patched(
        client, code, sale_mode="stock", sizes=[{"label": "XL", "in_stock": False}]
    )

    assert _sizes(product) == {"S": True, "M": True, "L": True, "XL": False}


async def test_on_order_with_sizes_is_rejected(
    client: httpx.AsyncClient, seeded: None, admin: None
) -> None:
    on_order = await _code(client, "Buzo a pedido")
    stock = await _code(client, "Remera básica")

    already = await _patch(client, on_order, sizes=[{"label": "S", "in_stock": True}])
    switching = await _patch(
        client, stock, sale_mode="on_order", sizes=[{"label": "S", "in_stock": True}]
    )
    creating = await _create(
        client,
        name="Buzo",
        category="buzos",
        sale_mode="on_order",
        sizes=[{"label": "S", "in_stock": True}],
    )

    for response in (already, switching, creating):
        assert _error_locs(response) == [["body", "sizes"]]
        assert response.json()["detail"][0]["type"] == "on_order_with_sizes"
    assert _sizes(await _get(client, stock)) == {"S": True, "M": False, "L": True}


async def test_on_order_with_an_empty_size_list_is_fine(
    client: httpx.AsyncClient, seeded: None, admin: None
) -> None:
    code = await _code(client, "Buzo a pedido")

    product = await _patched(client, code, sizes=[], price=1)

    assert product["sizes"] == []


async def test_changing_to_a_category_of_another_group_redoes_the_sizes(
    client: httpx.AsyncClient, seeded: None, admin: None
) -> None:
    code = await _code(client, "Remera básica")

    product = await _patched(client, code, category="accesorios")

    assert product["category"] == "accesorios"
    assert _sizes(product) == {"Único": True}


async def test_changing_to_a_category_of_the_same_group_keeps_the_sizes(
    client: httpx.AsyncClient, seeded: None, admin: None
) -> None:
    code = await _code(client, "Remera básica")

    product = await _patched(client, code, category="camperas")

    assert _sizes(product) == {"S": True, "M": False, "L": True}


async def test_an_on_order_product_changing_group_stays_without_sizes(
    client: httpx.AsyncClient, seeded: None, admin: None
) -> None:
    code = await _code(client, "Buzo a pedido")

    product = await _patched(client, code, category="accesorios")

    assert product["sizes"] == []


async def test_sizes_are_checked_against_the_new_category(
    client: httpx.AsyncClient, seeded: None, admin: None
) -> None:
    code = await _code(client, "Remera básica")

    ok = await _patched(
        client, code, category="accesorios", sizes=[{"label": "Único", "in_stock": False}]
    )
    wrong = await _patch(
        client, code, category="remeras", sizes=[{"label": "Único", "in_stock": True}]
    )

    assert _sizes(ok) == {"Único": False}
    assert _error_locs(wrong) == [["body", "sizes", 0, "label"]]
