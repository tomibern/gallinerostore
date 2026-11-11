"""Reglas de negocio del catálogo (modo de venta, sin stock, código, estado)."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import StoreConfig
from app.modules.catalog import repository
from app.modules.catalog.schemas import ProductListItem, ProductSizeOut

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


async def new_product_code(session: AsyncSession, prefix: str) -> str:
    """Código permanente con el prefijo de la tienda: ABC-001, ABC-002… ABC-1000."""
    return f"{prefix}-{await repository.next_code_number(session):03d}"


async def list_published(session: AsyncSession, store: StoreConfig) -> list[ProductListItem]:
    rows = await repository.published_with_stock_flag(session)
    return [
        ProductListItem(
            code=product.code,
            name=product.name,
            slug=product.slug,
            price=product.price,
            currency=store.store.currency,
            sale_mode=product.sale_mode,
            out_of_stock=out_of_stock,
            sizes=[
                ProductSizeOut(label=ps.size.label, in_stock=ps.in_stock)
                for ps in sorted(product.sizes, key=lambda ps: ps.size.sort_order)
            ],
        )
        for product, out_of_stock in rows
    ]
