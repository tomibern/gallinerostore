"""Cuerpo de `POST /events`: un tipo por evento, cada uno con sus campos y ninguno más."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.modules.events.models import Device, Page
from app.modules.settings.models import Channel

# Al azar en el navegador: 16 bytes en hexadecimal. No identifica a nadie.
SessionId = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{32}$")]
# utm_source de la URL de entrada («historia», «bio»…) o «directo».
Source = Annotated[
    str, StringConstraints(strip_whitespace=True, to_lower=True, min_length=1, max_length=60)
]
ProductCode = Annotated[str, StringConstraints(min_length=1, max_length=20)]
SizeLabel = Annotated[str, StringConstraints(min_length=1, max_length=20)]
# Las visitas que se cuentan como páginas: la home, los listados y «Cómo comprar».
ViewPage = Literal[Page.HOME, Page.STOCK, Page.ON_ORDER, Page.HOW_TO_BUY]


class _EventBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: SessionId
    source: Source
    device: Device


class PageView(_EventBase):
    """Visita a la home, a un listado o a «Cómo comprar»."""

    type: Literal["page_view"]
    page: ViewPage


class ProductView(_EventBase):
    """Visita al detalle de un producto."""

    type: Literal["product_view"]
    product_code: ProductCode


class ContactClick(_EventBase):
    """Consulta por un producto: se tocó el link que abre el chat."""

    type: Literal["contact_click"]
    product_code: ProductCode
    channel: Channel
    size: SizeLabel


class GeneralContactClick(_EventBase):
    """Consulta general: se tocó el link que abre el chat, desde esa página."""

    type: Literal["general_contact_click"]
    channel: Channel
    page: Page


EventIn = Annotated[
    PageView | ProductView | ContactClick | GeneralContactClick, Field(discriminator="type")
]


class EventOut(BaseModel):
    """Un evento guardado, para verificar los e2e."""

    type: str
    product_code: str | None
    channel: Channel | None
    size: str | None
    page: str | None
    source: str | None
    device: str | None
