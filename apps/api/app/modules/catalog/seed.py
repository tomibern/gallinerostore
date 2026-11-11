"""Carga de datos iniciales del catálogo desde un TOML del cliente.

El núcleo no trae datos: cada cliente tiene su ``config/seed.toml``. La carga
es idempotente: se puede correr varias veces sin duplicar nada (busca por slug
o por grupo y etiqueta, y actualiza lo que ya existe). Las reglas de negocio
salen del service y el acceso a datos, del repository.
"""

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import StoreConfig
from app.modules.catalog import repository, service
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
    # En el seed el slug identifica al producto (todavía no tiene código).
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


@dataclass
class SeedLookups:
    """Lo ya cargado, por clave del seed, para resolver las referencias de los productos."""

    sizes: dict[tuple[str, str], Size] = field(default_factory=dict)
    categories: dict[str, Category] = field(default_factory=dict)
    collections: dict[str, Collection] = field(default_factory=dict)
    versions: dict[str, Version] = field(default_factory=dict)


def load_seed(path: Path) -> CatalogSeed:
    with path.open("rb") as f:
        return CatalogSeed.model_validate(tomllib.load(f))


async def apply_seed(session: AsyncSession, seed: CatalogSeed, store: StoreConfig) -> None:
    """Carga el seed en la sesión (flush, sin commit: decide quien llama)."""
    _check_categories(seed.categories)
    _check_single_default_collection(seed.collections)

    lookups = SeedLookups(sizes=await _upsert_sizes(session, seed.sizes))
    for position, category in enumerate(seed.categories):
        lookups.categories |= await _upsert_category(session, category, None, None, position)
    for position, collection in enumerate(seed.collections):
        lookups.collections[collection.slug] = await _upsert_by_slug(
            session,
            Collection,
            collection.slug,
            name=collection.name,
            is_default=collection.default,
            sort_order=position,
        )
    for position, version in enumerate(seed.versions):
        lookups.versions[version.slug] = await _upsert_by_slug(
            session, Version, version.slug, name=version.name, sort_order=position
        )
    await repository.flush(session)

    for position, product in enumerate(seed.products):
        await _upsert_product(session, product, position, store, lookups)
    await repository.flush(session)


def _check_categories(categories: list[CategorySeed], depth: int = 1) -> None:
    for category in categories:
        try:
            service.check_category_depth(category.slug, depth)
        except service.CategoryTooDeepError as error:
            raise SeedError(str(error)) from error
        _check_categories(category.children, depth + 1)


def _check_single_default_collection(collections: list[CollectionSeed]) -> None:
    defaults = [c.slug for c in collections if c.default]
    if len(defaults) > 1:
        raise SeedError(
            f"Solo una colección puede ser la por defecto; hay {len(defaults)}: {defaults}."
        )


async def _upsert_sizes(
    session: AsyncSession, groups: list[SizeGroupSeed]
) -> dict[tuple[str, str], Size]:
    sizes = {(s.size_group, s.label): s for s in await repository.all_sizes(session)}
    for group in groups:
        for position, label in enumerate(group.labels):
            size = sizes.get((group.group, label))
            if size is None:
                size = Size(label=label, size_group=group.group)
                repository.add(session, size)
                sizes[(group.group, label)] = size
            size.sort_order = position
    return sizes


async def _upsert_category(
    session: AsyncSession,
    seed: CategorySeed,
    parent: Category | None,
    inherited_group: str | None,
    position: int,
) -> dict[str, Category]:
    """Crea o actualiza la categoría y sus hijas. Devuelve todas por slug."""
    size_group = seed.size_group or inherited_group
    if size_group is None:
        raise SeedError(f"La categoría «{seed.slug}» no tiene grupo de talles.")
    category = await _upsert_by_slug(
        session,
        Category,
        seed.slug,
        name=seed.name,
        size_group=size_group,
        sort_order=position,
        parent_id=parent.id if parent else None,
    )
    await repository.flush(session)

    loaded = {seed.slug: category}
    for child_position, child in enumerate(seed.children):
        loaded |= await _upsert_category(session, child, category, size_group, child_position)
    return loaded


async def _upsert_by_slug[T: (Category, Collection, Version)](
    session: AsyncSession, model: type[T], slug: str, **fields: object
) -> T:
    instance = await repository.find_by_slug(session, model, slug)
    if instance is None:
        instance = model(slug=slug)
        repository.add(session, instance)
    for name, value in fields.items():
        setattr(instance, name, value)
    return instance


async def _upsert_product(
    session: AsyncSession,
    seed: ProductSeed,
    position: int,
    store: StoreConfig,
    lookups: SeedLookups,
) -> None:
    category = _resolve(lookups.categories, seed.category, kind="categoría", product_slug=seed.slug)
    collection = _resolve(
        lookups.collections, seed.collection, kind="colección", product_slug=seed.slug
    )
    version = (
        _resolve(lookups.versions, seed.version, kind="versión", product_slug=seed.slug)
        if seed.version
        else None
    )

    product = await _existing_product(session, seed.slug)
    if product is None:
        product = Product(code=await service.new_product_code(session, store.store.code_prefix))
        repository.add(session, product)

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
    product.sizes = [
        ProductSize(
            size_id=_resolve_size(lookups, category, label, seed.slug).id, in_stock=in_stock
        )
        for label, in_stock in seed.sizes.items()
    ]
    await repository.flush(session)


async def _existing_product(session: AsyncSession, slug: str) -> Product | None:
    """El producto del seed con ese slug. Si hay más de uno, no adivina cuál pisar."""
    matches = await repository.products_with_slug(session, slug)
    if len(matches) > 1:
        codes = ", ".join(p.code for p in matches)
        raise SeedError(
            f"Hay {len(matches)} productos con el slug «{slug}» ({codes}): "
            f"el seed no puede saber cuál actualizar. Cambiá el slug en el seed."
        )
    return matches[0] if matches else None


def _resolve_size(lookups: SeedLookups, category: Category, label: str, product_slug: str) -> Size:
    size = lookups.sizes.get((category.size_group, label))
    if size is None:
        raise SeedError(
            f"El producto «{product_slug}» usa el talle «{label}», que no existe en el "
            f"grupo «{category.size_group}» de su categoría."
        )
    return size


def _resolve[T](items: dict[str, T], slug: str, *, kind: str, product_slug: str) -> T:
    if slug not in items:
        raise SeedError(
            f"El producto «{product_slug}» usa la {kind} «{slug}», que no está en el seed."
        )
    return items[slug]
