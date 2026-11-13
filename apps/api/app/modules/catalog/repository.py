"""Acceso a datos del catálogo con SQLAlchemy."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from sqlalchemy import ColumnElement, Select, case, exists, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.models import Base
from app.modules.catalog.models import (
    PRODUCT_CODE_SEQUENCE,
    Category,
    Collection,
    Product,
    ProductImage,
    ProductSize,
    ProductSort,
    ProductStatus,
    ProductTag,
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


class Filter(StrEnum):
    """Filtros del listado, por el nombre que tienen en la query string."""

    CATEGORY = "category"
    VERSION = "version"
    COLLECTION = "collection"
    TAG = "tag"
    SIZE = "size"


@dataclass(frozen=True)
class ListingQuery:
    """Qué productos publicados se listan. Los filtros ya vienen limpios (el service
    saca los que no aplican); un filtro sin valores no filtra."""

    section: Section | None
    sold_out_goes_on_order: bool
    filters: Mapping[Filter, Sequence[str]] = field(default_factory=dict)


def _facet_model(facet: Filter) -> type[Version | Collection | Tag]:
    models: dict[Filter, type[Version | Collection | Tag]] = {
        Filter.VERSION: Version,
        Filter.COLLECTION: Collection,
        Filter.TAG: Tag,
    }
    return models[facet]


def _ids_by_slug(model: type[Version | Collection | Tag], slugs: Sequence[str]) -> Select[Any]:
    return select(model.id).where(model.slug.in_(slugs))


def _filter_condition(name: Filter, values: Sequence[str]) -> ColumnElement[bool]:
    """Condición de un filtro: sus valores se suman (O)."""
    match name:
        case Filter.CATEGORY:
            # Una categoría de nivel 1 incluye a sus hijas (hay dos niveles como máximo).
            chosen = select(Category.id).where(Category.slug.in_(values))
            return Product.category_id.in_(
                select(Category.id).where(
                    or_(Category.id.in_(chosen), Category.parent_id.in_(chosen))
                )
            )
        case Filter.VERSION:
            return Product.version_id.in_(_ids_by_slug(Version, values))
        case Filter.COLLECTION:
            return Product.collection_id.in_(_ids_by_slug(Collection, values))
        case Filter.TAG:
            return exists().where(
                ProductTag.product_id == Product.id,
                ProductTag.tag_id.in_(_ids_by_slug(Tag, values)),
            )
        case Filter.SIZE:
            # Por etiqueta: «M» matchea en todos los grupos de talles. Solo talles disponibles.
            return exists().where(
                ProductSize.product_id == Product.id,
                ProductSize.in_stock,
                ProductSize.size_id.in_(select(Size.id).where(Size.label.in_(values))),
            )


def _conditions(query: ListingQuery, *, skip: Filter | None = None) -> list[ColumnElement[bool]]:
    """Publicado, de la sección y con cada filtro (se cruzan: Y). ``skip`` deja uno
    afuera: cada faceta se cuenta sin su propio filtro, para poder sumar valores."""
    conditions: list[ColumnElement[bool]] = [Product.status == ProductStatus.PUBLISHED]
    if query.section is not None:
        section = _section_column(query.sold_out_goes_on_order)
        conditions.append(section == query.section.value)
    conditions.extend(
        _filter_condition(name, values)
        for name, values in query.filters.items()
        if values and name is not skip
    )
    return conditions


def _order_by(sort: ProductSort) -> list[ColumnElement[Any]]:
    """Siempre termina en el id: un orden total, así la paginación no repite ni saltea."""
    match sort:
        case ProductSort.MANUAL:
            return [Product.sort_order.asc(), Product.created_at.desc(), Product.id.desc()]
        case ProductSort.NEWEST:
            return [Product.created_at.desc(), Product.id.desc()]
        case ProductSort.PRICE_ASC:
            return [Product.price.asc(), Product.id.asc()]
        case ProductSort.PRICE_DESC:
            return [Product.price.desc(), Product.id.desc()]


async def published_products(
    session: AsyncSession, query: ListingQuery, sort: ProductSort
) -> Sequence[tuple[Product, Section, bool]]:
    """Productos publicados que cumplen la consulta, con su sección y si están agotados."""
    section_column = _section_column(query.sold_out_goes_on_order).label("section")
    stmt = (
        select(Product, section_column, catalog_products.c.sold_out)
        .join(catalog_products, catalog_products.c.id == Product.id)
        .where(*_conditions(query))
        .options(selectinload(Product.images))
        .order_by(*_order_by(sort))
    )
    result = await session.execute(stmt)
    return [
        (product, Section(section_value), bool(sold_out))
        for product, section_value, sold_out in result.all()
    ]


def _count_stmt(query: ListingQuery, skip: Filter) -> Select[Any]:
    """Base de una faceta: cuenta productos distintos con los demás filtros."""
    return (
        select()
        .select_from(Product)
        .join(catalog_products, catalog_products.c.id == Product.id)
        .where(*_conditions(query, skip=skip))
    )


async def count_by_category(session: AsyncSession, query: ListingQuery) -> dict[int, int]:
    """Productos por categoría asignada (sin sumar las hijas), sin el filtro de categoría."""
    stmt = (
        _count_stmt(query, Filter.CATEGORY)
        .add_columns(Product.category_id, func.count(Product.id.distinct()))
        .group_by(Product.category_id)
    )
    return {category_id: count for category_id, count in (await session.execute(stmt)).all()}


async def all_categories(session: AsyncSession) -> Sequence[Category]:
    return (await session.scalars(select(Category).order_by(Category.sort_order))).all()


async def count_collections(session: AsyncSession) -> int:
    return int(await session.scalar(select(func.count()).select_from(Collection)) or 0)


async def existing_values(
    session: AsyncSession, facet: Filter, values: Sequence[str]
) -> list[tuple[str, str]]:
    """(valor, nombre) de los valores pedidos que existen; los desconocidos no vuelven."""
    if facet is Filter.SIZE:
        stmt = select(Size.label, Size.label).where(Size.label.in_(values)).distinct()
    else:
        model = _facet_model(facet)
        stmt = (
            select(model.slug, model.name)
            .where(model.slug.in_(values))
            .order_by(model.sort_order, model.id)
        )
    return [(value, name) for value, name in (await session.execute(stmt)).all()]


async def facet_values(
    session: AsyncSession, query: ListingQuery, facet: Filter
) -> list[tuple[str, str, int]]:
    """(valor, nombre, productos) de una faceta con resultados, sin su propio filtro."""
    count = func.count(Product.id.distinct())
    stmt = _count_stmt(query, facet)
    match facet:
        case Filter.VERSION | Filter.COLLECTION:
            model = Version if facet is Filter.VERSION else Collection
            key = Product.version_id if facet is Filter.VERSION else Product.collection_id
            stmt = (
                stmt.join(model, model.id == key)
                .add_columns(model.slug, model.name, count)
                .group_by(model.id)
                .order_by(model.sort_order, model.id)
            )
        case Filter.TAG:
            stmt = (
                stmt.join(ProductTag, ProductTag.product_id == Product.id)
                .join(Tag, Tag.id == ProductTag.tag_id)
                .add_columns(Tag.slug, Tag.name, count)
                .group_by(Tag.id)
                .order_by(Tag.sort_order, Tag.id)
            )
        case Filter.SIZE:
            # Por etiqueta, sumando grupos; en el orden de carga de los talles.
            stmt = (
                stmt.join(ProductSize, ProductSize.product_id == Product.id)
                .join(Size, Size.id == ProductSize.size_id)
                .where(ProductSize.in_stock)
                .add_columns(Size.label, Size.label, count)
                .group_by(Size.label)
                .order_by(func.min(Size.id))
            )
        case Filter.CATEGORY:
            raise ValueError("La faceta de categoría se arma con count_by_category.")
    return [(value, name, n) for value, name, n in (await session.execute(stmt)).all()]


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
