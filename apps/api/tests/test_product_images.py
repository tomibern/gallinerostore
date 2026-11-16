"""Imágenes de producto: la portada que devuelve GET /products y su archivo en el almacenamiento."""

from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.storage import ObjectStorage
from app.modules.catalog.seed import apply_seed, load_seed
from tests.conftest import FIXTURES


async def _products(client: httpx.AsyncClient) -> list[dict[str, Any]]:
    response = await client.get("/products")
    assert response.status_code == 200
    products: list[dict[str, Any]] = response.json()["items"]
    return products


async def test_each_product_has_a_cover_under_media(
    client: httpx.AsyncClient, seeded: None
) -> None:
    for product in await _products(client):
        cover = product["cover"]
        assert cover is not None, product["slug"]
        assert cover["full"].startswith("/media/")
        assert cover["thumb"].startswith("/media/")
        assert cover["full"].endswith(".webp") and cover["thumb"].endswith(".webp")
        assert cover["alt"] == product["name"]
        assert max(cover["width"], cover["height"]) == 1600


async def test_cover_files_exist_in_storage(
    client: httpx.AsyncClient, storage: ObjectStorage, seeded: None
) -> None:
    for product in await _products(client):
        cover = product["cover"]
        for path in (cover["full"], cover["thumb"]):
            assert storage.exists(path.removeprefix("/media/")), path


async def test_reseeding_keeps_the_same_cover_without_new_files(
    client: httpx.AsyncClient,
    settings: Settings,
    db_session: AsyncSession,
    storage: ObjectStorage,
    seeded: None,
) -> None:
    before = {p["code"]: p["cover"] for p in await _products(client)}
    files_before = {code: storage.list_keys(f"products/{code}/") for code in before}

    await apply_seed(db_session, load_seed(FIXTURES / "seed.toml"), settings.store_config, storage)

    after = {p["code"]: p["cover"] for p in await _products(client)}
    assert after == before
    assert {code: storage.list_keys(f"products/{code}/") for code in after} == files_before
    # Dos archivos (completa y miniatura) por foto: remera-completa tiene tres.
    photos = {
        p["code"]: 3 if p["slug"] == "remera-completa" else 1 for p in await _products(client)
    }
    assert {code: len(keys) for code, keys in files_before.items()} == {
        code: 2 * n for code, n in photos.items()
    }


async def test_seed_can_give_a_product_several_photos_in_order(
    client: httpx.AsyncClient, storage: ObjectStorage, seeded: None
) -> None:
    code = next(p["code"] for p in await _products(client) if p["slug"] == "remera-completa")

    images = (await client.get(f"/products/{code.lower()}")).json()["images"]

    assert len(images) == 3
    assert [image["full"].rsplit("/", 1)[1] for image in images] == [
        "1-1600.webp",
        "2-1600.webp",
        "3-1600.webp",
    ]
    for image in images:
        assert storage.exists(image["full"].removeprefix("/media/"))
