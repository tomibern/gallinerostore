"""Acceso a la tabla events."""

from collections.abc import Sequence

from sqlalchemy import Row, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.models import Product, Size
from app.modules.events.models import Event


async def save(session: AsyncSession, event: Event) -> None:
    """Guarda el evento. Es el único endpoint público que escribe: confirma acá."""
    session.add(event)
    await session.commit()


async def for_session(
    session: AsyncSession, session_id: str
) -> Sequence[Row[Event, str | None, str | None]]:
    """Los eventos de una sesión en el orden en que llegaron, con el código del producto y
    la etiqueta del talle."""
    stmt = (
        select(Event, Product.code, Size.label)
        .outerjoin(Product, Product.id == Event.product_id)
        .outerjoin(Size, Size.id == Event.size_id)
        .where(Event.session_id == session_id)
        .order_by(Event.id)
    )
    return (await session.execute(stmt)).all()
