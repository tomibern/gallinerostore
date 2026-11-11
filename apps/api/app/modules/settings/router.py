from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.config import StoreConfig, get_store_config
from app.modules.settings import service
from app.modules.settings.schemas import PublicStore

router = APIRouter(tags=["settings"])


@router.get("/store", response_model=PublicStore)
async def store(config: Annotated[StoreConfig, Depends(get_store_config)]) -> PublicStore:
    return service.public_store(config)
