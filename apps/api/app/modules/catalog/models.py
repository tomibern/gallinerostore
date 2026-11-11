"""Tablas del catálogo: productos, talles, categorías, colecciones y versiones."""

from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models import Base
from app.modules.media.service import StoredImage


class SaleMode(StrEnum):
    """Modo de venta: define en qué sección aparece el producto."""

    STOCK = "stock"
    ON_ORDER = "on_order"


class ProductStatus(StrEnum):
    """Estado: borrador → publicado ↔ oculto → archivado."""

    DRAFT = "draft"
    PUBLISHED = "published"
    HIDDEN = "hidden"
    ARCHIVED = "archived"


def _enum(enum_cls: type[StrEnum], name: str) -> Enum:
    # Texto con CHECK en vez de enum nativo de Postgres: sumar un valor es una
    # migración simple.
    return Enum(
        enum_cls,
        name=name,
        native_enum=False,
        create_constraint=True,
        length=20,
        values_callable=lambda e: [m.value for m in e],
    )


class Size(Base):
    __tablename__ = "sizes"
    __table_args__ = (UniqueConstraint("size_group", "label"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    label: Mapped[str] = mapped_column(String(20))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    size_group: Mapped[str] = mapped_column(String(40))


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    size_group: Mapped[str] = mapped_column(String(40))


class Collection(Base):
    __tablename__ = "collections"
    __table_args__ = (
        # Una sola colección por defecto: índice único sobre las filas con is_default.
        Index(
            "uq_collections_single_default",
            "is_default",
            unique=True,
            postgresql_where=text("is_default"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class Version(Base):
    __tablename__ = "versions"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Código permanente (ABC-014, con el prefijo de config/store.toml): lo asigna el
    # service al crear el producto.
    code: Mapped[str] = mapped_column(String(20), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    # No es único: el producto se identifica por código (renombrar no rompe links).
    slug: Mapped[str] = mapped_column(String(220), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    collection_id: Mapped[int] = mapped_column(ForeignKey("collections.id"))
    version_id: Mapped[int | None] = mapped_column(ForeignKey("versions.id"))
    season: Mapped[str | None] = mapped_column(String(40))
    sale_mode: Mapped[SaleMode] = mapped_column(_enum(SaleMode, "sale_mode"))
    # En la unidad menor de la moneda (ADR 0002).
    price: Mapped[int] = mapped_column(BigInteger)
    compare_at_price: Mapped[int | None] = mapped_column(BigInteger)
    status: Mapped[ProductStatus] = mapped_column(
        _enum(ProductStatus, "product_status"), default=ProductStatus.DRAFT
    )
    featured: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    model_group: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    sizes: Mapped[list["ProductSize"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    # En orden: la primera es la portada.
    images: Mapped[list["ProductImage"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductImage.sort_order",
    )


class ProductSize(Base):
    __tablename__ = "product_sizes"

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), primary_key=True
    )
    size_id: Mapped[int] = mapped_column(ForeignKey("sizes.id"), primary_key=True)
    # En stock: disponible ya. En encargue: talle que se puede pedir.
    in_stock: Mapped[bool] = mapped_column(Boolean, default=True)

    product: Mapped[Product] = relationship(back_populates="sizes")
    size: Mapped[Size] = relationship()


class Tag(Base):
    """Etiqueta libre (titular, alternativa, arquero…): filtros secundarios y colecciones."""

    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class ProductTag(Base):
    __tablename__ = "product_tags"

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)


class StoryItemKind(StrEnum):
    """Tipo de ítem de la historia del producto."""

    MILESTONE = "milestone"  # figurita: año, título y anécdota
    STAT = "stat"  # cifra
    FUN_FACT = "fun_fact"  # ¿Sabías que…?


class ProductStoryItem(Base):
    """Ítem de la historia del producto. Sin ítems, la sección no se muestra."""

    __tablename__ = "product_story_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[StoryItemKind] = mapped_column(_enum(StoryItemKind, "story_item_kind"))
    year: Mapped[int | None] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class ProductImage(Base):
    __tablename__ = "product_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    # Claves dentro del bucket, nunca URLs: el dominio de las fotos puede cambiar.
    path_full: Mapped[str] = mapped_column(String(300))
    path_thumb: Mapped[str] = mapped_column(String(300))
    alt: Mapped[str] = mapped_column(String(300))
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    product: Mapped[Product] = relationship(back_populates="images")

    @classmethod
    def from_stored(cls, product_id: int, stored: StoredImage, alt: str) -> "ProductImage":
        """La fila para una imagen ya subida: rutas, medidas y posición salen de ``stored``."""
        return cls(
            product_id=product_id,
            path_full=stored.path_full,
            path_thumb=stored.path_thumb,
            alt=alt,
            width=stored.width,
            height=stored.height,
            sort_order=stored.position,
        )


# Secuencia de códigos: nunca reutiliza números aunque se borren productos.
PRODUCT_CODE_SEQUENCE = "product_code_seq"

# Vista de solo lectura para el catálogo público: calcula «sin stock» (producto
# de stock sin ningún talle disponible). La crea la migración; no la toca
# autogenerate (ver alembic/env.py).
catalog_products = Table(
    "catalog_products",
    Base.metadata,
    Column("id", Integer, primary_key=True),
    Column("out_of_stock", Boolean),
    info={"is_view": True},
)
