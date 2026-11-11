from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from mypy_boto3_s3 import S3Client
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.config import Settings, get_settings
from app.core.db import get_engine
from app.core.storage import get_s3
from app.health import service
from app.health.schemas import Health

router = APIRouter(tags=["health"])


@router.get("/health", response_model=Health)
async def health(
    response: Response,
    engine: Annotated[AsyncEngine, Depends(get_engine)],
    s3: Annotated[S3Client, Depends(get_s3)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> Health:
    result = await service.check_health(engine, s3, settings.s3_bucket)
    if not result.is_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return result
