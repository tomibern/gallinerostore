"""Fixtures compartidas: la app se prueba por HTTP contra la base de tests."""

import os
from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from typing import Any

import httpx
import pytest
from dotenv import dotenv_values
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import REPO_ROOT, Settings, get_store_config
from app.core.db import get_session
from app.core.storage import ObjectStorage, create_s3_client, ensure_bucket
from app.main import create_app
from app.modules.catalog.seed import apply_seed, load_seed
from app.modules.settings.seed import SettingsSeed, apply_settings_seed, load_settings_seed
from tests.isolation import (
    checkout_name,
    isolated_bucket,
    isolated_database_url,
    prepare_database,
)
from tests.support import http_client

FIXTURES = Path(__file__).parent / "fixtures"


def _test_database_url() -> str:
    """De la variable de entorno (CI) o del .env de la raíz (desarrollo)."""
    url = os.environ.get("TEST_DATABASE_URL") or dotenv_values(REPO_ROOT / ".env").get(
        "TEST_DATABASE_URL"
    )
    if not url:
        raise RuntimeError("Falta TEST_DATABASE_URL (ver .env.example)")
    return url


@pytest.fixture(scope="session")
def settings() -> Settings:
    """Configuración de tests: misma que desarrollo, pero contra la base de tests.

    En un worktree, la base y el bucket llevan su nombre para no pisarse con otras
    corridas en paralelo (ver `tests/isolation.py`).
    """
    name = checkout_name(REPO_ROOT)
    database_url = isolated_database_url(_test_database_url(), name)
    prepare_database(database_url)
    test_settings = Settings(  # el resto sale del entorno
        database_url=database_url,
        s3_bucket=isolated_bucket("test-media", name),
        store_config_path=FIXTURES / "store.toml",
        site_url="https://tienda.test",
    )
    ensure_bucket(create_s3_client(test_settings), test_settings.s3_bucket)
    return test_settings


@pytest.fixture
async def app(settings: Settings) -> AsyncIterator[FastAPI]:
    """App de tests: cada test corre dentro de una transacción que se deshace al final.

    Lo que un test escribe (aunque la app haga commit) nunca llega a la base,
    así los tests no se pisan entre sí.
    """
    application = create_app(settings)
    async with (
        application.router.lifespan_context(application),
        application.state.engine.connect() as conn,
    ):
        outer = await conn.begin()
        session = AsyncSession(
            bind=conn,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )

        async def _session() -> AsyncIterator[AsyncSession]:
            yield session

        application.dependency_overrides[get_session] = _session
        application.state.test_session = session
        try:
            yield application
        finally:
            await session.close()
            await outer.rollback()


@pytest.fixture
def db_session(app: FastAPI) -> AsyncSession:
    """La misma sesión que usa la app en este test (dentro de la transacción que se deshace)."""
    session: AsyncSession = app.state.test_session
    return session


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    async with http_client(app) as c:
        yield c


@pytest.fixture(scope="session")
def storage(settings: Settings) -> Iterator[ObjectStorage]:
    """El bucket de tests, a través de la misma interfaz que usa la app.

    La base hace rollback después de cada test, pero el bucket no: se vacía al
    empezar y al terminar la sesión para que no se acumulen archivos huérfanos.
    Vaciarlo puede tardar más que el timeout de lectura de la app (cada `seeded`
    sube imágenes con códigos nuevos), así que este cliente espera más.
    """
    test_storage = ObjectStorage(create_s3_client(settings, read_timeout=60), settings.s3_bucket)
    test_storage.delete_prefix("")
    yield test_storage
    test_storage.delete_prefix("")


async def settings_seed(db_session: AsyncSession, **changes: Any) -> None:
    """La configuración del fixture (WhatsApp, Instagram, plantillas y textos), con cambios."""
    seed = load_settings_seed(FIXTURES / "seed.toml")
    assert seed is not None
    await apply_settings_seed(db_session, SettingsSeed.model_validate(seed.model_dump() | changes))


@pytest.fixture
def instagram_on(app: FastAPI, settings: Settings) -> None:
    """Instagram prendido (el fixture de la tienda lo tiene apagado)."""
    features = settings.store_config.features.model_copy(update={"instagram": True})
    store = settings.store_config.model_copy(update={"features": features})
    app.dependency_overrides[get_store_config] = lambda: store


@pytest.fixture
async def seeded(settings: Settings, db_session: AsyncSession, storage: ObjectStorage) -> None:
    """El seed ficticio cargado (con imágenes) dentro de la transacción del test."""
    await apply_seed(db_session, load_seed(FIXTURES / "seed.toml"), settings.store_config, storage)
