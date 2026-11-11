"""Chequeos de salud de la infraestructura."""

import anyio
from mypy_boto3_s3 import S3Client
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.health.schemas import Health, HealthChecks, Status


async def check_health(engine: AsyncEngine, s3: S3Client, bucket: str) -> Health:
    checks = HealthChecks(
        database=await _check_database(engine),
        storage=await _check_storage(s3, bucket),
    )
    healthy = checks.database == "ok" and checks.storage == "ok"
    return Health(status="ok" if healthy else "error", checks=checks)


async def _check_database(engine: AsyncEngine) -> Status:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        return "error"
    return "ok"


async def _check_storage(s3: S3Client, bucket: str) -> Status:
    try:
        await anyio.to_thread.run_sync(s3.list_buckets)
    except Exception:
        return "error"
    return "ok"
