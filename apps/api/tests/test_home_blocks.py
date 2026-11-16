"""Bloques de la home: los declara la configuración y sus fotos salen de home_slides."""

from pathlib import Path

import httpx
import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import StoreConfig
from app.modules.settings.models import HomeSlide


def _slide(block: str, n: int, sort_order: int) -> HomeSlide:
    return HomeSlide(
        block=block, path_full=f"home/{block}/{n}-1600.webp", alt=f"Foto {n}", sort_order=sort_order
    )


async def test_store_returns_declared_blocks_in_config_order_with_their_slides(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    db_session.add_all(
        [
            _slide("galeria", 2, sort_order=1),
            _slide("galeria", 1, sort_order=0),
            # Un bloque que la configuración no declara no se muestra.
            _slide("otro-bloque", 1, sort_order=0),
        ]
    )
    await db_session.flush()

    response = await client.get("/store")

    assert response.status_code == 200
    assert response.json()["home_blocks"] == [
        {
            "key": "galeria",
            "slides": [
                {"full": "/media/home/galeria/1-1600.webp", "alt": "Foto 1"},
                {"full": "/media/home/galeria/2-1600.webp", "alt": "Foto 2"},
            ],
        },
        {"key": "sin-fotos", "slides": []},
    ]


async def test_store_returns_at_most_four_slides_per_block(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    db_session.add_all([_slide("galeria", n, sort_order=n) for n in range(1, 6)])
    await db_session.flush()

    blocks = (await client.get("/store")).json()["home_blocks"]

    assert [s["alt"] for s in blocks[0]["slides"]] == ["Foto 1", "Foto 2", "Foto 3", "Foto 4"]


def _config_with_home(tmp_path: Path, home: str) -> Path:
    path = tmp_path / "store.toml"
    base = (Path(__file__).parent / "fixtures" / "store.toml").read_text().split("[home]")[0]
    path.write_text(base + home)
    return path


def test_store_without_home_section_has_no_blocks(tmp_path: Path) -> None:
    config = StoreConfig.from_toml(_config_with_home(tmp_path, ""))

    assert config.home.blocks == []


@pytest.mark.parametrize(
    "blocks",
    [
        '["Con Mayúsculas"]',
        '["con espacios"]',
        '["repetido", "repetido"]',
        f'["{"x" * 41}"]',
    ],
)
def test_store_rejects_invalid_block_keys(tmp_path: Path, blocks: str) -> None:
    with pytest.raises(ValidationError):
        StoreConfig.from_toml(_config_with_home(tmp_path, f"[home]\nblocks = {blocks}\n"))
