"""Historia del producto en el detalle: hitos, cifras y dato curioso.

Viene ordenada por tipo (hitos, cifras, dato curioso) y, dentro del tipo, en el
orden en que se cargó. Sin historia, o con ``features.product_story`` apagada,
la lista viene vacía y la tienda no muestra la sección.
"""

from typing import Any

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_store_config
from app.core.storage import ObjectStorage
from app.modules.catalog.seed import SeedError, StoryItemSeed, apply_seed, load_seed
from tests.conftest import FIXTURES


@pytest.fixture
def story_on(app: FastAPI, settings: Settings) -> None:
    """La historia prendida (el fixture de la tienda la tiene apagada)."""
    features = settings.store_config.features.model_copy(update={"product_story": True})
    store = settings.store_config.model_copy(update={"features": features})
    app.dependency_overrides[get_store_config] = lambda: store


async def _story(client: httpx.AsyncClient, slug: str) -> list[dict[str, Any]]:
    items = (await client.get("/products")).json()["items"]
    code = next(p["code"] for p in items if p["slug"] == slug)
    response = await client.get(f"/products/{code.lower()}")
    assert response.status_code == 200
    story: list[dict[str, Any]] = response.json()["story"]
    return story


async def test_story_comes_ordered_by_kind_and_then_by_load_order(
    client: httpx.AsyncClient, seeded: None, story_on: None
) -> None:
    assert await _story(client, "remera-completa") == [
        {
            "kind": "milestone",
            "year": 2001,
            "title": "Primer campeonato",
            "body": "Ganó de visitante.",
        },
        {"kind": "milestone", "year": 1999, "title": "Debut", "body": "Se estrenó en un amistoso."},
        {"kind": "stat", "year": None, "title": "3", "body": "títulos"},
        {"kind": "stat", "year": None, "title": "120", "body": "partidos"},
        {
            "kind": "fun_fact",
            "year": None,
            "title": "Se diseñó en una servilleta",
            "body": "Y la servilleta se perdió.",
        },
    ]


async def test_product_without_story_has_an_empty_one(
    client: httpx.AsyncClient, seeded: None, story_on: None
) -> None:
    assert await _story(client, "remera-basica") == []


async def test_story_is_empty_with_product_story_turned_off(
    client: httpx.AsyncClient, seeded: None
) -> None:
    # El fixture de la tienda la tiene apagada, y remera-completa tiene historia.
    assert await _story(client, "remera-completa") == []


async def test_seeding_twice_replaces_the_story_instead_of_duplicating_it(
    client: httpx.AsyncClient,
    settings: Settings,
    db_session: AsyncSession,
    storage: ObjectStorage,
    seeded: None,
    story_on: None,
) -> None:
    seed = load_seed(FIXTURES / "seed.toml")
    await apply_seed(db_session, seed, settings.store_config, storage)
    assert len(await _story(client, "remera-completa")) == 5

    product = next(p for p in seed.products if p.slug == "remera-completa")
    shorter = product.model_copy(
        update={"story": [StoryItemSeed(kind="stat", title="7", body="finales")]}
    )
    await apply_seed(
        db_session, seed.model_copy(update={"products": [shorter]}), settings.store_config, storage
    )

    assert await _story(client, "remera-completa") == [
        {"kind": "stat", "year": None, "title": "7", "body": "finales"}
    ]


async def test_seed_rejects_a_milestone_without_year(
    settings: Settings, db_session: AsyncSession, storage: ObjectStorage
) -> None:
    seed = load_seed(FIXTURES / "seed.toml")
    product = next(p for p in seed.products if p.slug == "remera-completa")
    without_year = product.model_copy(
        update={"story": [StoryItemSeed(kind="milestone", title="Debut")]}
    )

    with pytest.raises(SeedError, match="«remera-completa».*año"):
        await apply_seed(
            db_session,
            seed.model_copy(update={"products": [without_year]}),
            settings.store_config,
            storage,
        )
