"""Endpoints de las métricas del admin. Sin lógica: delegan en el service."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Now
from app.core.config import StoreConfig, get_store_config
from app.core.db import get_session
from app.modules.auth.dependencies import require_admin
from app.modules.metrics import service
from app.modules.metrics.schemas import MetricsSummary, Period

router = APIRouter(
    prefix="/admin/metrics",
    tags=["admin-metrics"],
    dependencies=[Depends(require_admin)],
    responses={401: {"description": "Sin sesión vigente."}},
)


@router.get("/summary")
async def metrics_summary(
    session: Annotated[AsyncSession, Depends(get_session)],
    store: Annotated[StoreConfig, Depends(get_store_config)],
    now: Now,
    period: Period = Period.LAST_7_DAYS,
) -> MetricsSummary:
    """Visitas, consultas y tasa de consulta del período comparadas con el período
    anterior de igual largo, el gráfico por hora (hoy) o por día, las consultas por canal y
    el origen de las visitas. Las visitas del admin con su sesión no se guardan."""
    return await service.summary(session, store, period, now)
