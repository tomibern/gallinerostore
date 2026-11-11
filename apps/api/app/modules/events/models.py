"""Eventos de interés: visitas y consultas, sin datos personales ni cookies."""

from datetime import datetime
from enum import StrEnum

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base, text_enum


class EventType(StrEnum):
    PAGE_VIEW = "page_view"  # visita a la home o a un listado
    PRODUCT_VIEW = "product_view"  # visita al detalle de un producto
    CONTACT_CLICK = "contact_click"  # consulta por un producto
    GENERAL_CONTACT_CLICK = "general_contact_click"  # consulta general


class Channel(StrEnum):
    """Canal de contacto de una consulta."""

    WHATSAPP = "whatsapp"
    INSTAGRAM = "instagram"


class Event(Base):
    """Un evento anónimo. Nada que identifique a una persona: ni IP, ni user agent, ni
    datos de contacto. ``session_id`` es un identificador al azar que sirve para no
    contar visitas repetidas."""

    __tablename__ = "events"
    __table_args__ = (
        Index("ix_events_type_created_at", "type", "created_at"),
        Index("ix_events_product_id_created_at", "product_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    type: Mapped[EventType] = mapped_column(text_enum(EventType, "event_type", length=30))
    # SET NULL: archivar es lo habitual, pero si se borra un borrador no se pierden métricas.
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"))
    channel: Mapped[Channel | None] = mapped_column(text_enum(Channel, "event_channel", length=30))
    size_id: Mapped[int | None] = mapped_column(ForeignKey("sizes.id", ondelete="SET NULL"))
    # Origen del tráfico (utm_source: bio, historia, link compartido…).
    source: Mapped[str | None] = mapped_column(String(60))
    # Tipo de dispositivo (celular, computadora), no el modelo ni el navegador.
    device: Mapped[str | None] = mapped_column(String(20))
    session_id: Mapped[str | None] = mapped_column(String(64))
    # Página en las visitas a listados y en las consultas generales.
    page: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
