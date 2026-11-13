"""Reglas de negocio del catálogo (sección, disponibilidad, encargues, categorías y código)."""

from collections.abc import Collection

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import StoreConfig
from app.modules.catalog import repository
from app.modules.catalog.models import Availability, ProductImage, SaleMode, Section
from app.modules.catalog.schemas import ImageOut, ProductListItem

MAX_CATEGORY_DEPTH = 2


class CategoryTooDeepError(ValueError):
    """Las categorías admiten como máximo dos niveles."""


def check_category_depth(slug: str, depth: int) -> None:
    """Valida el nivel de una categoría (1 = raíz). El admin la va a reusar al crear categorías."""
    if depth > MAX_CATEGORY_DEPTH:
        raise CategoryTooDeepError(
            f"La categoría «{slug}» quedaría en el nivel {depth}: "
            f"las categorías admiten como máximo dos niveles."
        )


class OnOrderWithSizesError(ValueError):
    """Un encargue no tiene talles propios: se pide en cualquiera del grupo de su categoría."""


def check_on_order_sizes(slug: str, sale_mode: SaleMode, size_labels: Collection[str]) -> None:
    """Rechaza talles propios en un encargue. El admin la va a reusar al cargar productos."""
    if sale_mode is SaleMode.ON_ORDER and size_labels:
        raise OnOrderWithSizesError(
            f"El producto «{slug}» es por encargue y trae talles ({', '.join(size_labels)}): "
            f"un encargue se pide en cualquier talle del grupo de su categoría. "
            f"Sacale los talles."
        )


async def new_product_code(session: AsyncSession, prefix: str) -> str:
    """Código permanente con el prefijo de la tienda: ABC-001, ABC-002… ABC-1000."""
    return f"{prefix}-{await repository.next_code_number(session):03d}"


def _image_out(image: ProductImage, media_base_url: str) -> ImageOut:
    base = media_base_url.rstrip("/")
    return ImageOut(
        full=f"{base}/{image.path_full}",
        thumb=f"{base}/{image.path_thumb}",
        alt=image.alt,
        width=image.width,
        height=image.height,
    )


def availability(section: Section, sold_out: bool) -> Availability:
    """Lo que ve el cliente: en stock, por encargue o agotado (en una u otra sección)."""
    if section is Section.ON_ORDER:
        return Availability.SOLD_OUT_ON_ORDER if sold_out else Availability.ON_ORDER
    return Availability.SOLD_OUT if sold_out else Availability.IN_STOCK


async def list_published(
    session: AsyncSession, store: StoreConfig, media_base_url: str, section: Section | None
) -> list[ProductListItem]:
    """Productos publicados, de una sección o de todas, en el orden manual."""
    rows = await repository.published_products(
        session, section=section, sold_out_goes_on_order=store.features.on_order
    )
    return [
        ProductListItem(
            code=product.code,
            name=product.name,
            slug=product.slug,
            price=product.price,
            currency=store.store.currency,
            section=product_section,
            availability=availability(product_section, sold_out),
            cover=_image_out(product.images[0], media_base_url) if product.images else None,
        )
        for product, product_section, sold_out in rows
    ]
