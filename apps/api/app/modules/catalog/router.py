"""Endpoints HTTP del catálogo. Sin lógica: validan entrada y delegan en el service."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import StoreConfig, get_store_config
from app.core.db import get_session
from app.modules.catalog import service
from app.modules.catalog.schemas import ProductListItem

router = APIRouter(tags=["catalog"])


@router.get("/products", response_model=list[ProductListItem])
async def list_products(
    session: Annotated[AsyncSession, Depends(get_session)],
    store: Annotated[StoreConfig, Depends(get_store_config)],
) -> list[ProductListItem]:
    """Productos publicados del catálogo."""
    return await service.list_published(session, store)
