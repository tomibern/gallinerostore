"""Tareas de mantenimiento: ``uv run python -m app.cli <comando>``.

- ``ensure-bucket``: crea el bucket de imágenes si no existe.
- ``seed``: carga los datos iniciales del cliente (idempotente).
- ``openapi``: imprime el OpenAPI de la API (lo usa ``make gen-client``).
"""

import asyncio
import json
import sys

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.db import create_engine
from app.core.storage import ObjectStorage, create_s3_client, ensure_bucket
from app.main import create_app
from app.modules.catalog.seed import apply_seed, load_seed

USAGE = "Uso: python -m app.cli [ensure-bucket | seed | openapi]"


def _ensure_bucket(settings: Settings) -> None:
    created = ensure_bucket(create_s3_client(settings), settings.s3_bucket)
    print(f"Bucket '{settings.s3_bucket}': {'creado' if created else 'ya existía'}")


async def _seed(settings: Settings) -> None:
    seed = load_seed(settings.seed_path)
    engine = create_engine(settings.database_url)
    try:
        async with (
            engine.begin() as conn,
            AsyncSession(bind=conn, expire_on_commit=False) as session,
        ):
            storage = ObjectStorage(create_s3_client(settings), settings.s3_bucket)
            await apply_seed(session, seed, settings.store_config, storage)
    finally:
        await engine.dispose()
    print(f"Seed cargado desde {settings.seed_path}: {len(seed.products)} productos")


def main(argv: list[str]) -> int:
    settings = Settings()
    match argv:
        case ["ensure-bucket"]:
            _ensure_bucket(settings)
        case ["seed"]:
            asyncio.run(_seed(settings))
        case ["openapi"]:
            print(json.dumps(create_app(settings).openapi(), indent=2, ensure_ascii=False))
        case _:
            print(USAGE, file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
