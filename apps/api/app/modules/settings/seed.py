"""Carga la configuración editable de la tienda desde la sección [settings] del seed.

Los datos (WhatsApp, Instagram, textos) son del cliente y viven en su
``config/seed.toml``; el núcleo solo sabe cargarlos. Es idempotente: siempre
actualiza la misma fila.
"""

import tomllib
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.settings import repository
from app.modules.settings.models import SETTINGS_ROW_ID, StoreSettings


class SettingsSeed(BaseModel):
    contact_channels: dict[str, dict[str, Any]] = {}
    how_to_buy_md: str = ""
    faq_md: str = ""
    on_order_notice: str = ""
    message_templates: dict[str, str] = {}


def load_settings_seed(path: Path) -> SettingsSeed | None:
    """La sección [settings] del seed, o None si el seed no la tiene."""
    with path.open("rb") as f:
        section = tomllib.load(f).get("settings")
    return SettingsSeed.model_validate(section) if section is not None else None


async def apply_settings_seed(session: AsyncSession, seed: SettingsSeed) -> None:
    settings = await repository.get_store_settings(session)
    if settings is None:
        settings = StoreSettings(id=SETTINGS_ROW_ID)
        repository.add(session, settings)
    for name, value in seed.model_dump().items():
        setattr(settings, name, value)
    await repository.flush(session)
