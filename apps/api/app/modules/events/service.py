"""Reglas de los eventos: a qué producto y talle apuntan, y si se guardan."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import StoreConfig
from app.modules.catalog import service as catalog_service
from app.modules.events import repository
from app.modules.events.models import Event, EventType
from app.modules.events.schemas import (
    ContactClick,
    EventIn,
    EventOut,
    GeneralContactClick,
    PageView,
    ProductView,
)


class InvalidEventError(ValueError):
    """El evento apunta a un producto que no está en el catálogo público o a un talle que
    el producto no ofrece."""


async def _product_and_size(
    session: AsyncSession, store: StoreConfig, code: str, size: str | None
) -> tuple[int, int | None]:
    product = await catalog_service.offered_product(session, store, code)
    if product is None:
        raise InvalidEventError(f"No hay un producto publicado con el código «{code}».")
    if size is None:
        return product.id, None
    if size not in product.size_ids:
        raise InvalidEventError(f"El producto «{code}» no ofrece el talle «{size}».")
    return product.id, product.size_ids[size]


async def record(session: AsyncSession, store: StoreConfig, event: EventIn) -> None:
    """Guarda el evento sin nada que identifique a la persona. Con las métricas apagadas
    lo valida igual, pero no lo guarda."""
    row = Event(
        type=EventType(event.type),
        session_id=event.session_id,
        source=event.source,
        device=event.device,
    )
    match event:
        case PageView(page=page) | GeneralContactClick(page=page):
            row.page = page
        case ProductView(product_code=code):
            row.product_id, _ = await _product_and_size(session, store, code, None)
        case ContactClick(product_code=code, size=size):
            row.product_id, row.size_id = await _product_and_size(session, store, code, size)
    if isinstance(event, ContactClick | GeneralContactClick):
        row.channel = event.channel
    if store.features.metrics:
        await repository.save(session, row)


async def for_session(session: AsyncSession, session_id: str) -> list[EventOut]:
    """Los eventos guardados de una sesión (para verificar los e2e)."""
    return [
        EventOut(
            type=event.type,
            product_code=code,
            channel=event.channel,
            size=size,
            page=event.page,
            source=event.source,
            device=event.device,
        )
        for event, code, size in await repository.for_session(session, session_id)
    ]
