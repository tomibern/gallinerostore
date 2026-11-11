"""Configuración editable de la tienda y fotos de los carruseles de la home."""

from typing import Any

from sqlalchemy import CheckConstraint, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base

SETTINGS_ROW_ID = 1


class StoreSettings(Base):
    """La fila única con lo que el admin edita. Lo técnico va en config/store.toml."""

    __tablename__ = "settings"
    __table_args__ = (CheckConstraint(f"id = {SETTINGS_ROW_ID}", name="single_row"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=SETTINGS_ROW_ID)
    # Canal → datos de contacto, por ejemplo {"whatsapp": {"number": "..."}}.
    contact_channels: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    how_to_buy_md: Mapped[str] = mapped_column(Text, default="")
    faq_md: Mapped[str] = mapped_column(Text, default="")
    on_order_notice: Mapped[str] = mapped_column(Text, default="")
    # Plantillas de los mensajes prearmados, por caso (stock, sin stock, encargue…).
    message_templates: Mapped[dict[str, str]] = mapped_column(JSONB, default=dict)


class HomeSlide(Base):
    """Foto de un carrusel de la home. Máximo 4 por bloque (se valida en la API)."""

    __tablename__ = "home_slides"

    id: Mapped[int] = mapped_column(primary_key=True)
    block: Mapped[str] = mapped_column(String(40), index=True)
    path_full: Mapped[str] = mapped_column(String(300))
    alt: Mapped[str] = mapped_column(String(300))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
