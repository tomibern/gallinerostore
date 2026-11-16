"""Base y bucket de tests propios de cada worktree de git.

Varios worktrees pueden correr la suite al mismo tiempo (por ejemplo, un agente por
ticket). Si comparten la base, las transacciones que cargan el seed se bloquean entre
sí; si comparten el bucket, una corrida le vacía las imágenes a la otra. Por eso cada
worktree usa recursos con su nombre como sufijo. El clon principal (y CI) usa los
nombres configurados tal cual.
"""

import asyncio
import re
from argparse import Namespace
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine

# Límite de largo de un identificador en Postgres y de un nombre de bucket en S3.
MAX_NAME_LENGTH = 63

API_ROOT = Path(__file__).resolve().parents[1]


def checkout_name(repo_root: Path) -> str | None:
    """El nombre de la carpeta si es un worktree de git; None en el clon principal.

    En un worktree, `.git` es un archivo que apunta al repositorio; en el clon
    principal es una carpeta.
    """
    return repo_root.name if (repo_root / ".git").is_file() else None


def _slug(name: str, separator: str) -> str:
    return re.sub(r"[^a-z0-9]+", separator, name.lower()).strip(separator)


def isolated_database_url(url: str, name: str | None) -> str:
    """La URL de la base de tests de este worktree."""
    if name is None:
        return url
    parsed = make_url(url)
    database = f"{parsed.database}_{_slug(name, '_')}"[:MAX_NAME_LENGTH]
    return parsed.set(database=database).render_as_string(hide_password=False)


def isolated_bucket(bucket: str, name: str | None) -> str:
    """El bucket de tests de este worktree."""
    if name is None:
        return bucket
    return f"{bucket}-{_slug(name, '-')}"[:MAX_NAME_LENGTH].rstrip("-")


async def _create_database_if_missing(url: str) -> None:
    parsed = make_url(url)
    admin = create_async_engine(
        parsed.set(database="postgres"), isolation_level="AUTOCOMMIT", pool_size=1
    )
    try:
        async with admin.connect() as conn:
            exists = await conn.scalar(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": parsed.database},
            )
            if not exists:
                await conn.execute(text(f'CREATE DATABASE "{parsed.database}"'))
    finally:
        await admin.dispose()


def prepare_database(url: str) -> None:
    """Crea la base si no existe y le aplica las migraciones pendientes.

    Se llama fuera del loop de los tests: Alembic levanta su propio loop.
    """
    asyncio.run(_create_database_if_missing(url))
    # Sin archivo de configuración, para que Alembic no reconfigure el logging de pytest.
    config = Config()
    config.set_main_option("script_location", str(API_ROOT / "alembic"))
    config.cmd_opts = Namespace(x=[f"database_url={url}"])
    command.upgrade(config, "head")
