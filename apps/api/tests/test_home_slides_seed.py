"""Fotos de prueba de los bloques de la home, cargadas por el seed."""

from typing import Any

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.storage import ObjectStorage
from app.modules.settings.seed import (
    HomeSlideSeed,
    apply_home_slides_seed,
    load_home_slides_seed,
)
from app.modules.settings.service import TooManySlidesError
from tests.conftest import FIXTURES


async def _blocks(client: httpx.AsyncClient) -> dict[str, list[dict[str, Any]]]:
    blocks = (await client.get("/store")).json()["home_blocks"]
    return {block["key"]: block["slides"] for block in blocks}


async def test_seed_loads_slides_into_their_block_in_order(
    client: httpx.AsyncClient,
    db_session: AsyncSession,
    settings: Settings,
    storage: ObjectStorage,
) -> None:
    seed = load_home_slides_seed(FIXTURES / "seed.toml")

    await apply_home_slides_seed(db_session, seed, settings.store_config, storage)

    slides = (await _blocks(client))["galeria"]
    assert [s["alt"] for s in slides] == [
        "Primera foto de la galería",
        "Segunda foto de la galería",
    ]
    for slide in slides:
        assert storage.exists(slide["full"].removeprefix("/media/")), slide["full"]


async def test_seed_never_adds_slides_to_a_block_that_already_has_them(
    client: httpx.AsyncClient,
    db_session: AsyncSession,
    settings: Settings,
    storage: ObjectStorage,
) -> None:
    # Una vez cargadas, las fotos las maneja el admin: repetir el seed no las duplica.
    seed = load_home_slides_seed(FIXTURES / "seed.toml")
    await apply_home_slides_seed(db_session, seed, settings.store_config, storage)

    await apply_home_slides_seed(db_session, seed, settings.store_config, storage)

    assert len((await _blocks(client))["galeria"]) == 2


async def test_seed_rejects_slides_of_an_undeclared_block(
    db_session: AsyncSession, settings: Settings, storage: ObjectStorage
) -> None:
    seed = [HomeSlideSeed(block="galeira", alt="Typo en la clave")]

    with pytest.raises(ValueError, match="galeira"):
        await apply_home_slides_seed(db_session, seed, settings.store_config, storage)


async def test_seed_rejects_more_than_four_slides_per_block(
    db_session: AsyncSession, settings: Settings, storage: ObjectStorage
) -> None:
    seed = [HomeSlideSeed(block="galeria", alt=f"Foto {n}") for n in range(5)]

    with pytest.raises(TooManySlidesError):
        await apply_home_slides_seed(db_session, seed, settings.store_config, storage)
