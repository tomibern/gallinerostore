"""Acceso a datos de la configuración editable de la tienda."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.settings.models import SETTINGS_ROW_ID, StoreSettings


async def get_store_settings(session: AsyncSession) -> StoreSettings | None:
    return await session.get(StoreSettings, SETTINGS_ROW_ID)


def add(session: AsyncSession, settings: StoreSettings) -> None:
    session.add(settings)


async def flush(session: AsyncSession) -> None:
    await session.flush()
