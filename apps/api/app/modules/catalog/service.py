"""Reglas de negocio del catálogo (sección, disponibilidad, encargues, categorías y código)."""

import re
import unicodedata
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import StoreConfig
from app.modules.catalog import models, repository
from app.modules.catalog.models import (
    Availability,
    Category,
    Product,
    ProductImage,
    ProductSize,
    ProductStatus,
    ProductStoryItem,
    SaleMode,
    Section,
    Size,
    SizeStatus,
    StoryItemKind,
    Tag,
    Version,
)
from app.modules.catalog.repository import AdminListingQuery, Filter, ListingQuery
from app.modules.catalog.schemas import (
    AdminProduct,
    AdminProductCreate,
    AdminProductList,
    AdminProductListItem,
    AdminProductPatch,
    AdminProductQuery,
    AdminSizeAvailability,
    AdminSizeOut,
    CatalogFeatures,
    CatalogOptions,
    CategoryFacetValue,
    CategoryOption,
    FacetValue,
    ImageOut,
    NamedRef,
    ProductDetail,
    ProductFacets,
    ProductFilters,
    ProductList,
    ProductListItem,
    ProductSizeOut,
    StoryItemOut,
)
from app.modules.metrics import service as metrics
from app.modules.settings import service as settings_service
from app.modules.settings.models import MessageCase
from app.modules.settings.schemas import MessagePreview, PreviewProduct

MAX_CATEGORY_DEPTH = 2

# Ruta del detalle en la web, para el link del mensaje prearmado. El e2e verifica que
# lleve al mismo producto.
PRODUCT_PATH = "/p/{code}"


class CategoryTooDeepError(ValueError):
    """Las categorías admiten como máximo dos niveles."""


def check_category_depth(slug: str, depth: int) -> None:
    """Valida el nivel de una categoría (1 = raíz). El admin la va a reusar al crear categorías."""
    if depth > MAX_CATEGORY_DEPTH:
        raise CategoryTooDeepError(
            f"La categoría «{slug}» quedaría en el nivel {depth}: "
            f"las categorías admiten como máximo dos niveles."
        )


class IncompleteMilestoneError(ValueError):
    """Un hito de la historia necesita año y anécdota: se muestra con año y título y,
    al darse vuelta, cuenta la anécdota."""


