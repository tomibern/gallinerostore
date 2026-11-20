import re
from typing import Annotated, Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    ValidationInfo,
    field_validator,
)
from pydantic_core import PydanticCustomError

from app.core.config import StoreFeatures
from app.modules.settings.models import Channel, MessageCase, MessageVariable, case_variables


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


# --- Admin: contacto, mensajes prearmados y aviso de encargue -------------------------

# Cualquier cosa entre llaves cuenta como variable: así un error de tipeo («{talle}»)
# se avisa en lugar de llegar tal cual al chat.
_PLACEHOLDER = re.compile(r"\{([^{}]*)\}")

# Sin recortar espacios: uno al final puede ser a propósito («Busco: »), para que la
# persona siga escribiendo en el chat.
TemplateText = Annotated[str, StringConstraints(max_length=1000)]


def check_template_variables(case: MessageCase, template: str) -> str:
    """Rechaza una variable que no existe o que no es de ese caso (la consulta general
    no tiene producto)."""
    if not template.strip():
        raise PydanticCustomError("blank", "El mensaje no puede quedar vacío.")
    allowed = {variable.value for variable in case_variables(case)}
    for match in _PLACEHOLDER.finditer(template):
        name = match.group(1)
        if name not in allowed:
            raise PydanticCustomError(
                "unknown_variable",
                "La variable «{variable}» no existe en este mensaje.",
                {"variable": name, "allowed": sorted(allowed)},
            )
    return template


class MessageTemplates(BaseModel):
    """Las cinco plantillas de los mensajes prearmados, una por caso (MessageCase)."""

    model_config = ConfigDict(extra="forbid")

    stock: TemplateText
    out_of_stock: TemplateText
    on_order: TemplateText
    sold_out_on_order: TemplateText
    general: TemplateText

    @field_validator("*")
    @classmethod
    def _known_variables(cls, value: str, info: ValidationInfo) -> str:
        assert info.field_name is not None
        return check_template_variables(MessageCase(info.field_name), value)


class AdminSettingsIn(BaseModel):
    """Lo que guarda la sección Contacto: canales, plantillas y aviso de encargue."""

    model_config = ConfigDict(extra="forbid")

    contact_channels: ContactChannels = Field(
        description="Un canal en null (o sin cargar) no se ofrece en la tienda."
    )
    message_templates: MessageTemplates
    on_order_notice: Annotated[str, StringConstraints(strip_whitespace=True, max_length=2000)] = (
        Field(
            description="El aviso general de demora y seña de los encargues. Vacío: no se muestra."
        )
    )

    @field_validator("contact_channels", mode="before")
    @classmethod
    def _as_people_write_them(cls, value: Any) -> Any:
        """El admin escribe el número como lo ve («+54 9 2920 34-2004») y el usuario con
        «@»: se guardan como los piden wa.me e ig.me. El seed, en cambio, ya los trae así."""
        if not isinstance(value, dict):
            return value
        channels = dict(value)
        whatsapp, instagram = channels.get("whatsapp"), channels.get("instagram")
        if isinstance(whatsapp, dict) and isinstance(whatsapp.get("number"), str):
            number = re.sub(r"[\s+().-]", "", whatsapp["number"])
            channels["whatsapp"] = whatsapp | {"number": number}
        if isinstance(instagram, dict) and isinstance(instagram.get("username"), str):
            username = instagram["username"].strip().removeprefix("@")
            channels["instagram"] = instagram | {"username": username}
        return channels


class AdminSettings(AdminSettingsIn):
    """Lo que edita el admin en Contacto, con las variables que admite cada plantilla."""

    message_variables: dict[MessageCase, list[MessageVariable]] = Field(
        description="Las variables que se pueden insertar en la plantilla de cada caso."
    )


class MessagePreviewIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case: MessageCase
    template: TemplateText

    @field_validator("template")
    @classmethod
    def _known_variables(cls, value: str, info: ValidationInfo) -> str:
        case = info.data.get("case")
        if case is None:  # el caso ya vino con su propio error
            return value
        return check_template_variables(case, value)


class PreviewProduct(BaseModel):
    code: str
    name: str
    size: str


class MessagePreview(BaseModel):
    """El mensaje armado por la API, como lo recibiría el chat (ADR 0005)."""

    message: str
    product: PreviewProduct | None = Field(
        description=(
            "El producto publicado con el que se armó, o null en la consulta general "
            "(o si todavía no hay productos publicados)."
        )
    )


# --- Admin: «Cómo comprar» y preguntas frecuentes -------------------------------------

# La regla que parte «Cómo comprar» y las preguntas en partes (``service.split_headings``):
# un encabezado de dos numerales (no tres), «## Título», con un cierre opcional «##»,
# salvo dentro de un bloque de código cercado.
HEADING_LINE = re.compile(r"^##(?:[ \t]+(.*))?$")
FENCE_LINE = re.compile(r"^(?:```|~~~)")

MAX_ITEMS = 30


def check_heading(value: str) -> str:
    """Un título o una pregunta: una sola línea y no vacía."""
    value = value.strip()
    if not value:
        raise PydanticCustomError("blank", "No puede quedar vacío.")
    if "\n" in value or "\r" in value:
        raise PydanticCustomError("multiline", "Va en una sola línea.")
    return value


def check_body(value: str) -> str:
    """El texto de un tema o la respuesta de una pregunta: Markdown que no abre otra
    parte ni deja un bloque de código sin cerrar (que se tragaría las siguientes)."""
    value = value.strip()
    in_fence = False
    for line in value.splitlines():
        if FENCE_LINE.match(line):
            in_fence = not in_fence
        elif not in_fence and HEADING_LINE.match(line):
            raise PydanticCustomError(
                "section_heading", "Una línea no puede empezar con dos numerales."
            )
    if in_fence:
        raise PydanticCustomError("unclosed_fence", "Hay un bloque de código sin cerrar.")
    return value


HeadingText = Annotated[str, StringConstraints(max_length=200)]
SectionText = Annotated[str, StringConstraints(max_length=5000)]


class HowToBuyTopic(BaseModel):
    """Un tema de «Cómo comprar» (pagos, envíos…): título y texto. Se guarda como un
    ``##`` cada uno."""

    model_config = ConfigDict(extra="forbid")

    title: HeadingText = Field(description="El título, en una línea. No puede quedar vacío.")
    text: SectionText = Field(description="El texto, en Markdown. Puede quedar vacío.")

    check_title = field_validator("title")(check_heading)
    check_text = field_validator("text")(check_body)


class FaqEntry(BaseModel):
    """Una pregunta frecuente para editar: pregunta y respuesta."""

    model_config = ConfigDict(extra="forbid")

    question: HeadingText = Field(description="La pregunta, en una línea. No puede quedar vacía.")
    answer: SectionText = Field(description="La respuesta, en Markdown. Puede quedar vacía.")

    check_question = field_validator("question")(check_heading)
    check_answer = field_validator("answer")(check_body)


class HowToBuyContent(BaseModel):
    """«Cómo comprar» y las preguntas frecuentes como listas, en su orden. Lo que se
    guarda reemplaza todo: agregar, ordenar y borrar es mandar la lista nueva."""

    model_config = ConfigDict(extra="forbid")

    topics: list[HowToBuyTopic] = Field(max_length=MAX_ITEMS)
    faq: list[FaqEntry] = Field(max_length=MAX_ITEMS)
