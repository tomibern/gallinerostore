"""Salida de `GET /admin/metrics/summary`: todo lo que muestra la pantalla de Métricas."""

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field

from app.modules.settings.models import Channel


class Period(StrEnum):
    """Períodos móviles que terminan ahora, en días de la tienda."""

    TODAY = "today"  # desde la medianoche de la tienda
    LAST_7_DAYS = "7d"  # hoy y los 6 días anteriores
    LAST_30_DAYS = "30d"  # hoy y los 29 días anteriores


class Count(BaseModel):
    """Un total del período comparado con el período anterior de igual largo."""

    current: int
    previous: int
    change: float | None = Field(
        description="Cambio relativo contra el período anterior (0.25 es +25 %). "
        "Sin valor si el período anterior es cero."
    )


class Rate(BaseModel):
    """Tasa de consulta global: consultas de productos dividido visitas a detalles."""

    current: float | None = Field(description="Sin valor si no hubo visitas a detalles.")
    previous: float | None


class ChartPoint(BaseModel):
    """Una barra del gráfico: un día, o una hora de hoy."""

    date: date
    hour: int | None = Field(description="Hora del día (0 a 23) en el gráfico de hoy.")
    visits: int
    inquiries: int


class ChannelCount(BaseModel):
    channel: Channel
    inquiries: int
    share: float | None = Field(description="Parte del total de consultas (de 0 a 1).")


class SourceCount(BaseModel):
    """Origen de las visitas: el utm_source tal cual, o ninguno («directo / otros»)."""

    source: str | None
    visits: int
    share: float = Field(description="Parte del total de visitas (de 0 a 1).")


class MetricsSummary(BaseModel):
    period: Period
    visits: Count
    inquiries: Count
    rate: Rate
    chart: list[ChartPoint]
    channels: list[ChannelCount]
    sources: list[SourceCount] = Field(description="Ordenados por visitas, de más a menos.")
