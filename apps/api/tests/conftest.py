"""Fixtures compartidas: la app se prueba por HTTP contra la base de tests."""

import os
from collections.abc import AsyncIterator
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.db import get_session
from app.core.storage import create_s3_client, ensure_bucket
from app.main import create_app

REPO_ROOT = Path(__file__).resolve().parents[3]


def _load_dotenv() -> None:
    """Carga el .env de la raíz si existe, sin pisar variables ya definidas (CI)."""
    env_file = REPO_ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key, value)


_load_dotenv()


@pytest.fixture(scope="session")
def settings() -> Settings:
    """Configuración de tests: misma que desarrollo, pero contra la base de tests."""
    test_settings = Settings(  # el resto sale del entorno
        database_url=os.environ["TEST_DATABASE_URL"],
        s3_bucket="test-media",
        store_config_path=Path(__file__).parent / "fixtures" / "store.toml",
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
        try:
            yield application
        finally:
            await session.close()
            await outer.rollback()


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
