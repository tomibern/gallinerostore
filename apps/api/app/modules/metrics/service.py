"""Reglas de las métricas: qué rango cubre cada período, contra qué se compara y cómo
se arman la tasa, el gráfico, los canales, los orígenes y el ranking de productos
(glosario: **Visita**, **Tasa de consulta**, **Origen**)."""

from collections.abc import Callable, Collection
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
    ProductActivity,
    ProductRanking,
    RankedProduct,
    RankingSort,
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


def _shown_channels(store: StoreConfig, counts: dict[Channel, int]) -> list[Channel]:
    """Todos los canales, también los que no tuvieron consultas. Instagram apagado no
    aparece, salvo que haya consultas de antes de apagarlo."""
    return [
        channel
        for channel in Channel
        if channel is not Channel.INSTAGRAM or store.features.instagram or counts.get(channel)
    ]


async def _channels(
    session: AsyncSession, store: StoreConfig, window: Window
) -> list[ChannelCount]:
    counts = await repository.inquiries_by_channel(session, window)
    total = sum(counts.values())
    channels = _shown_channels(store, counts)
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


def _ranked(product: repository.ProductRef, counts: repository.ProductCounts) -> RankedProduct:
    inquiries = sum(counts.inquiries.values())
    return RankedProduct(
        code=product.code,
        name=product.name,
        status=product.status,
        visits=counts.visits,
        inquiries=inquiries,
        rate=_rate(inquiries, counts.visits),
        whatsapp=counts.inquiries.get(Channel.WHATSAPP, 0),
        instagram=counts.inquiries.get(Channel.INSTAGRAM, 0),
    )


_SORT_VALUE: dict[RankingSort, Callable[[RankedProduct], float | None]] = {
    RankingSort.VISITS: lambda item: item.visits,
    RankingSort.INQUIRIES: lambda item: item.inquiries,
    RankingSort.RATE: lambda item: item.rate,
    RankingSort.WHATSAPP: lambda item: item.whatsapp,
    RankingSort.INSTAGRAM: lambda item: item.instagram,
}


def _sort_key(sort: RankingSort, item: RankedProduct) -> tuple[float, int, int, str, str]:
    """De mayor a menor por la columna; sin tasa va al final. Empates: más consultas, más
    visitas y por nombre (y código, para que el orden sea siempre el mismo)."""
    value = _SORT_VALUE[sort](item)
    first = -1.0 if value is None else float(value)
    return (-first, -item.inquiries, -item.visits, item.name.casefold(), item.code)


async def product_ranking(
    session: AsyncSession, store: StoreConfig, period: Period, sort: RankingSort, now: datetime
) -> ProductRanking:
    """Los productos con visitas o consultas en el período, archivados incluidos, con su
    tasa y sus consultas por canal. Las mismas reglas de visita y consulta del resumen."""
    window = windows(period, now, store.store.zone).current
    counts = await repository.counts_by_product(session, window)
    products = await repository.products_by_id(session, counts.keys())
    items = sorted(
        (_ranked(products[product_id], counts[product_id]) for product_id in products),
        key=lambda item: _sort_key(sort, item),
    )
    by_channel = {
        Channel.WHATSAPP: sum(item.whatsapp for item in items),
        Channel.INSTAGRAM: sum(item.instagram for item in items),
    }
    return ProductRanking(
        period=period, sort=sort, channels=_shown_channels(store, by_channel), items=items
    )


async def activity_last_7_days(
    session: AsyncSession, store: StoreConfig, now: datetime, product_ids: Collection[int]
) -> dict[int, ProductActivity]:
    """Visitas al detalle y consultas de esos productos en los últimos 7 días (el mismo
    período «7d» del ranking). Todos los pedidos tienen su entrada, aunque sea en cero."""
    window = windows(Period.LAST_7_DAYS, now, store.store.zone).current
    counts = await repository.counts_by_product(session, window, product_ids)
    empty = repository.ProductCounts()
    return {
        product_id: ProductActivity(
            visits=counts.get(product_id, empty).visits,
            inquiries=sum(counts.get(product_id, empty).inquiries.values()),
        )
        for product_id in product_ids
    }
