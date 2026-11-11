"""Tareas de mantenimiento: ``uv run python -m app.cli <comando>``.

- ``ensure-bucket``: crea el bucket de imágenes si no existe y le da lectura pública.
- ``seed``: carga los datos iniciales del cliente (idempotente).
- ``openapi``: imprime el OpenAPI de la API (lo usa ``make gen-client``).
"""

import asyncio
import json
import sys

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.db import create_engine
from app.core.storage import ObjectStorage, allow_public_read, create_s3_client, ensure_bucket
from app.main import create_app
from app.modules.catalog.seed import apply_seed, load_seed
from app.modules.settings.seed import apply_settings_seed, load_settings_seed

USAGE = "Uso: python -m app.cli [ensure-bucket | seed | openapi]"


def _ensure_bucket(settings: Settings) -> None:
    s3 = create_s3_client(settings)
    created = ensure_bucket(s3, settings.s3_bucket)
    allow_public_read(s3, settings.s3_bucket)
    state = "creado" if created else "ya existía"
    print(f"Bucket '{settings.s3_bucket}': {state}, con lectura pública")


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
            store_settings = load_settings_seed(settings.seed_path)
            if store_settings is not None:
                await apply_settings_seed(session, store_settings)
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
