"""Reglas de las métricas: qué rango cubre cada período, contra qué se compara y cómo
se arman la tasa, el gráfico, los canales y los orígenes (glosario: **Visita**, **Tasa
de consulta**, **Origen**)."""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import StoreConfig
from app.modules.events.models import EventType
from app.modules.metrics import repository
from app.modules.metrics.repository import Window
from app.modules.metrics.schemas import (
    ChannelCount,
    ChartPoint,
    Count,
    MetricsSummary,
    Period,
    Rate,
    SourceCount,
)
from app.modules.settings.models import Channel

PERIOD_DAYS = {Period.TODAY: 1, Period.LAST_7_DAYS: 7, Period.LAST_30_DAYS: 30}


@dataclass(frozen=True)
class Windows:
    current: Window
    # El período anterior de igual largo: los mismos días corridos para atrás, hasta la
    # misma hora («Hoy» se compara con ayer hasta esta hora).
    previous: Window
    days: list[date]


def windows(period: Period, now: datetime, zone: ZoneInfo) -> Windows:
    """El período empieza a la medianoche de la tienda y termina ahora."""
    days = PERIOD_DAYS[period]
    local_now = now.astimezone(zone)
    first_day = local_now.date() - timedelta(days=days - 1)
    shift = timedelta(days=days)
    return Windows(
        current=Window(datetime.combine(first_day, time(), zone), now, zone.key),
        # Cuentas de reloj de pared: un cambio de horario no corre el corte.
        previous=Window(
            datetime.combine(first_day - shift, time(), zone), local_now - shift, zone.key
        ),
        days=[first_day + timedelta(days=n) for n in range(days)],
    )


def _change(current: int, previous: int) -> float | None:
    return (current - previous) / previous if previous else None


def _rate(inquiries: int, visits: int) -> float | None:
    return inquiries / visits if visits else None


def _count(current: int, previous: int) -> Count:
    return Count(current=current, previous=previous, change=_change(current, previous))


@dataclass(frozen=True)
class _Totals:
    visits: int
    inquiries: int
    rate: float | None


async def _totals(session: AsyncSession, window: Window) -> _Totals:
    visits = await repository.visits_by_type(session, window)
    inquiries = await repository.inquiries_by_type(session, window)
    return _Totals(
        visits=sum(visits.values()),
        inquiries=sum(inquiries.values()),
        rate=_rate(
            inquiries.get(EventType.CONTACT_CLICK, 0), visits.get(EventType.PRODUCT_VIEW, 0)
        ),
    )


async def _chart(session: AsyncSession, period: Period, periods: Windows) -> list[ChartPoint]:
    """Por hora en «Hoy» (hasta la hora actual) y por día en los otros, sin huecos."""
    window = periods.current
    if period is Period.TODAY:
        today = periods.days[0]
        last_hour = window.end.astimezone(window.start.tzinfo).hour
        buckets: list[tuple[date, int | None]] = [(today, hour) for hour in range(last_hour + 1)]
        unit: repository.Unit = "hour"
    else:
        buckets = [(day, None) for day in periods.days]
        unit = "day"
    visits = await repository.visits_by_bucket(session, window, unit)
    inquiries = await repository.inquiries_by_bucket(session, window, unit)
    points = []
    for day, hour in buckets:
        key = datetime.combine(day, time(hour or 0))
        points.append(
            ChartPoint(
                date=day, hour=hour, visits=visits.get(key, 0), inquiries=inquiries.get(key, 0)
            )
        )
    return points


async def _channels(
    session: AsyncSession, store: StoreConfig, window: Window
) -> list[ChannelCount]:
    """Todos los canales, también los que no tuvieron consultas. Instagram apagado no
    aparece, salvo que haya consultas de antes de apagarlo."""
    counts = await repository.inquiries_by_channel(session, window)
    total = sum(counts.values())
    channels = [
        channel
        for channel in Channel
        if channel is not Channel.INSTAGRAM or store.features.instagram or counts.get(channel)
    ]
    return [
        ChannelCount(
            channel=channel,
            inquiries=counts.get(channel, 0),
            share=counts.get(channel, 0) / total if total else None,
        )
        for channel in channels
    ]


async def _sources(session: AsyncSession, window: Window) -> list[SourceCount]:
    rows = await repository.visits_by_source(session, window)
    total = sum(visits for _, visits in rows)
    return [
        SourceCount(source=source, visits=visits, share=visits / total) for source, visits in rows
    ]


async def summary(
    session: AsyncSession, store: StoreConfig, period: Period, now: datetime
) -> MetricsSummary:
    """Visitas, consultas y tasa del período contra el anterior, el gráfico, los canales y
    los orígenes. Se calcula en el momento."""
    periods = windows(period, now, store.store.zone)
    current = await _totals(session, periods.current)
    previous = await _totals(session, periods.previous)
    return MetricsSummary(
        period=period,
        visits=_count(current.visits, previous.visits),
        inquiries=_count(current.inquiries, previous.inquiries),
        rate=Rate(current=current.rate, previous=previous.rate),
        chart=await _chart(session, period, periods),
        channels=await _channels(session, store, periods.current),
        sources=await _sources(session, periods.current),
    )
