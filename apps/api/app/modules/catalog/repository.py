"""Acceso a datos del catálogo con SQLAlchemy."""

from collections.abc import Sequence

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.catalog.models import (
    PRODUCT_CODE_SEQUENCE,
    Product,
    ProductSize,
    ProductStatus,
    catalog_products,
)


async def next_code_number(session: AsyncSession) -> int:
    """Próximo número de la secuencia de códigos. Nunca se repite, aunque haya rollback."""
    result = await session.execute(text(f"SELECT nextval('{PRODUCT_CODE_SEQUENCE}')"))
    return int(result.scalar_one())


async def published_with_stock_flag(session: AsyncSession) -> Sequence[tuple[Product, bool]]:
    """Productos publicados con sus talles y el indicador «sin stock» de la vista."""
    stmt = (
        select(Product, catalog_products.c.out_of_stock)
        .join(catalog_products, catalog_products.c.id == Product.id)
        .where(Product.status == ProductStatus.PUBLISHED)
        .options(selectinload(Product.sizes).selectinload(ProductSize.size))
        .order_by(Product.sort_order, Product.id)
    )
    result = await session.execute(stmt)
    return [(product, bool(out_of_stock)) for product, out_of_stock in result.all()]
