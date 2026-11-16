"""Carga la configuración editable de la tienda ([settings]) y las fotos de los
bloques de la home ([[home_slides]]) desde el seed.

Los datos (WhatsApp, Instagram, textos) son del cliente y viven en su
``config/seed.toml``; el núcleo solo sabe cargarlos. Solo crea la fila si no
existe: después la edita el admin y repetir el seed no pisa sus cambios. Para
volver a los valores del seed, ``make reset``.
"""

import tomllib
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import StoreConfig
from app.core.storage import ObjectStorage
from app.modules.media.placeholder import placeholder_image
from app.modules.media.service import store_home_slide
from app.modules.settings import repository
from app.modules.settings.models import SETTINGS_ROW_ID, HomeSlide, StoreSettings
from app.modules.settings.service import check_slide_count


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


async def apply_settings_seed(session: AsyncSession, seed: SettingsSeed) -> bool:
    """Crea la fila de configuración con los valores del seed. Devuelve True si la creó."""
    if await repository.get_store_settings(session) is not None:
        return False
    store_settings = StoreSettings(id=SETTINGS_ROW_ID, **seed.model_dump())
    repository.add(session, store_settings)
    await repository.flush(session)
    return True


class HomeSlideSeed(BaseModel):
    """Una foto de prueba de un bloque de la home: el seed dibuja una imagen con el texto."""

    block: str
    alt: str


def load_home_slides_seed(path: Path) -> list[HomeSlideSeed]:
    """Las fotos de [[home_slides]] del seed, en orden (vacía si no tiene)."""
    with path.open("rb") as f:
        slides = tomllib.load(f).get("home_slides", [])
    return [HomeSlideSeed.model_validate(slide) for slide in slides]


async def apply_home_slides_seed(
    session: AsyncSession, seed: list[HomeSlideSeed], store: StoreConfig, storage: ObjectStorage
) -> list[str]:
    """Carga las fotos de cada bloque que todavía no tiene ninguna. Devuelve los bloques
    cargados: un bloque con fotos ya lo maneja el admin y el seed no lo toca."""
    by_block: dict[str, list[HomeSlideSeed]] = {}
    for slide in seed:
        by_block.setdefault(slide.block, []).append(slide)
    undeclared = sorted(set(by_block) - set(store.home.blocks))
    if undeclared:
        raise ValueError(
            f"El seed trae fotos de bloques que [home] no declara: {', '.join(undeclared)}"
        )
    for block, slides in by_block.items():
        check_slide_count(block, len(slides))

    loaded: list[str] = []
    for block, slides in by_block.items():
        if await repository.count_slides(session, block):
            continue
        for position, slide in enumerate(slides):
            image = placeholder_image(slide.alt, f"{block} {position + 1}")
            path = store_home_slide(storage, block, position, image)
            repository.add(
                session, HomeSlide(block=block, path_full=path, alt=slide.alt, sort_order=position)
            )
        loaded.append(block)
    await repository.flush(session)
    return loaded