def check_story_item(slug: str, kind: StoryItemKind, year: int | None, body: str | None) -> None:
    """Valida un ítem de la historia. El admin la va a reusar al cargar la historia."""
    if kind is StoryItemKind.MILESTONE and (year is None or not body):
        raise IncompleteMilestoneError(
            f"Un hito de «{slug}» no tiene año o anécdota: un hito muestra el año y el "
            f"título, y al darse vuelta cuenta la anécdota."
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
    solo en En stock (un encargue se pide en cualquier talle). Los demás se ignoran.
    La búsqueda se cruza con todo."""
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
        featured=filters.featured,
        filters=applied,
        search=_search_words(filters.q),
    )


def _search_words(q: str | None) -> tuple[str, ...]:
    """Las palabras de la búsqueda; sin texto (o solo espacios), ninguna."""
    return tuple(q.split()) if q else ()


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
    """Una página de los productos publicados que cumplen los filtros, en el orden
    pedido, con el total y las facetas."""
    query = _listing_query(store, filters)
    rows, has_more = await repository.published_products(
        session, query, filters.sort, limit=filters.limit, offset=filters.offset
    )
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
    return ProductList(
        items=items,
        has_more=has_more,
        total=await repository.count_published(session, query),
        facets=await _facets(session, query),
    )


def _named(item: Category | models.Collection | Version | Tag) -> NamedRef:
    return NamedRef(slug=item.slug, name=item.name)


def product_url(site_url: str, code: str) -> str:
    """El link público del detalle de un producto (el código va en minúsculas)."""
    return site_url.rstrip("/") + PRODUCT_PATH.format(code=code.lower())


def _message_values(product: Product, size: Size, link: str) -> dict[str, str]:
    """Las variables de las plantillas (MessageVariable) para un talle de un producto."""
    return {"product": product.name, "code": product.code, "size": size.label, "link": link}


def message_case(product_availability: Availability, status: SizeStatus) -> MessageCase:
    """Qué plantilla usa la consulta por un talle. Un agotado con los encargues apagados
    tiene sus talles sin stock: pregunta por disponibilidad."""
    if status is SizeStatus.ON_ORDER:
        if product_availability is Availability.SOLD_OUT_ON_ORDER:
            return MessageCase.SOLD_OUT_ON_ORDER
        return MessageCase.ON_ORDER
    if status is SizeStatus.OUT_OF_STOCK:
        return MessageCase.OUT_OF_STOCK
    return MessageCase.STOCK


async def _offered_sizes(
    session: AsyncSession, product: Product, section: Section
) -> list[tuple[Size, SizeStatus]]:
    """En Por encargue, todos los talles del grupo de la categoría (aunque un agotado
    tenga los suyos); en stock, los propios con su estado. Siempre en el orden del grupo."""
    if section is Section.ON_ORDER:
        group = await repository.sizes_in_group(session, product.category.size_group)
        return [(size, SizeStatus.ON_ORDER) for size in group]
    return _own_sizes(product)


def _own_sizes(product: Product) -> list[tuple[Size, SizeStatus]]:
    """Los talles propios de un producto de stock, en el orden del grupo, con su estado."""
    own = sorted(product.sizes, key=lambda ps: (ps.size.sort_order, ps.size.id))
    return [
        (ps.size, SizeStatus.IN_STOCK if ps.in_stock else SizeStatus.OUT_OF_STOCK) for ps in own
    ]


@dataclass(frozen=True)
class OfferedProduct:
    """Un producto del catálogo público y los talles que ofrece (etiqueta → id)."""

    id: int
    size_ids: dict[str, int]


async def offered_product(
    session: AsyncSession, store: StoreConfig, code: str
) -> OfferedProduct | None:
    """El producto publicado con ese código y los mismos talles que muestra su detalle,
    o None si no está en el catálogo público."""
    row = await repository.published_product_by_code(session, code, store.features.on_order)
    if row is None:
        return None
    product, section, _ = row
    sizes = await _offered_sizes(session, product, section)
    return OfferedProduct(id=product.id, size_ids={size.label: size.id for size, _ in sizes})


# Cuántos productos publicados se miran para encontrar uno de cada caso en la vista
# previa. Si ninguno es del caso, se usa el primero.
_PREVIEW_CANDIDATES = 50


async def _preview_sample(
    session: AsyncSession, store: StoreConfig, case: MessageCase
) -> tuple[Product, Size] | None:
    """Un producto publicado real y un talle cuya consulta usa la plantilla de ese caso;
    si no hay ninguno así, el primer talle del primer producto."""
    rows = await repository.published_products_with_sizes(
        session, store.features.on_order, limit=_PREVIEW_CANDIDATES
    )
    fallback: tuple[Product, Size] | None = None
    for product, section, sold_out in rows:
        product_availability = availability(section, sold_out)
        for size, status in await _offered_sizes(session, product, section):
            if message_case(product_availability, status) is case:
                return product, size
            fallback = fallback or (product, size)
    return fallback


async def message_preview(
    session: AsyncSession, store: StoreConfig, site_url: str, case: MessageCase, template: str
) -> MessagePreview:
    """El mensaje que armaría la API con esa plantilla para un producto publicado real
    (ADR 0005: la web nunca arma mensajes). La consulta general no lleva producto."""
    sample = None if case is MessageCase.GENERAL else await _preview_sample(session, store, case)
    if sample is None:
        return MessagePreview(message=settings_service.render_message(template, {}), product=None)
    product, size = sample
    values = _message_values(product, size, product_url(site_url, product.code))
    return MessagePreview(
        message=settings_service.render_message(template, values),
        product=PreviewProduct(code=product.code, name=product.name, size=size.label),
    )


# Orden de los tipos en la sección: el de declaración del enum.
_STORY_KIND_ORDER = {kind: position for position, kind in enumerate(StoryItemKind)}


def _story_out(items: Sequence[ProductStoryItem]) -> list[StoryItemOut]:
    """La historia agrupada por tipo; dentro del tipo, en el orden en que llega."""
    ordered = sorted(items, key=lambda item: _STORY_KIND_ORDER[item.kind])
    return [
        StoryItemOut(kind=item.kind, year=item.year, title=item.title, body=item.body)
        for item in ordered
    ]


async def published_product(
    session: AsyncSession, store: StoreConfig, media_base_url: str, site_url: str, code: str
) -> ProductDetail | None:
    """El detalle de un producto publicado por su código, o None si no existe o no está
    publicado (borrador, oculto y archivado no se ven). Cada talle trae sus consultas
    con el mensaje prearmado y el link ya armados (ADR 0005)."""
    row = await repository.published_product_by_code(session, code, store.features.on_order)
    if row is None:
        return None
    product, section, sold_out = row
    features = store.features
    product_availability = availability(section, sold_out)
    contact = await settings_service.contact(session, features)
    link = product_url(site_url, product.code)
    sizes = [
        ProductSizeOut(
            label=size.label,
            status=status,
            inquiries=contact.inquiries(
                message_case(product_availability, status),
                _message_values(product, size, link),
            ),
        )
        for size, status in await _offered_sizes(session, product, section)
    ]
    return ProductDetail(
        code=product.code,
        name=product.name,
        slug=product.slug,
        price=product.price,
        currency=store.store.currency,
        section=section,
        availability=product_availability,
        description=product.description,
        season=product.season,
        category=_named(product.category),
        version=_named(product.version) if features.versions and product.version else None,
        collection=_named(product.collection) if features.collections else None,
        images=[_image_out(image, media_base_url) for image in product.images],
        sizes=sizes,
        on_order_notice=contact.on_order_notice if section is Section.ON_ORDER else None,
        story=_story_out(product.story_items) if features.product_story else [],
    )


# --- Admin ----------------------------------------------------------------------


async def _admin_sizes(
    session: AsyncSession, product: Product, groups: dict[str, Sequence[Size]]
) -> list[AdminSizeOut]:
    """Los talles que ve el admin. Se decide por el modo de venta, no por la sección: un
    producto de stock agotado muestra los suyos tachados, aunque esté en Por encargue.
    ``groups`` guarda los grupos ya leídos, para no repetir la consulta en la página."""
    if product.sale_mode is SaleMode.ON_ORDER:
        group = product.category.size_group
        if group not in groups:
            groups[group] = await repository.sizes_in_group(session, group)
        return [
            AdminSizeOut(label=size.label, status=SizeStatus.ON_ORDER) for size in groups[group]
        ]
    return [AdminSizeOut(label=size.label, status=status) for size, status in _own_sizes(product)]


async def list_for_admin(
    session: AsyncSession,
    store: StoreConfig,
    media_base_url: str,
    query: AdminProductQuery,
    now: datetime,
) -> AdminProductList:
    """Una página del listado del admin: cualquier estado, con la sección y la
    disponibilidad calculadas con la misma regla del catálogo público, y las visitas y
    consultas de los últimos 7 días (las calcula metrics)."""
    listing = AdminListingQuery(
        filter=query.filter,
        sold_out_goes_on_order=store.features.on_order,
        search=_search_words(query.q),
    )
    rows, has_more = await repository.admin_products(
        session, listing, limit=query.limit, offset=query.offset
    )
    groups: dict[str, Sequence[Size]] = {}
    activity = await metrics.activity_last_7_days(
        session, store, now, [product.id for product, *_ in rows]
    )
    items = [
        AdminProductListItem(
            code=product.code,
            name=product.name,
            price=product.price,
            currency=store.store.currency,
            status=product.status,
            featured=product.featured,
            section=product_section,
            availability=availability(product_section, sold_out),
            sizes=await _admin_sizes(session, product, groups),
            cover=_image_out(product.images[0], media_base_url) if product.images else None,
            visits_7d=activity[product.id].visits,
            inquiries_7d=activity[product.id].inquiries,
        )
        for product, product_section, sold_out in rows
    ]
    return AdminProductList(
        items=items,
        has_more=has_more,
        total=await repository.count_admin_products(session, listing),
    )


# --- Admin: editor de producto --------------------------------------------------------


@dataclass(frozen=True)
class FieldProblem:
    """Un campo del editor que no vale. ``loc`` es el camino dentro del cuerpo del pedido
    («category», («sizes», 0, «label»)…), igual que en los errores de Pydantic."""

    loc: tuple[str | int, ...]
    type: str
    message: str


class InvalidProductError(ValueError):
    """Uno o más campos del editor no valen contra lo cargado (categoría que no existe,
    talle de otro grupo, encargue con talles…). El router lo devuelve como un 422 por campo."""

    def __init__(self, problems: Sequence[FieldProblem]) -> None:
        super().__init__("; ".join(problem.message for problem in problems))
        self.problems = list(problems)


def slugify(text: str) -> str:
    """El slug de un nombre, para la URL: sin acentos, en minúsculas y con guiones."""
    plain = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", plain.lower()).strip("-") or "producto"


async def _default_collection(session: AsyncSession) -> models.Collection | None:
    """La colección de un producto que no elige ninguna: la marcada por defecto o, si
    hay una sola cargada, esa."""
    default = await repository.default_collection(session)
    if default is not None:
        return default
    collections = await repository.all_ordered(session, models.Collection)
    return collections[0] if len(collections) == 1 else None


def _tree_order(categories: Sequence[Category]) -> list[Category]:
    """Cada categoría de nivel 1 seguida de sus hijas, en su orden."""
    children: dict[int, list[Category]] = {}
    for category in categories:
        if category.parent_id is not None:
            children.setdefault(category.parent_id, []).append(category)
    ordered: list[Category] = []
    for root in (c for c in categories if c.parent_id is None):
        ordered.append(root)
        ordered.extend(children.get(root.id, []))
    return ordered


async def catalog_options(session: AsyncSession, store: StoreConfig) -> CatalogOptions:
    """Lo que el editor ofrece para elegir: categorías con su grupo de talles,
    colecciones, versiones, etiquetas, talles por grupo y las funciones activas."""
    categories = await repository.all_categories(session)
    slugs = {category.id: category.slug for category in categories}
    default = await _default_collection(session)
    groups = await repository.sizes_by_group(session)
    return CatalogOptions(
        categories=[
            CategoryOption(
                slug=category.slug,
                name=category.name,
                parent=slugs.get(category.parent_id) if category.parent_id else None,
                size_group=category.size_group,
            )
            for category in _tree_order(categories)
        ],
        collections=[
            _named(item) for item in await repository.all_ordered(session, models.Collection)
        ],
        default_collection=default.slug if default else None,
        versions=[_named(item) for item in await repository.all_ordered(session, Version)],
        tags=[_named(item) for item in await repository.all_ordered(session, Tag)],
        sizes={group: [size.label for size in sizes] for group, sizes in groups.items()},
        features=CatalogFeatures(
            collections=store.features.collections,
            versions=store.features.versions,
            on_order=store.features.on_order,
        ),
    )


def _admin_product_out(product: Product, store: StoreConfig) -> AdminProduct:
    tags = sorted(product.tags, key=lambda tag: (tag.sort_order, tag.id))
    return AdminProduct(
        code=product.code,
        name=product.name,
        status=product.status,
        category=product.category.slug,
        collection=product.collection.slug,
        version=product.version.slug if product.version else None,
        season=product.season,
        tags=[tag.slug for tag in tags],
        description=product.description,
        price=product.price,
        currency=store.store.currency,
        sale_mode=product.sale_mode,
        sizes=[
            AdminSizeAvailability(label=size.label, in_stock=status is SizeStatus.IN_STOCK)
            for size, status in _own_sizes(product)
        ],
    )


async def admin_product(
    session: AsyncSession, store: StoreConfig, code: str
) -> AdminProduct | None:
    """Un producto en cualquier estado, como lo edita el admin; None si no existe."""
    product = await repository.admin_product_by_code(session, code)
    return _admin_product_out(product, store) if product else None


@dataclass
class _Resolved:
    """Lo que el pedido nombra por slug, ya buscado. Solo lo que vino en el pedido."""

    category: Category | None = None
    collection: models.Collection | None = None
    version: Version | None = None
    tags: list[Tag] | None = None


async def _resolve(
    session: AsyncSession, body: AdminProductPatch, problems: list[FieldProblem]
) -> _Resolved:
    """Busca categoría, colección, versión y etiquetas, y anota las que no existen."""
    fields = body.model_fields_set
    resolved = _Resolved()
    if body.category is not None:
        resolved.category = await repository.find_by_slug(session, Category, body.category)
        if resolved.category is None:
            problems.append(FieldProblem(("category",), "unknown", "La categoría no existe."))
    if body.collection is not None:
        resolved.collection = await repository.find_by_slug(
            session, models.Collection, body.collection
        )
        if resolved.collection is None:
            problems.append(FieldProblem(("collection",), "unknown", "La colección no existe."))
    if "version" in fields and body.version is not None:
        resolved.version = await repository.find_by_slug(session, Version, body.version)
        if resolved.version is None:
            problems.append(FieldProblem(("version",), "unknown", "La versión no existe."))
    if body.tags is not None:
        found = await repository.tags_by_slug(session, body.tags)
        problems.extend(
            FieldProblem(("tags", position), "unknown", f"La etiqueta «{slug}» no existe.")
            for position, slug in enumerate(body.tags)
            if slug not in found
        )
        resolved.tags = [found[slug] for slug in body.tags if slug in found]
    return resolved


def _size_problems(
    body: AdminProductPatch, sale_mode: SaleMode, group: Sequence[Size]
) -> list[FieldProblem]:
    """Un encargue no lleva talles; en stock, cada talle tiene que ser del grupo."""
    if not body.sizes:
        return []
    if sale_mode is SaleMode.ON_ORDER:
        return [
            FieldProblem(
                ("sizes",),
                "on_order_with_sizes",
                "Un encargue no tiene talles: se pide en cualquier talle del grupo.",
            )
        ]
    labels = {size.label for size in group}
    return [
        FieldProblem(
            ("sizes", position, "label"),
            "unknown_size",
            f"El talle «{item.label}» no es del grupo de la categoría.",
        )
        for position, item in enumerate(body.sizes)
        if item.label not in labels
    ]


async def _save(
    session: AsyncSession,
    store: StoreConfig,
    product: Product,
    body: AdminProductPatch,
    *,
    creating: bool,
) -> AdminProduct:
    """Valida el pedido contra lo cargado y, si todo vale, lo aplica y lo guarda.

    Reglas de talles: un encargue no tiene filas propias. Al pasar a stock (o al crear
    uno de stock), y al cambiar de categoría a otro grupo siendo de stock, quedan todos
    los talles del grupo, disponibles. Después se aplica ``sizes``."""
    problems: list[FieldProblem] = []
    resolved = await _resolve(session, body, problems)
    fields = body.model_fields_set

    category = resolved.category or (None if creating else product.category)
    collection = resolved.collection
    if creating and collection is None and body.collection is None:
        collection = await _default_collection(session)
        if collection is None:
            problems.append(FieldProblem(("collection",), "missing", "Elegí una colección."))
    sale_mode = body.sale_mode or (SaleMode.STOCK if creating else product.sale_mode)
    groups = await repository.sizes_by_group(session)
    group = groups.get(category.size_group, []) if category else []
    problems += _size_problems(body, sale_mode, group)
    if problems:
        raise InvalidProductError(problems)
    assert category is not None  # sin categoría habría un problema anotado
    if creating:
        # Recién ahora, para no gastar números de la secuencia en pedidos inválidos.
        product.code = await new_product_code(session, store.store.code_prefix)

    rebuild_sizes = sale_mode is SaleMode.STOCK and (
        creating
        or product.sale_mode is SaleMode.ON_ORDER
        or product.category.size_group != category.size_group
    )
    if body.name is not None:
        product.name = body.name
        product.slug = slugify(body.name)
    product.category = category
    if collection is not None:
        product.collection = collection
    if "version" in fields:
        product.version = resolved.version
    if "season" in fields:
        product.season = body.season
    if "description" in fields:
        product.description = body.description
    if resolved.tags is not None:
        product.tags = resolved.tags
    if body.price is not None:
        product.price = body.price
    product.sale_mode = sale_mode

    if sale_mode is SaleMode.ON_ORDER:
        product.sizes = []
    elif rebuild_sizes:
        product.sizes = [ProductSize(size=size, in_stock=True) for size in group]
    if body.sizes:
        own = {row.size.label: row for row in product.sizes}
        by_label = {size.label: size for size in group}
        for item in body.sizes:
            if item.label in own:
                own[item.label].in_stock = item.in_stock
            else:
                product.sizes.append(ProductSize(size=by_label[item.label], in_stock=item.in_stock))

    if creating:
        repository.add(session, product)
    await repository.commit(session)
    return _admin_product_out(product, store)


async def create_product(
    session: AsyncSession, store: StoreConfig, body: AdminProductCreate
) -> AdminProduct:
    """Un producto nuevo: un borrador con el código ya asignado (no cambia nunca)."""
    product = Product(
        name="",
        slug="",
        price=0,
        status=ProductStatus.DRAFT,
        featured=False,
        sort_order=0,
        version=None,
        tags=[],
        sizes=[],
    )
    return await _save(session, store, product, body, creating=True)


async def update_product(
    session: AsyncSession, store: StoreConfig, code: str, body: AdminProductPatch
) -> AdminProduct | None:
    """Edita los datos, el modo de venta y los talles de un producto; None si no existe.
    El código no se edita."""
    product = await repository.admin_product_by_code(session, code)
    if product is None:
        return None
    return await _save(session, store, product, body, creating=False)
