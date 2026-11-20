"""Agregaciones sobre la tabla events, en el momento y sin tablas resumen.

Todas reciben una ``Window``: un rango de horas y la zona de la tienda, que define los
días (para no contar dos veces una visita) y las horas o días del gráfico. Las horas
y los días que devuelven son de la zona de la tienda, sin zona.
"""

from collections.abc import Collection
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

from sqlalchemy import Date, String, Subquery, cast, func, literal, select
from sqlalchemy.dialects.postgresql import aggregate_order_by
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.modules.catalog.models import Product, ProductStatus
from app.modules.events.models import DIRECT_SOURCE, Event, EventType
from app.modules.settings.models import Channel

VIEW_TYPES = (EventType.PAGE_VIEW, EventType.PRODUCT_VIEW)
INQUIRY_TYPES = (EventType.CONTACT_CLICK, EventType.GENERAL_CONTACT_CLICK)

Unit = Literal["hour", "day"]


@dataclass(frozen=True)
class Window:
    """Rango ``[start, end)`` (horas con zona) y la zona de la tienda (nombre IANA)."""

    start: datetime
    end: datetime
    timezone: str


def _inline(value: str) -> ColumnElement[str]:
    """Un valor fijo escrito en el SQL: así la misma expresión en el SELECT y en el GROUP BY
    es idéntica para Postgres (con parámetros distintos no lo sería)."""
    return literal(value, literal_execute=True)


def _local(timezone: str) -> ColumnElement[datetime]:
    """La hora del evento en la zona de la tienda."""
    return func.timezone(_inline(timezone), Event.created_at)


def _bucket(unit: Unit, at: ColumnElement[datetime]) -> ColumnElement[datetime]:
    return func.date_trunc(_inline(unit), at)


def _in_range(types: tuple[EventType, ...], window: Window) -> tuple[ColumnElement[bool], ...]:
    return (
        Event.type.in_(types),
        Event.created_at >= window.start,
        Event.created_at < window.end,
    )


def _visits(window: Window, *conditions: ColumnElement[bool]) -> Subquery:
    """Una fila por visita: un par distinto de sesión, página o producto, y día de la
    tienda. Un evento sin sesión es una visita por sí solo. La visita queda en la hora
    de su primer evento y con el origen de ese evento («directo» es ninguno).
    ``conditions`` acota los eventos (por ejemplo, a algunos productos)."""
    local = _local(window.timezone)
    first_source = func.array_agg(aggregate_order_by(Event.source, Event.created_at, Event.id))[1]
    # Sin sesión, el id del evento la reemplaza: nunca coincide con otro.
    visitor = func.coalesce(Event.session_id, cast(Event.id, String))
    return (
        select(
            Event.type.label("type"),
            Event.product_id.label("product_id"),
            func.min(local).label("at"),
            func.nullif(first_source, DIRECT_SOURCE).label("source"),
        )
        .where(*_in_range(VIEW_TYPES, window), *conditions)
        .group_by(visitor, Event.type, Event.page, Event.product_id, cast(local, Date))
        .subquery()
    )


async def visits_by_type(session: AsyncSession, window: Window) -> dict[EventType, int]:
    visits = _visits(window)
    rows = await session.execute(select(visits.c.type, func.count()).group_by(visits.c.type))
    return {EventType(type_): count for type_, count in rows}


async def visits_by_bucket(
    session: AsyncSession, window: Window, unit: Unit
) -> dict[datetime, int]:
    visits = _visits(window)
    bucket = _bucket(unit, visits.c.at)
    rows = await session.execute(select(bucket, func.count()).group_by(bucket))
    return {at: count for at, count in rows}


async def visits_by_source(session: AsyncSession, window: Window) -> list[tuple[str | None, int]]:
    """Visitas por origen (sin origen, None), de más a menos."""
    visits = _visits(window)
    count = func.count()
    rows = await session.execute(
        select(visits.c.source, count)
        .group_by(visits.c.source)
        .order_by(count.desc(), visits.c.source.nulls_last())
    )
    return [(source, visits_) for source, visits_ in rows]


