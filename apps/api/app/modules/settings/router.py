from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, StoreConfig, get_settings, get_store_config
from app.core.db import get_session
from app.modules.settings import service
from app.modules.settings.schemas import PublicStore

router = APIRouter(tags=["settings"])


@router.get("/store", response_model=PublicStore)
async def store(
    session: Annotated[AsyncSession, Depends(get_session)],
    config: Annotated[StoreConfig, Depends(get_store_config)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> PublicStore:
    """Configuración pública de la tienda: los bloques de la home con sus fotos, «Cómo
    comprar», las preguntas frecuentes, los canales activos y la consulta general."""
    return await service.public_store(session, config, settings.media_base_url)
