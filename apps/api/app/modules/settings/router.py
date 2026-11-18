from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, StoreConfig, get_settings, get_store_config
from app.core.db import get_session
from app.modules.auth.dependencies import AdminAccess, CsrfChecked
from app.modules.catalog import service as catalog_service
from app.modules.settings import service
from app.modules.settings.schemas import (
    AdminSettings,
    AdminSettingsIn,
    MessagePreview,
    MessagePreviewIn,
    PublicStore,
)

router = APIRouter(tags=["settings"])
admin_router = APIRouter(prefix="/admin/settings", tags=["admin-settings"])

_NO_SESSION: dict[int | str, dict[str, Any]] = {401: {"description": "Sin sesión vigente."}}
_INVALID: dict[int | str, dict[str, Any]] = {
    422: {
        "description": (
            "Un campo inválido: el error dice cuál (``loc``). Una variable que no existe "
            "en una plantilla tiene ``type`` ``unknown_variable``."
        )
    }
}


@router.get("/store", response_model=PublicStore)
async def store(
    session: Annotated[AsyncSession, Depends(get_session)],
    config: Annotated[StoreConfig, Depends(get_store_config)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> PublicStore:
    """Configuración pública de la tienda: los bloques de la home con sus fotos, «Cómo
    comprar», las preguntas frecuentes, los canales activos y la consulta general."""
    return await service.public_store(session, config, settings.media_base_url)


@admin_router.get("", responses=_NO_SESSION)
async def get_admin_settings(
    _: AdminAccess, session: Annotated[AsyncSession, Depends(get_session)]
) -> AdminSettings:
    """Contacto, mensajes prearmados y aviso de encargue, para editarlos."""
    return await service.admin_settings(session)


@admin_router.put("", dependencies=[CsrfChecked], responses=_NO_SESSION | _INVALID)
async def put_admin_settings(
    body: AdminSettingsIn,
    _: AdminAccess,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AdminSettings:
    """Guarda contacto, mensajes prearmados y aviso de encargue."""
    return await service.save_admin_settings(session, body)


@admin_router.post("/message-preview", dependencies=[CsrfChecked], responses=_NO_SESSION | _INVALID)
async def preview_message(
    body: MessagePreviewIn,
    _: AdminAccess,
    session: Annotated[AsyncSession, Depends(get_session)],
    config: Annotated[StoreConfig, Depends(get_store_config)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> MessagePreview:
    """Arma el mensaje de una plantilla (sin guardarla) con un producto publicado real."""
    return await catalog_service.message_preview(
        session, config, settings.site_url, body.case, body.template
    )
