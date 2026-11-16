"""Reglas de la configuración pública de la tienda y de los bloques de la home."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import StoreConfig
from app.modules.settings import repository
from app.modules.settings.schemas import HomeBlock, HomeSlideOut, PublicStore

MAX_SLIDES_PER_BLOCK = 4


class TooManySlidesError(ValueError):
    """Un bloque de la home tiene como máximo cuatro fotos."""


def check_slide_count(block: str, count: int) -> None:
    """Valida la cantidad de fotos de un bloque. El admin la va a reusar al subir fotos."""
    if count > MAX_SLIDES_PER_BLOCK:
        raise TooManySlidesError(
            f"El bloque «{block}» tendría {count} fotos: "
            f"un bloque de la home admite como máximo {MAX_SLIDES_PER_BLOCK}."
        )


async def home_blocks(
    session: AsyncSession, config: StoreConfig, media_base_url: str
) -> list[HomeBlock]:
    """Los bloques declarados en la configuración, en su orden, con sus fotos."""
    keys = config.home.blocks
    if not keys:
        return []
    base = media_base_url.rstrip("/")
    slides: dict[str, list[HomeSlideOut]] = {key: [] for key in keys}
    for slide in await repository.slides_for_blocks(session, keys, MAX_SLIDES_PER_BLOCK):
        slides[slide.block].append(HomeSlideOut(full=f"{base}/{slide.path_full}", alt=slide.alt))
    return [HomeBlock(key=key, slides=slides[key]) for key in keys]


async def public_store(
    session: AsyncSession, config: StoreConfig, media_base_url: str
) -> PublicStore:
    store = config.store
    return PublicStore(
        name=store.name,
        locale=store.locale,
        currency=store.currency,
        price_decimals=store.price_decimals,
        collection_label=store.collection_label,
        features=config.features,
        home_blocks=await home_blocks(session, config, media_base_url),
    )


async def on_order_notice(session: AsyncSession) -> str | None:
    """El aviso de encargue que edita el admin, o None si no está cargado."""
    store_settings = await repository.get_store_settings(session)
    return (store_settings.on_order_notice or None) if store_settings else None
