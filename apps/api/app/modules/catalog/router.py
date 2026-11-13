"""Endpoints HTTP del catálogo. Sin lógica: validan entrada y delegan en el service."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, StoreConfig, get_settings, get_store_config
from app.core.db import get_session
from app.modules.catalog import service
from app.modules.catalog.schemas import ProductFilters, ProductList

router = APIRouter(tags=["catalog"])


@router.get("/products", response_model=ProductList)
async def list_products(
    session: Annotated[AsyncSession, Depends(get_session)],
    store: Annotated[StoreConfig, Depends(get_store_config)],
    settings: Annotated[Settings, Depends(get_settings)],
    filters: Annotated[ProductFilters, Query()],
) -> ProductList:
    """Productos publicados filtrados y ordenados, con los valores de filtro de la sección."""
    return await service.list_published(session, store, settings.media_base_url, filters)
