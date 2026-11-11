from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Response, status
from mypy_boto3_s3 import S3Client
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.db import get_engine
from app.core.storage import get_s3
from app.health import service

router = APIRouter(tags=["health"])


class HealthChecks(BaseModel):
    database: service.CheckResult
    storage: service.CheckResult


class Health(BaseModel):
    status: Literal["ok", "error"]
    checks: HealthChecks


@router.get("/health", response_model=Health)
async def health(
    response: Response,
    engine: Annotated[AsyncEngine, Depends(get_engine)],
    s3: Annotated[S3Client, Depends(get_s3)],
) -> Health:
    checks = HealthChecks(
        database=await service.check_database(engine),
        storage=await service.check_storage(s3),
    )
    healthy = checks.database == "ok" and checks.storage == "ok"
    if not healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return Health(status="ok" if healthy else "error", checks=checks)
