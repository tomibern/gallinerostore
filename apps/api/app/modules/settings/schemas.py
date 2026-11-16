from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.core.config import StoreFeatures
from app.modules.settings.models import Channel


class HomeSlideOut(BaseModel):
    full: str = Field(description="Ruta de la foto (lado mayor 1600 px), bajo /media.")
    alt: str


class HomeBlock(BaseModel):
    """Un bloque con carrusel de la home. Sus textos salen del diccionario de la web
    (``home.blocks.<key>.*``); la API solo da la clave y las fotos."""

    key: str = Field(description="Clave del bloque, declarada en la configuración de la tienda.")
    slides: list[HomeSlideOut] = Field(
        description="Hasta 4 fotos, en su orden. Vacía si el bloque todavía no tiene fotos."
    )


class PublicStore(BaseModel):
    """Lo que la web necesita saber de la tienda. Nada secreto."""

    name: str
    locale: str
    currency: str
    price_decimals: int
    collection_label: str
    features: StoreFeatures
    home_blocks: list[HomeBlock] = Field(
        description="Bloques con carrusel de la home, en el orden de la configuración."
    )


class WhatsAppContact(BaseModel):
    # Número internacional sin «+», espacios ni guiones, como lo pide wa.me. Hasta 15
    # dígitos (E.164); el mínimo de 8 es una elección. La regla de cada país (el 9 de
    # los celulares de Argentina) es del cliente, no del núcleo.
    number: Annotated[str, StringConstraints(pattern=r"^[0-9]{8,15}$")]


class InstagramContact(BaseModel):
    # Usuario sin «@»: letras, números, puntos y guiones bajos, hasta 30.
    username: Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9._]{1,30}$")]


class ContactChannels(BaseModel):
    """Los datos de cada canal de contacto. Un canal sin datos no se ofrece."""

    model_config = ConfigDict(extra="forbid")

    whatsapp: WhatsAppContact | None = None
    instagram: InstagramContact | None = None


class Inquiry(BaseModel):
    """Una consulta lista para usar: el mensaje prearmado y el link que abre el chat."""

    channel: Channel
    message: str = Field(description="El mensaje prearmado, ya armado.")
    url: str = Field(
        description=(
            "WhatsApp: wa.me con el mensaje en el texto. Instagram: el chat (ig.me) sin "
            "texto, porque no lo acepta; el mensaje se muestra aparte para copiarlo."
        )
    )
