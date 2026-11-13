"""Reglas de negocio del catálogo (sección, disponibilidad, encargues, categorías y código)."""

from collections.abc import Collection, Mapping, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import StoreConfig
from app.modules.catalog import repository
from app.modules.catalog.models import Availability, Category, ProductImage, SaleMode, Section
from app.modules.catalog.repository import Filter, ListingQuery
from app.modules.catalog.schemas import (
    CategoryFacetValue,
    FacetValue,
    ImageOut,
    ProductFacets,
    ProductFilters,
    ProductList,
    ProductListItem,
)

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


def _listing_query(store: StoreConfig, filters: ProductFilters) -> ListingQuery:
    """Los filtros que aplican: versión y colección solo con su función activa, y talle
    solo en En stock (un encargue se pide en cualquier talle). Los demás se ignoran."""
    applied: dict[Filter, list[str]] = {
        Filter.CATEGORY: filters.category,
        Filter.TAG: filters.tag,
    }
    if store.features.versions:
        applied[Filter.VERSION] = filters.version
    if store.features.collections:
        applied[Filter.COLLECTION] = filters.collection
    if filters.section is Section.STOCK:
        applied[Filter.SIZE] = filters.size
    return ListingQuery(
        section=filters.section,
        sold_out_goes_on_order=store.features.on_order,
        filters=applied,
    )


def category_facet(
    categories: Sequence[Category], counts: Mapping[int, int], selected: Collection[str]
) -> list[CategoryFacetValue]:
    """Categorías con resultados (o elegidas) en orden de árbol. Una de nivel 1 suma sus hijas."""
    children: dict[int, list[Category]] = {}
    for category in categories:
        if category.parent_id is not None:
            children.setdefault(category.parent_id, []).append(category)

    facet: list[CategoryFacetValue] = []
    for root in (c for c in categories if c.parent_id is None):
        kids = children.get(root.id, [])
        total = counts.get(root.id, 0) + sum(counts.get(kid.id, 0) for kid in kids)
        if total or root.slug in selected:
            facet.append(
                CategoryFacetValue(value=root.slug, name=root.name, count=total, parent=None)
            )
        facet.extend(
            CategoryFacetValue(
                value=kid.slug, name=kid.name, count=counts.get(kid.id, 0), parent=root.slug
            )
            for kid in kids
            if counts.get(kid.id) or kid.slug in selected
        )
    return facet


async def _facet(session: AsyncSession, query: ListingQuery, facet: Filter) -> list[FacetValue]:
    """Valores con resultados, más los elegidos que se quedaron sin resultados (con 0):
    así siempre está el chip para sacarlos. Un filtro que no aplica no tiene faceta."""
    if facet not in query.filters:
        return []
    values = [
        FacetValue(value=value, name=name, count=count)
        for value, name, count in await repository.facet_values(session, query, facet)
    ]
    shown = {v.value for v in values}
    missing = [v for v in query.filters[facet] if v not in shown]
    if missing:
        values += [
            FacetValue(value=value, name=name, count=0)
            for value, name in await repository.existing_values(session, facet, missing)
        ]
    return values


async def _facets(session: AsyncSession, query: ListingQuery) -> ProductFacets:
    """Lo necesario para dibujar los filtros: solo valores con resultados en la sección."""
    # Con una sola colección cargada, el filtro no tiene sentido.
    collections_shown = await repository.count_collections(session) > 1
    return ProductFacets(
        categories=category_facet(
            await repository.all_categories(session),
            await repository.count_by_category(session, query),
            query.filters.get(Filter.CATEGORY, []),
        ),
        versions=await _facet(session, query, Filter.VERSION),
        collections=await _facet(session, query, Filter.COLLECTION) if collections_shown else [],
        tags=await _facet(session, query, Filter.TAG),
        sizes=await _facet(session, query, Filter.SIZE),
    )


async def list_published(
    session: AsyncSession, store: StoreConfig, media_base_url: str, filters: ProductFilters
) -> ProductList:
    """Productos publicados que cumplen los filtros, en el orden pedido, con las facetas."""
    query = _listing_query(store, filters)
    rows = await repository.published_products(session, query, filters.sort)
    items = [
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
    return ProductList(items=items, facets=await _facets(session, query))
