"""Chequeos de salud de la infraestructura."""

from typing import Literal

import anyio
from mypy_boto3_s3 import S3Client
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

CheckResult = Literal["ok", "error"]


async def check_database(engine: AsyncEngine) -> CheckResult:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        return "error"
    return "ok"


async def check_storage(s3: S3Client) -> CheckResult:
    try:
        await anyio.to_thread.run_sync(s3.list_buckets)
    except Exception:
        return "error"
    return "ok"
