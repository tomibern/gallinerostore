"""Acceso a datos de la configuración editable de la tienda."""

from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.settings.models import SETTINGS_ROW_ID, HomeSlide, StoreSettings


async def get_store_settings(session: AsyncSession) -> StoreSettings | None:
    return await session.get(StoreSettings, SETTINGS_ROW_ID)


def add(session: AsyncSession, row: StoreSettings | HomeSlide) -> None:
    session.add(row)


async def flush(session: AsyncSession) -> None:
    await session.flush()


async def commit(session: AsyncSession) -> None:
    await session.commit()


async def slides_for_blocks(
    session: AsyncSession, blocks: Sequence[str], per_block: int
) -> Sequence[HomeSlide]:
    """Las primeras ``per_block`` fotos de cada bloque, por orden de carga."""
    position = (
        func.row_number()
        .over(partition_by=HomeSlide.block, order_by=(HomeSlide.sort_order, HomeSlide.id))
        .label("position")
    )
    ranked = select(HomeSlide.id, position).where(HomeSlide.block.in_(blocks)).subquery()
    stmt = (
        select(HomeSlide)
        .join(ranked, ranked.c.id == HomeSlide.id)
        .where(ranked.c.position <= per_block)
        .order_by(HomeSlide.block, ranked.c.position)
    )
    return (await session.scalars(stmt)).all()


async def count_slides(session: AsyncSession, block: str) -> int:
    stmt = select(func.count()).select_from(HomeSlide).where(HomeSlide.block == block)
    return int(await session.scalar(stmt) or 0)
