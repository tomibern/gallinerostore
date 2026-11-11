"""Tareas de mantenimiento: ``uv run python -m app.cli <comando>``."""

import sys

from app.core.config import Settings
from app.core.storage import create_s3_client, ensure_bucket


def main(argv: list[str]) -> int:
    if argv != ["ensure-bucket"]:
        print("Uso: python -m app.cli ensure-bucket", file=sys.stderr)
        return 2
    settings = Settings()
    created = ensure_bucket(create_s3_client(settings), settings.s3_bucket)
    print(f"Bucket '{settings.s3_bucket}': {'creado' if created else 'ya existía'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
