"""Endpoints HTTP del catálogo. Sin lógica: validan entrada y delegan en el service."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, StoreConfig, get_settings, get_store_config
from app.core.db import get_session
from app.modules.catalog import service
from app.modules.catalog.schemas import ProductDetail, ProductFilters, ProductList

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


@router.get(
    "/products/{code}",
    response_model=ProductDetail,
    responses={404: {"description": "No hay un producto publicado con ese código."}},
)
async def get_product(
    code: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    store: Annotated[StoreConfig, Depends(get_store_config)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ProductDetail:
    """Detalle de un producto publicado. El código no distingue mayúsculas (gs-014 = GS-014)."""
    product = await service.published_product(session, store, settings.media_base_url, code)
    if product is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")
    return product
