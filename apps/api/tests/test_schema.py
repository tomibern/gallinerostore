"""El esquema completo: las migraciones bajan y suben limpias, y los eventos no guardan
datos personales."""

from argparse import Namespace
from collections.abc import AsyncIterator
from pathlib import Path

import anyio
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, make_url, text
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


@pytest.fixture
async def scratch_database_url(settings: Settings) -> AsyncIterator[str]:
    """Una base vacía solo para este test: bajar y subir migraciones en la base de
    tests compartida rompería cualquier otra corrida que esté usándola."""
    url = make_url(settings.database_url)
    name = f"{url.database}_migrations"
    admin = create_async_engine(url, isolation_level="AUTOCOMMIT")
    try:
        async with admin.connect() as conn:
            await conn.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
            await conn.execute(text(f'CREATE DATABASE "{name}"'))
        yield url.set(database=name).render_as_string(hide_password=False)
        async with admin.connect() as conn:
            await conn.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
    finally:
        await admin.dispose()


async def test_migrations_go_up_down_and_up_cleanly(scratch_database_url: str) -> None:
    config = _alembic(scratch_database_url)

    # Alembic usa asyncio.run por dentro: corre en otro hilo, fuera del loop del test.
    await anyio.to_thread.run_sync(command.upgrade, config, "head")
    assert await _table_names(scratch_database_url) >= DISCOVERY_TABLES

    await anyio.to_thread.run_sync(command.downgrade, config, "base")
    assert await _table_names(scratch_database_url) <= {"alembic_version"}

    await anyio.to_thread.run_sync(command.upgrade, config, "head")
    assert await _table_names(scratch_database_url) >= DISCOVERY_TABLES


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


# Un producto de stock y un encargue, ambos con un talle, antes de la migración.
_ON_ORDER_FIXTURE = [
    """
    INSERT INTO sizes (id, label, sort_order, size_group) VALUES (1, 'M', 0, 'g')
    """,
    """
    INSERT INTO categories (id, name, slug, sort_order, size_group)
        VALUES (1, 'C', 'c', 0, 'g')
    """,
    """
    INSERT INTO collections (id, name, slug, is_default, sort_order)
        VALUES (1, 'K', 'k', true, 0)
    """,
    """
    INSERT INTO products (id, code, name, slug, category_id, collection_id,
        sale_mode, price, status, featured, sort_order)
        VALUES
        (1, 'X-001', 'Stock', 'stock', 1, 1, 'stock', 1, 'published', false, 0),
        (2, 'X-002', 'Encargue', 'encargue', 1, 1, 'on_order', 1, 'published',
        false, 1)
    """,
    """
    INSERT INTO product_sizes (product_id, size_id, in_stock)
        VALUES (1, 1, true), (2, 1, true)
    """,
]


async def test_on_order_products_lose_their_own_sizes(scratch_database_url: str) -> None:
    # Un encargue se pide en cualquier talle de su grupo: la migración borra sus talles
    # y deja los de los productos de stock.
    config = _alembic(scratch_database_url)
    await anyio.to_thread.run_sync(command.upgrade, config, "398992582d68")

    engine = create_async_engine(scratch_database_url)
    try:
        async with engine.begin() as conn:
            for statement in _ON_ORDER_FIXTURE:
                await conn.execute(text(statement))

        await anyio.to_thread.run_sync(command.upgrade, config, "head")

        async with engine.connect() as conn:
            rows = await conn.execute(text("SELECT product_id FROM product_sizes"))
            assert [row.product_id for row in rows] == [1]
    finally:
        await engine.dispose()
