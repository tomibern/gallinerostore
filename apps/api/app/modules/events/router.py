"""Endpoints HTTP de los eventos. Sin lógica: validan entrada y delegan en el service."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, StoreConfig, get_settings, get_store_config
from app.core.db import get_session
from app.modules.events import service
from app.modules.events.rate_limit import EVENTS_RATE_LIMIT, limiter
from app.modules.events.schemas import EventIn, EventOut, SessionId

router = APIRouter(tags=["events"])


@router.post(
    "/events",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={429: {"description": "Demasiados eventos desde la misma IP."}},
)
@limiter.limit(EVENTS_RATE_LIMIT)
async def record_event(
    request: Request,  # lo usa el límite de frecuencia
    event: EventIn,
    session: Annotated[AsyncSession, Depends(get_session)],
    store: Annotated[StoreConfig, Depends(get_store_config)],
) -> None:
    """Registra una visita o una consulta, sin cookies ni datos personales. La IP solo
    cuenta para el límite de frecuencia: no se guarda."""
    try:
        await service.record(session, store, event)
    except service.InvalidEventError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


def _e2e_only(settings: Annotated[Settings, Depends(get_settings)]) -> None:
    if not settings.e2e_endpoints:
        raise HTTPException(status_code=404)


# Para verificar los e2e: fuera del OpenAPI y apagado salvo con E2E_ENDPOINTS.
e2e_router = APIRouter(prefix="/e2e", include_in_schema=False, dependencies=[Depends(_e2e_only)])


@e2e_router.get("/events")
async def session_events(
    session_id: SessionId, session: Annotated[AsyncSession, Depends(get_session)]
) -> list[EventOut]:
    """Los eventos guardados de una sesión, en orden."""
    return await service.for_session(session, session_id)
