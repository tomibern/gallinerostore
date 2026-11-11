"""El esquema completo: las migraciones bajan y suben limpias, y los eventos no guardan
datos personales."""

from argparse import Namespace
from pathlib import Path

import anyio
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import Settings

API_ROOT = Path(__file__).resolve().parents[1]

DISCOVERY_TABLES = {
    "products",
    "product_sizes",
    "sizes",
    "categories",
    "collections",
    "versions",
    "tags",
    "product_tags",
    "product_images",
    "product_story_items",
    "home_slides",
    "events",
    "settings",
    "admins",
}


def _alembic(database_url: str) -> Config:
    config = Config(API_ROOT / "alembic.ini")
    config.set_main_option("script_location", str(API_ROOT / "alembic"))
    config.cmd_opts = Namespace(x=[f"database_url={database_url}"])
    return config


async def _table_names(database_url: str) -> set[str]:
    engine = create_async_engine(database_url)
    try:
        async with engine.connect() as conn:
            return set(await conn.run_sync(lambda c: inspect(c).get_table_names()))
    finally:
        await engine.dispose()


async def _columns(database_url: str, table: str) -> set[str]:
    engine = create_async_engine(database_url)
    try:
        async with engine.connect() as conn:
            columns = await conn.run_sync(lambda c: inspect(c).get_columns(table))
            return {column["name"] for column in columns}
    finally:
        await engine.dispose()


async def test_migrations_go_down_and_up_cleanly(settings: Settings) -> None:
    config = _alembic(settings.database_url)

    # Alembic usa asyncio.run por dentro: corre en otro hilo, fuera del loop del test.
    await anyio.to_thread.run_sync(command.downgrade, config, "base")
    assert await _table_names(settings.database_url) <= {"alembic_version"}

    await anyio.to_thread.run_sync(command.upgrade, config, "head")
    assert await _table_names(settings.database_url) >= DISCOVERY_TABLES


async def test_events_store_no_personal_data(settings: Settings) -> None:
    # Producto, canal, talle, origen, dispositivo, sesión anónima, página y fecha.
    # Nada que identifique a una persona (IP, user agent, email, teléfono, nombre).
    assert await _columns(settings.database_url, "events") == {
        "id",
        "type",
        "product_id",
        "channel",
        "size_id",
        "source",
        "device",
        "session_id",
        "page",
        "created_at",
    }
