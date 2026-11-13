"""Catálogo público de solo lectura: lo que devuelve GET /products después del seed."""

from typing import Any

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.storage import ObjectStorage
from app.modules.catalog.models import Collection, Product
from app.modules.catalog.seed import SeedError, apply_seed, load_seed
from tests.conftest import FIXTURES


def _by_slug(products: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {p["slug"]: p for p in products}


async def test_lists_only_published_products(client: httpx.AsyncClient, seeded: None) -> None:
    response = await client.get("/products")

    assert response.status_code == 200
    slugs = {p["slug"] for p in response.json()["items"]}
    assert len(slugs) == 9
    assert not slugs & {"remera-borrador", "remera-oculta", "buzo-archivado"}


async def test_product_carries_code_price_section_and_availability(
    client: httpx.AsyncClient, seeded: None
) -> None:
    products = _by_slug((await client.get("/products")).json()["items"])

    remera = products["remera-basica"]
    assert remera["code"].startswith("TP-")
    assert remera["name"] == "Remera básica"
    assert remera["price"] == 1999900
    assert remera["currency"] == "USD"
    assert remera["section"] == "stock"
    assert remera["availability"] == "in_stock"
    assert remera["cover"] is not None


async def test_codes_follow_the_store_prefix_with_three_digits(
    client: httpx.AsyncClient, seeded: None
) -> None:
    codes = [p["code"] for p in (await client.get("/products")).json()["items"]]

    assert all(len(code) >= 6 and code[:3] == "TP-" and code[3:].isdigit() for code in codes)
    assert len(set(codes)) == len(codes)


async def test_seeding_twice_does_not_duplicate_products(
    client: httpx.AsyncClient,
    settings: Settings,
    db_session: AsyncSession,
    storage: ObjectStorage,
    seeded: None,
) -> None:
    first = _by_slug((await client.get("/products")).json()["items"])

    await apply_seed(db_session, load_seed(FIXTURES / "seed.toml"), settings.store_config, storage)
    second = _by_slug((await client.get("/products")).json()["items"])

    assert second.keys() == first.keys()
    assert {s: p["code"] for s, p in second.items()} == {s: p["code"] for s, p in first.items()}


async def test_a_discarded_product_code_is_never_reused(
    client: httpx.AsyncClient,
    settings: Settings,
    db_session: AsyncSession,
    storage: ObjectStorage,
    seeded: None,
) -> None:
    seed = load_seed(FIXTURES / "seed.toml")
    extra = seed.products[0].model_copy(update={"slug": "remera-descartada"})
    # Se crea y se descarta (rollback): el número de código igual queda usado.
    async with db_session.begin_nested() as nested:
        await apply_seed(
            db_session,
            seed.model_copy(update={"products": [extra]}),
            settings.store_config,
            storage,
        )
        discarded = _by_slug((await client.get("/products")).json()["items"])["remera-descartada"][
            "code"
        ]
        await nested.rollback()

    again = seed.products[0].model_copy(update={"slug": "remera-nueva"})
    await apply_seed(
        db_session, seed.model_copy(update={"products": [again]}), settings.store_config, storage
    )
    new_code = _by_slug((await client.get("/products")).json()["items"])["remera-nueva"]["code"]

    assert new_code != discarded
    assert int(new_code[3:]) > int(discarded[3:])


async def test_categories_reject_a_third_level(
    settings: Settings, db_session: AsyncSession, storage: ObjectStorage
) -> None:
    seed = load_seed(FIXTURES / "seed.toml")
    nested = seed.categories[1].model_copy(deep=True)
    nested.children[0].children = [nested.children[0].model_copy(update={"slug": "nieto"})]

    with pytest.raises(SeedError, match="dos niveles"):
        await apply_seed(
            db_session,
            seed.model_copy(update={"categories": [nested]}),
            settings.store_config,
            storage,
        )


async def test_seed_refuses_to_guess_between_products_sharing_a_slug(
    settings: Settings, db_session: AsyncSession, storage: ObjectStorage, seeded: None
) -> None:
    # Dos productos con el mismo slug (el slug no es único: lo puede repetir el admin).
    other = await db_session.scalar(select(Product).where(Product.slug == "buzo-a-pedido"))
    assert other is not None
    other.slug = "remera-basica"
    await db_session.flush()

    with pytest.raises(SeedError, match="no puede saber cuál actualizar"):
        await apply_seed(
            db_session, load_seed(FIXTURES / "seed.toml"), settings.store_config, storage
        )


async def test_seed_rejects_more_than_one_default_collection(
    settings: Settings, db_session: AsyncSession, storage: ObjectStorage
) -> None:
    seed = load_seed(FIXTURES / "seed.toml")
    both_default = [c.model_copy(update={"default": True}) for c in seed.collections]

    with pytest.raises(SeedError, match="Solo una colección"):
        await apply_seed(
            db_session,
            seed.model_copy(update={"collections": both_default}),
            settings.store_config,
            storage,
        )


async def test_database_allows_a_single_default_collection(
    db_session: AsyncSession, seeded: None
) -> None:
    # La regla vale aunque alguien escriba sin pasar por el seed (por ejemplo, el admin).
    db_session.add(Collection(name="Otra", slug="otra", is_default=True, sort_order=9))

    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_seed_rejects_an_on_order_product_with_sizes(
    settings: Settings, db_session: AsyncSession, storage: ObjectStorage
) -> None:
    # Un encargue se pide en cualquier talle del grupo de su categoría: no trae talles.
    seed = load_seed(FIXTURES / "seed.toml")
    on_order = next(p for p in seed.products if p.slug == "buzo-a-pedido")
    with_sizes = on_order.model_copy(update={"sizes": {"M": True}})

    with pytest.raises(SeedError, match="«buzo-a-pedido» es por encargue"):
        await apply_seed(
            db_session,
            seed.model_copy(update={"products": [with_sizes]}),
            settings.store_config,
            storage,
        )