async def inquiries_by_type(session: AsyncSession, window: Window) -> dict[EventType, int]:
    rows = await session.execute(
        select(Event.type, func.count())
        .where(*_in_range(INQUIRY_TYPES, window))
        .group_by(Event.type)
    )
    return {EventType(type_): count for type_, count in rows}


async def inquiries_by_bucket(
    session: AsyncSession, window: Window, unit: Unit
) -> dict[datetime, int]:
    bucket = _bucket(unit, _local(window.timezone))
    rows = await session.execute(
        select(bucket, func.count()).where(*_in_range(INQUIRY_TYPES, window)).group_by(bucket)
    )
    return {at: count for at, count in rows}


async def inquiries_by_channel(session: AsyncSession, window: Window) -> dict[Channel, int]:
    rows = await session.execute(
        select(Event.channel, func.count())
        .where(*_in_range(INQUIRY_TYPES, window))
        .group_by(Event.channel)
    )
    return {Channel(channel): count for channel, count in rows if channel is not None}


@dataclass(frozen=True)
class ProductCounts:
    """Visitas al detalle y consultas de un producto en un rango, por canal."""

    visits: int = 0
    inquiries: dict[Channel, int] = field(default_factory=dict)


def _of_products(product_ids: Collection[int] | None) -> tuple[ColumnElement[bool], ...]:
    """Eventos de un producto que todavía existe; de esos productos, si se dicen."""
    if product_ids is None:
        return (Event.product_id.is_not(None),)
    return (Event.product_id.in_(product_ids),)


async def counts_by_product(
    session: AsyncSession, window: Window, product_ids: Collection[int] | None = None
) -> dict[int, ProductCounts]:
    """Visitas al detalle y consultas por producto (con las mismas reglas de los
    totales), de todos los que tuvieron alguna en el rango o solo de ``product_ids``.
    Un producto sin nada no aparece."""
    if product_ids is not None and not product_ids:
        return {}
    of_products = _of_products(product_ids)
    visits = _visits(window, Event.type == EventType.PRODUCT_VIEW, *of_products)
    visit_rows = await session.execute(
        select(visits.c.product_id, func.count()).group_by(visits.c.product_id)
    )
    inquiry_rows = await session.execute(
        select(Event.product_id, Event.channel, func.count())
        .where(*_in_range((EventType.CONTACT_CLICK,), window), *of_products)
        .group_by(Event.product_id, Event.channel)
    )
    visits_by_id: dict[int, int] = {product_id: count for product_id, count in visit_rows}
    inquiries_by_id: dict[int, dict[Channel, int]] = {}
    for product_id, channel, count in inquiry_rows:
        if product_id is not None and channel is not None:
            inquiries_by_id.setdefault(product_id, {})[Channel(channel)] = count
    return {
        product_id: ProductCounts(
            visits=visits_by_id.get(product_id, 0),
            inquiries=inquiries_by_id.get(product_id, {}),
        )
        for product_id in visits_by_id.keys() | inquiries_by_id.keys()
    }


@dataclass(frozen=True)
class ProductRef:
    """Lo que el ranking muestra de un producto, en cualquier estado."""

    code: str
    name: str
    status: ProductStatus


async def products_by_id(
    session: AsyncSession, product_ids: Collection[int]
) -> dict[int, ProductRef]:
    """Código, nombre y estado de esos productos, en cualquier estado."""
    if not product_ids:
        return {}
    rows = await session.execute(
        select(Product.id, Product.code, Product.name, Product.status).where(
            Product.id.in_(product_ids)
        )
    )
    return {
        product_id: ProductRef(code=code, name=name, status=ProductStatus(status))
        for product_id, code, name, status in rows
    }
