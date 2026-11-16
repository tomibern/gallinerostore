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


class FaqItem(BaseModel):
    """Una pregunta frecuente: cada encabezado ``##`` de las preguntas abre una."""

    question: str = Field(description="El texto del encabezado, sin los #.")
    answer_md: str = Field(description="La respuesta, en Markdown.")


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
    channels: list[Channel] = Field(
        description="Canales de contacto activos, en el orden en que se ofrecen."
    )
    general_inquiries: list[Inquiry] = Field(
        description="La consulta general (sin producto), una por canal activo."
    )
    on_order_notice: str | None = Field(
        description="El aviso de demora de los productos por encargue, si la tienda lo cargó."
    )
    how_to_buy_md: str = Field(description="«Cómo comprar» en Markdown (puede ser vacío).")
    faq_intro_md: str = Field(
        description="El texto de las preguntas frecuentes antes de la primera pregunta."
    )
    faq: list[FaqItem] = Field(description="Las preguntas frecuentes, en su orden.")
