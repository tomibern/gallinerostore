"""Endpoints HTTP del catálogo. Sin lógica: validan entrada y delegan en el service."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.exceptions import RequestValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Now
from app.core.config import Settings, StoreConfig, get_settings, get_store_config
from app.core.db import get_session
from app.modules.auth.dependencies import AdminAccess, CsrfChecked
from app.modules.catalog import service
from app.modules.catalog.schemas import (
    AdminProduct,
    AdminProductCreate,
    AdminProductList,
    AdminProductPatch,
    AdminProductQuery,
    CatalogOptions,
    ProductDetail,
    ProductFilters,
    ProductList,
)

router = APIRouter(tags=["catalog"])
admin_router = APIRouter(prefix="/admin", tags=["admin-catalog"])


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
    """Detalle de un producto publicado. El código no distingue mayúsculas (abc-014 = ABC-014)."""
    product = await service.published_product(
        session, store, settings.media_base_url, settings.site_url, code
    )
    if product is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")
    return product


@admin_router.get("/products", responses={401: {"description": "Sin sesión vigente."}})
async def list_admin_products(
    admin: AdminAccess,
    session: Annotated[AsyncSession, Depends(get_session)],
    store: Annotated[StoreConfig, Depends(get_store_config)],
    settings: Annotated[Settings, Depends(get_settings)],
    query: Annotated[AdminProductQuery, Query()],
    now: Now,
) -> AdminProductList:
    """Todos los productos del admin (borradores, ocultos y archivados incluidos), con
    búsqueda y filtro, del más nuevo al más viejo, con sus visitas y consultas de los
    últimos 7 días."""
    return await service.list_for_admin(session, store, settings.media_base_url, query, now)


_NO_SESSION: dict[int | str, dict[str, Any]] = {401: {"description": "Sin sesión vigente."}}
_NOT_FOUND: dict[int | str, dict[str, Any]] = {
    404: {"description": "No hay un producto con ese código."}
}
_INVALID: dict[int | str, dict[str, Any]] = {
    422: {
        "description": (
            "Un campo inválido: el error dice cuál (``loc``). Una categoría, colección, "
            "versión, etiqueta o talle que no existe tiene ``type`` ``unknown`` o "
            "``unknown_size``; talles en un encargue, ``on_order_with_sizes``."
        )
    }
}


def _as_validation_error(error: service.InvalidProductError) -> RequestValidationError:
    """Los problemas del service con la misma forma que los errores de Pydantic."""
    return RequestValidationError(
        [
            {"loc": ("body", *problem.loc), "msg": problem.message, "type": problem.type}
            for problem in error.problems
        ]
    )


@admin_router.get("/catalog-options", responses=_NO_SESSION)
async def get_catalog_options(
    admin: AdminAccess,
    session: Annotated[AsyncSession, Depends(get_session)],
    store: Annotated[StoreConfig, Depends(get_store_config)],
) -> CatalogOptions:
    """Lo que el editor ofrece para elegir: categorías con su grupo de talles,
    colecciones, versiones, etiquetas, talles por grupo y funciones activas."""
    return await service.catalog_options(session, store)


@admin_router.post(
    "/products",
    status_code=201,
    dependencies=[CsrfChecked],
    responses=_NO_SESSION | _INVALID,
)
async def create_admin_product(
    body: AdminProductCreate,
    admin: AdminAccess,
    session: Annotated[AsyncSession, Depends(get_session)],
    store: Annotated[StoreConfig, Depends(get_store_config)],
) -> AdminProduct:
    """Crea un borrador. El código lo asigna la API y no cambia nunca."""
    try:
        return await service.create_product(session, store, body)
    except service.InvalidProductError as error:
        raise _as_validation_error(error) from error


@admin_router.get("/products/{code}", responses=_NO_SESSION | _NOT_FOUND)
async def get_admin_product(
    code: str,
    admin: AdminAccess,
    session: Annotated[AsyncSession, Depends(get_session)],
    store: Annotated[StoreConfig, Depends(get_store_config)],
) -> AdminProduct:
    """Un producto en cualquier estado, para editarlo. El código no distingue mayúsculas."""
    product = await service.admin_product(session, store, code)
    if product is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")
    return product


@admin_router.patch(
    "/products/{code}",
    dependencies=[CsrfChecked],
    responses=_NO_SESSION | _NOT_FOUND | _INVALID,
)
async def patch_admin_product(
    code: str,
    body: AdminProductPatch,
    admin: AdminAccess,
    session: Annotated[AsyncSession, Depends(get_session)],
    store: Annotated[StoreConfig, Depends(get_store_config)],
) -> AdminProduct:
    """Edita los campos que vienen; los demás no cambian. Pasar a encargue borra los
    talles; pasar a stock, o cambiar a una categoría de otro grupo siendo de stock, deja
    todos los del grupo disponibles."""
    try:
        product = await service.update_product(session, store, code, body)
    except service.InvalidProductError as error:
        raise _as_validation_error(error) from error
    if product is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")
    return product
