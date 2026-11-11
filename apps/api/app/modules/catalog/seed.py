"""Carga de datos iniciales del catálogo desde un TOML del cliente.

El núcleo no trae datos: cada cliente tiene su ``config/seed.toml``. La carga
es idempotente: se puede correr varias veces sin duplicar nada (busca por slug
o por grupo y etiqueta, y actualiza lo que ya existe).
"""

import tomllib
from pathlib import Path

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import StoreConfig
from app.modules.catalog import service
from app.modules.catalog.models import (
    Category,
    Collection,
    Product,
    ProductSize,
    ProductStatus,
    SaleMode,
    Size,
    Version,
)

MAX_CATEGORY_DEPTH = 2


class SeedError(ValueError):
    """El archivo de seed tiene datos inválidos."""


class SizeGroupSeed(BaseModel):
    group: str
    labels: list[str]


class CategorySeed(BaseModel):
    name: str
    slug: str
    size_group: str | None = None
    children: list["CategorySeed"] = []


class CollectionSeed(BaseModel):
    name: str
    slug: str
    default: bool = False


class VersionSeed(BaseModel):
    name: str
    slug: str


class ProductSeed(BaseModel):
    slug: str
    name: str
    category: str
    collection: str
    version: str | None = None
    description: str | None = None
    season: str | None = None
    sale_mode: SaleMode
    status: ProductStatus = ProductStatus.DRAFT
    # En la unidad menor de la moneda (ADR 0002).
    price: int
    featured: bool = False
    # Talle → disponible (en stock) o se puede pedir (en encargue).
    sizes: dict[str, bool] = {}


class CatalogSeed(BaseModel):
    sizes: list[SizeGroupSeed] = []
    categories: list[CategorySeed] = []
    collections: list[CollectionSeed] = []
    versions: list[VersionSeed] = []
    products: list[ProductSeed] = []


def load_seed(path: Path) -> CatalogSeed:
    with path.open("rb") as f:
        return CatalogSeed.model_validate(tomllib.load(f))


async def apply_seed(session: AsyncSession, seed: CatalogSeed, store: StoreConfig) -> None:
    """Carga el seed en la sesión (flush, sin commit: decide quien llama)."""
    _check_category_depth(seed.categories)

    sizes = await _upsert_sizes(session, seed.sizes)
    categories: dict[str, Category] = {}
    for position, category in enumerate(seed.categories):
        await _upsert_category(session, category, None, None, position, categories)
    collections = {
        c.slug: await _upsert_by_slug(
            session, Collection, c.slug, name=c.name, is_default=c.default, sort_order=i
        )
        for i, c in enumerate(seed.collections)
    }
    versions = {
        v.slug: await _upsert_by_slug(session, Version, v.slug, name=v.name, sort_order=i)
        for i, v in enumerate(seed.versions)
    }
    await session.flush()

    for position, product in enumerate(seed.products):
        await _upsert_product(
            session, product, position, store, sizes, categories, collections, versions
        )
    await session.flush()


def _check_category_depth(categories: list[CategorySeed], depth: int = 1) -> None:
    for category in categories:
        if category.children and depth >= MAX_CATEGORY_DEPTH:
            raise SeedError(
                f"La categoría «{category.slug}» tiene subcategorías: "
                f"las categorías admiten como máximo dos niveles."
            )
        _check_category_depth(category.children, depth + 1)


async def _upsert_sizes(
    session: AsyncSession, groups: list[SizeGroupSeed]
) -> dict[tuple[str, str], Size]:
    existing = {(s.size_group, s.label): s for s in (await session.scalars(select(Size))).all()}
    for group in groups:
        for position, label in enumerate(group.labels):
            size = existing.get((group.group, label))
            if size is None:
                size = Size(label=label, size_group=group.group)
                session.add(size)
                existing[(group.group, label)] = size
            size.sort_order = position
    return existing


async def _upsert_category(
    session: AsyncSession,
    seed: CategorySeed,
    parent: Category | None,
    inherited_group: str | None,
    position: int,
    out: dict[str, Category],
) -> None:
    size_group = seed.size_group or inherited_group
    if size_group is None:
        raise SeedError(f"La categoría «{seed.slug}» no tiene grupo de talles.")
    category = await _upsert_by_slug(
        session, Category, seed.slug, name=seed.name, size_group=size_group, sort_order=position
    )
    category.parent_id = parent.id if parent else None
    await session.flush()
    out[seed.slug] = category
    for child_position, child in enumerate(seed.children):
        await _upsert_category(session, child, category, size_group, child_position, out)


async def _upsert_by_slug[T: (Category, Collection, Version)](
    session: AsyncSession, model: type[T], slug: str, **fields: object
) -> T:
    instance = await session.scalar(select(model).where(model.slug == slug))
    if instance is None:
        instance = model(slug=slug)
        session.add(instance)
    for name, value in fields.items():
        setattr(instance, name, value)
    return instance


async def _upsert_product(
    session: AsyncSession,
    seed: ProductSeed,
    position: int,
    store: StoreConfig,
    sizes: dict[tuple[str, str], Size],
    categories: dict[str, Category],
    collections: dict[str, Collection],
    versions: dict[str, Version],
) -> None:
    category = _lookup(categories, seed.category, "categoría", seed.slug)
    collection = _lookup(collections, seed.collection, "colección", seed.slug)
    version = _lookup(versions, seed.version, "versión", seed.slug) if seed.version else None

    product = await session.scalar(select(Product).where(Product.slug == seed.slug).limit(1))
    if product is None:
        product = Product(code=await service.new_product_code(session, store.store.code_prefix))
        session.add(product)

    product.slug = seed.slug
    product.name = seed.name
    product.description = seed.description
    product.season = seed.season
    product.category_id = category.id
    product.collection_id = collection.id
    product.version_id = version.id if version else None
    product.sale_mode = seed.sale_mode
    product.status = seed.status
    product.price = seed.price
    product.featured = seed.featured
    product.sort_order = position
    await session.flush()

    await session.refresh(product, ["sizes"])
    product.sizes.clear()
    await session.flush()
    for label, in_stock in seed.sizes.items():
        size = sizes.get((category.size_group, label))
        if size is None:
            raise SeedError(
                f"El producto «{seed.slug}» usa el talle «{label}», que no existe en el "
                f"grupo «{category.size_group}» de su categoría."
            )
        product.sizes.append(ProductSize(size_id=size.id, in_stock=in_stock))


def _lookup[T](items: dict[str, T], slug: str, what: str, product: str) -> T:
    if slug not in items:
        raise SeedError(f"El producto «{product}» usa la {what} «{slug}», que no está en el seed.")
    return items[slug]
