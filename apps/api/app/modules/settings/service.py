"""Reglas de la configuración pública de la tienda, de los bloques de la home y de los
mensajes prearmados de las consultas."""

import logging
import re
from dataclasses import dataclass, field
from urllib.parse import quote

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import StoreConfig, StoreFeatures
from app.modules.settings import repository
from app.modules.settings.models import Channel, MessageCase
from app.modules.settings.schemas import (
    ContactChannels,
    HomeBlock,
    HomeSlideOut,
    Inquiry,
    PublicStore,
)

logger = logging.getLogger(__name__)

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


# Plantillas neutras del núcleo, por si la tienda no cargó la de un caso: así nunca
# falta un mensaje. Las de cada cliente van en su seed (y después las edita el admin).
DEFAULT_MESSAGE_TEMPLATES: dict[MessageCase, str] = {
    MessageCase.STOCK: "¡Hola! Me interesa {product} ({code}), talle {size} (en stock). {link}",
    MessageCase.OUT_OF_STOCK: (
        "¡Hola! Me interesa {product} ({code}), talle {size} "
        "(sin stock, consulto disponibilidad). {link}"
    ),
    MessageCase.ON_ORDER: (
        "¡Hola! Me interesa {product} ({code}), talle {size} (por encargue). {link}"
    ),
    MessageCase.SOLD_OUT_ON_ORDER: (
        "¡Hola! Me interesa {product} ({code}), talle {size} (se agotó, por encargue). {link}"
    ),
}

# Las variables que admite una plantilla. Cualquier otra cosa entre llaves queda tal cual.
_VARIABLE = re.compile(r"\{(product|code|size|link)\}")


def render_message(template: str, values: dict[str, str]) -> str:
    """Reemplaza las variables conocidas de una vez. A diferencia de ``str.format``, una
    llave suelta o una variable desconocida no rompen nada: quedan como texto."""
    return _VARIABLE.sub(lambda match: values[match.group(1)], template)


@dataclass(frozen=True)
class Contact:
    """Lo que hace falta para armar las consultas, leído una vez de la configuración."""

    channels: ContactChannels = field(default_factory=ContactChannels)
    templates: dict[str, str] = field(default_factory=dict)
    on_order_notice: str | None = None

    def template(self, case: MessageCase) -> str:
        return self.templates.get(case) or DEFAULT_MESSAGE_TEMPLATES[case]

    def inquiries(self, case: MessageCase, values: dict[str, str]) -> list[Inquiry]:
        """Una consulta por canal cargado, WhatsApp primero."""
        message = render_message(self.template(case), values)
        result: list[Inquiry] = []
        if self.channels.whatsapp:
            number = self.channels.whatsapp.number
            url = f"https://wa.me/{number}?text={quote(message, safe='')}"
            result.append(Inquiry(channel=Channel.WHATSAPP, message=message, url=url))
        if self.channels.instagram:
            username = quote(self.channels.instagram.username, safe="")
            url = f"https://ig.me/m/{username}"
            result.append(Inquiry(channel=Channel.INSTAGRAM, message=message, url=url))
        return result


def _channels(raw: dict[str, object], features: StoreFeatures) -> ContactChannels:
    """Los canales cargados que la tienda ofrece. Uno mal cargado se deja afuera (y se
    avisa en el log) en lugar de romper el detalle."""
    channels: dict[str, object] = {}
    for name, data in raw.items():
        try:
            ContactChannels.model_validate({name: data})
        except ValidationError:
            logger.warning("Canal de contacto mal cargado, se ignora: %s", name)
            continue
        channels[name] = data
    parsed = ContactChannels.model_validate(channels)
    if not features.instagram:
        parsed.instagram = None
    return parsed


async def contact(session: AsyncSession, features: StoreFeatures) -> Contact:
    """Canales, plantillas y aviso de encargue que edita el admin. Sin la fila de
    configuración no hay canales: no hay a quién escribirle."""
    store_settings = await repository.get_store_settings(session)
    if store_settings is None:
        return Contact()
    return Contact(
        channels=_channels(store_settings.contact_channels or {}, features),
        templates=store_settings.message_templates or {},
        on_order_notice=store_settings.on_order_notice or None,
    )
