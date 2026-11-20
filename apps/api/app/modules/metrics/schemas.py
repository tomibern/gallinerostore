"""Salidas de las métricas del admin: el resumen y el ranking de productos de la
pantalla de Métricas, y las cifras de 7 días del listado de productos."""

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field

from app.modules.catalog.models import ProductStatus
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


class RankingSort(StrEnum):
    """Columna por la que se ordena el ranking, siempre de mayor a menor."""

    VISITS = "visits"
    INQUIRIES = "inquiries"
    RATE = "rate"
    WHATSAPP = "whatsapp"
    INSTAGRAM = "instagram"


class RankedProduct(BaseModel):
    """Un producto con actividad en el período, en cualquier estado."""

    code: str
    name: str
    status: ProductStatus
    visits: int = Field(description="Visitas al detalle del producto.")
    inquiries: int = Field(description="Consultas por el producto, por cualquier canal.")
    rate: float | None = Field(
        description="Tasa de consulta: consultas dividido visitas al detalle. Sin valor si "
        "no tuvo visitas."
    )
    whatsapp: int = Field(description="Consultas por WhatsApp.")
    instagram: int = Field(description="Consultas por Instagram.")


class ProductRanking(BaseModel):
    period: Period
    sort: RankingSort
    channels: list[Channel] = Field(
        description="Canales que se muestran: los mismos del resumen (Instagram apagado no "
        "aparece, salvo que haya consultas por ese canal en el período)."
    )
    items: list[RankedProduct] = Field(
        description="Los productos con alguna visita o consulta en el período, de mayor a "
        "menor según `sort` (sin tasa, al final). Empates: más consultas, más visitas, "
        "y por nombre."
    )


class ProductActivity(BaseModel):
    """Visitas al detalle y consultas de un producto en los últimos 7 días."""

    visits: int
    inquiries: int
