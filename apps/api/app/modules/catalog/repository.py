"""Acceso a datos del catálogo con SQLAlchemy."""

from collections.abc import Sequence

from sqlalchemy import ColumnElement, case, exists, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.models import Base
from app.modules.catalog.models import (
    PRODUCT_CODE_SEQUENCE,
    Category,
    Collection,
    Product,
    ProductImage,
    ProductStatus,
    SaleMode,
    Section,
    Size,
    Tag,
    Version,
    catalog_products,
)


async def next_code_number(session: AsyncSession) -> int:
    """Próximo número de la secuencia de códigos. Nunca se repite, aunque haya rollback."""
    result = await session.execute(text(f"SELECT nextval('{PRODUCT_CODE_SEQUENCE}')"))
    return int(result.scalar_one())


def _section_column(sold_out_goes_on_order: bool) -> ColumnElement[str]:
    """La sección derivada: encargue, o stock agotado si los encargues están activos."""
    goes_on_order: ColumnElement[bool] = Product.sale_mode == SaleMode.ON_ORDER
    if sold_out_goes_on_order:
        goes_on_order = or_(goes_on_order, catalog_products.c.sold_out)
    return case((goes_on_order, Section.ON_ORDER.value), else_=Section.STOCK.value)


async def published_products(
    session: AsyncSession, *, section: Section | None, sold_out_goes_on_order: bool
) -> Sequence[tuple[Product, Section, bool]]:
    """Productos publicados con su sección y si están agotados, en el orden manual."""
    section_column = _section_column(sold_out_goes_on_order).label("section")
    stmt = (
        select(Product, section_column, catalog_products.c.sold_out)
        .join(catalog_products, catalog_products.c.id == Product.id)
        .where(Product.status == ProductStatus.PUBLISHED)
        .options(selectinload(Product.images))
        .order_by(Product.sort_order, Product.id)
    )
    if section is not None:
        stmt = stmt.where(section_column == section.value)
    result = await session.execute(stmt)
    return [
        (product, Section(section_value), bool(sold_out))
        for product, section_value, sold_out in result.all()
    ]


async def all_sizes(session: AsyncSession) -> Sequence[Size]:
    return (await session.scalars(select(Size))).all()


async def find_by_slug[T: (Category, Collection, Tag, Version)](
    session: AsyncSession, model: type[T], slug: str
) -> T | None:
    return await session.scalar(select(model).where(model.slug == slug))


async def products_with_slug(session: AsyncSession, slug: str) -> Sequence[Product]:
    """Todos los productos con ese slug (no es único: puede haber más de uno)."""
    stmt = (
        select(Product)
        .where(Product.slug == slug)
        .options(selectinload(Product.sizes), selectinload(Product.tags))
    )
    return (await session.scalars(stmt)).all()


async def has_images(session: AsyncSession, product_id: int) -> bool:
    stmt = select(exists().where(ProductImage.product_id == product_id))
    return bool(await session.scalar(stmt))


def add(session: AsyncSession, instance: Base) -> None:
    session.add(instance)


async def flush(session: AsyncSession) -> None:
    await session.flush()
