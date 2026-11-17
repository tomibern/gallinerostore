"""Búsqueda por texto del listado: GET /products con ``q``.

Busca en el nombre y el código sin distinguir mayúsculas ni acentos. Cada palabra
tiene que aparecer (en el nombre o en el código), y la búsqueda se cruza con la
sección, los filtros, el total, las facetas y la paginación.
"""

from typing import Any

import httpx

Params = dict[str, str | list[str]]


async def _listing(client: httpx.AsyncClient, params: Params) -> dict[str, Any]:
    response = await client.get("/products", params=params)
    assert response.status_code == 200, response.text
    listing: dict[str, Any] = response.json()
    return listing


async def _slugs(client: httpx.AsyncClient, params: Params) -> set[str]:
    return {p["slug"] for p in (await _listing(client, params))["items"]}


async def _code(client: httpx.AsyncClient, slug: str) -> str:
    items = (await _listing(client, {"limit": "100"}))["items"]
    code: str = next(p["code"] for p in items if p["slug"] == slug)
    return code


async def test_search_by_partial_name(client: httpx.AsyncClient, seeded: None) -> None:
    slugs = await _slugs(client, {"section": "stock", "q": "reme"})

    assert slugs == {"remera-basica", "remera-completa"}


async def test_search_ignores_case_and_accents(client: httpx.AsyncClient, seeded: None) -> None:
    # El producto se llama «Remera básica».
    assert await _slugs(client, {"q": "BASICA"}) == {"remera-basica"}
    assert await _slugs(client, {"q": "básica"}) == {"remera-basica"}
    assert await _slugs(client, {"q": "Bâsíca"}) == {"remera-basica"}


async def test_search_by_code(client: httpx.AsyncClient, seeded: None) -> None:
    code = await _code(client, "remera-completa")

    assert await _slugs(client, {"q": code}) == {"remera-completa"}
    assert await _slugs(client, {"q": code.lower()}) == {"remera-completa"}


async def test_every_word_has_to_match_in_name_or_code(
    client: httpx.AsyncClient, seeded: None
) -> None:
    code = await _code(client, "buzo-a-pedido")

    assert await _slugs(client, {"q": "comp remera"}) == {"remera-completa"}
    assert await _slugs(client, {"q": f"buzo {code}"}) == {"buzo-a-pedido"}
    assert await _slugs(client, {"q": "remera buzo"}) == set()


async def test_search_combines_with_section_and_filters(
    client: httpx.AsyncClient, seeded: None
) -> None:
    assert await _slugs(client, {"section": "stock", "q": "remera", "tag": "alternativa"}) == {
        "remera-completa"
    }
    # «Buzo agotado» pasa a Por encargue; el de stock no hay.
    assert await _slugs(client, {"section": "stock", "q": "buzo"}) == set()
    assert await _slugs(client, {"section": "on_order", "q": "buzo", "category": "abrigos"}) == {
        "buzo-a-pedido",
        "buzo-agotado",
    }


async def test_search_only_finds_published_products(
    client: httpx.AsyncClient, seeded: None
) -> None:
    # Hay una remera en borrador, una oculta y un buzo archivado.
    assert await _slugs(client, {"q": "borrador"}) == set()
    assert await _slugs(client, {"q": "oculta"}) == set()
    assert await _slugs(client, {"q": "archivado"}) == set()


async def test_total_and_facets_count_only_the_search_results(
    client: httpx.AsyncClient, seeded: None
) -> None:
    listing = await _listing(client, {"section": "stock", "q": "remera"})

    assert listing["total"] == 2
    tags = {tag["value"]: tag["count"] for tag in listing["facets"]["tags"]}
    assert tags == {"titular": 1, "alternativa": 1}
    categories = {c["value"]: c["count"] for c in listing["facets"]["categories"]}
    assert categories == {"remeras": 2}


async def test_search_paginates(client: httpx.AsyncClient, seeded: None) -> None:
    first = await _listing(client, {"q": "remera", "limit": "1"})
    second = await _listing(client, {"q": "remera", "limit": "1", "offset": "1"})

    assert first["has_more"] is True
    assert first["total"] == 3  # básica, completa y agotada
    assert first["items"][0]["code"] != second["items"][0]["code"]


async def test_like_wildcards_are_literal(client: httpx.AsyncClient, seeded: None) -> None:
    assert await _slugs(client, {"q": "%"}) == set()
    assert await _slugs(client, {"q": "_"}) == set()
    assert await _slugs(client, {"q": "\\"}) == set()


async def test_blank_search_does_not_filter(client: httpx.AsyncClient, seeded: None) -> None:
    everything = await _slugs(client, {"section": "stock"})

    assert await _slugs(client, {"section": "stock", "q": ""}) == everything
    assert await _slugs(client, {"section": "stock", "q": "   "}) == everything


async def test_too_long_search_is_rejected(client: httpx.AsyncClient, seeded: None) -> None:
    response = await client.get("/products", params={"q": "a" * 101})

    assert response.status_code == 422
