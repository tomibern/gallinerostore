"""Modelos Pydantic de entrada y salida del catálogo."""

from pydantic import BaseModel, Field

from app.modules.catalog.models import (
    AdminFilter,
    Availability,
    ProductSort,
    ProductStatus,
    Section,
    SizeStatus,
    StoryItemKind,
)
from app.modules.settings.schemas import Inquiry

# Productos por página del listado, y el tope de seguridad de un pedido.
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
# Largo máximo del texto que se busca.
MAX_SEARCH_LENGTH = 100


class ImageOut(BaseModel):
    full: str = Field(description="Ruta de la imagen completa (lado mayor 1600 px), bajo /media.")
    thumb: str = Field(description="Ruta de la miniatura (400 px), bajo /media.")
    alt: str
    width: int
    height: int


class ProductListItem(BaseModel):
    code: str = Field(
        description="Código permanente del producto: prefijo de la tienda y número (ABC-014)."
    )
    name: str
    slug: str
    price: int = Field(description="Precio en la unidad menor de la moneda (centavos).")
    currency: str
    section: Section = Field(
        description="Sección donde aparece: un producto de stock agotado va a Por encargue."
    )
    availability: Availability = Field(description="Disponibilidad de cara al cliente.")
    cover: ImageOut | None = Field(description="La primera imagen del producto, si tiene.")


class ProductFilters(BaseModel):
    """Query string del listado: búsqueda, filtros, orden y página. Varios valores de un filtro
    se suman (O) y filtros distintos se cruzan (Y). Un filtro que no aplica se ignora
    y un valor que no existe deja el listado vacío, así un link compartido nunca da
    error. La página se pide con ``limit`` y ``offset`` sobre un orden estable."""

    section: Section | None = Field(default=None, description="Solo los productos de esa sección.")
    featured: bool = Field(
        default=False,
        description="Solo los destacados (los de la home). Con false no filtra.",
    )
    category: list[str] = Field(
        default=[], description="Slugs de categoría. Una de nivel 1 incluye a sus hijas."
    )
    version: list[str] = Field(
        default=[], description="Slugs de versión. Se ignora con las versiones apagadas."
    )
    collection: list[str] = Field(
        default=[], description="Slugs de colección. Se ignora con las colecciones apagadas."
    )
    tag: list[str] = Field(default=[], description="Slugs de etiqueta.")
    size: list[str] = Field(
        default=[],
        description=(
            "Etiquetas de talle disponible (en cualquier grupo de talles). "
            "Solo filtra en la sección En stock."
        ),
    )
    q: str | None = Field(
        default=None,
        max_length=MAX_SEARCH_LENGTH,
        description=(
            "Búsqueda por nombre o código, sin distinguir mayúsculas ni acentos. "
            "Cada palabra tiene que aparecer en el nombre o en el código."
        ),
    )
    sort: ProductSort = Field(default=ProductSort.MANUAL, description="Orden del listado.")
    limit: int = Field(
        default=DEFAULT_PAGE_SIZE,
        ge=1,
        le=MAX_PAGE_SIZE,
        description="Cuántos productos traer como máximo.",
    )
    offset: int = Field(default=0, ge=0, description="Cuántos productos saltear desde el inicio.")


class FacetValue(BaseModel):
    value: str = Field(description="Lo que se pasa en la query string: slug, o etiqueta de talle.")
    name: str
    count: int = Field(
        description="Productos con este valor, con los demás filtros aplicados (no el propio)."
    )


class CategoryFacetValue(FacetValue):
    parent: str | None = Field(description="Slug de la categoría madre; null en las de nivel 1.")


class ProductFacets(BaseModel):
    """Valores con resultados en la sección. Una lista vacía es un filtro que no se muestra."""

    categories: list[CategoryFacetValue] = Field(
        description="En orden de árbol: cada categoría de nivel 1 seguida de sus hijas."
    )
    versions: list[FacetValue] = Field(description="Vacía con las versiones apagadas.")
    collections: list[FacetValue] = Field(
        description="Vacía con las colecciones apagadas o con una sola colección cargada."
    )
    tags: list[FacetValue]
    sizes: list[FacetValue] = Field(description="Solo en la sección En stock.")


class ProductList(BaseModel):
    items: list[ProductListItem] = Field(description="La página pedida.")
    has_more: bool = Field(description="Si hay más productos después de esta página.")
    total: int = Field(description="Productos que cumplen los filtros, en todas las páginas.")
    facets: ProductFacets = Field(
        description="Calculadas sobre todo el listado filtrado, no sobre la página."
    )


class NamedRef(BaseModel):
    slug: str
    name: str


class ProductSizeOut(BaseModel):
    label: str
    status: SizeStatus = Field(
        description=(
            "in_stock y out_of_stock en un producto de stock (sin stock se muestra tachado, "
            "pero se puede elegir); on_order en un encargue o un agotado que pasó a encargue."
        )
    )
    inquiries: list[Inquiry] = Field(
        description=(
            "La consulta por este talle, una por canal ofrecido (WhatsApp primero), con el "
            "mensaje y el link ya armados. Vacía si la tienda no cargó canales."
        )
    )


class StoryItemOut(BaseModel):
    """Un ítem de la historia del producto. Cada tipo usa los campos a su manera:
    un hito (una tarjeta) muestra año y título y, al darse vuelta, la anécdota en
    ``body``; una cifra es el valor en ``title`` y su leyenda en ``body``; un dato
    curioso es el dato en ``title``, seguido de ``body`` si lo tiene."""

    kind: StoryItemKind
    year: int | None = Field(description="Año del hito; null en cifras y datos curiosos.")
    title: str
    body: str | None


class ProductDetail(BaseModel):
    code: str = Field(
        description="Código permanente del producto: prefijo de la tienda y número (ABC-014)."
    )
    name: str
    slug: str
    price: int = Field(description="Precio en la unidad menor de la moneda (centavos).")
    currency: str
    section: Section = Field(
        description="Sección donde aparece: un producto de stock agotado va a Por encargue."
    )
    availability: Availability = Field(description="Disponibilidad de cara al cliente.")
    description: str | None
    season: str | None
    category: NamedRef = Field(description="La categoría asignada (puede ser de nivel 2).")
    version: NamedRef | None = Field(description="Null sin versión o con las versiones apagadas.")
    collection: NamedRef | None = Field(description="Null con las colecciones apagadas.")
    images: list[ImageOut] = Field(description="En orden: la primera es la portada.")
    sizes: list[ProductSizeOut] = Field(
        description=(
            "En el orden del grupo de talles. En stock, los del producto; en un encargue o "
            "un agotado que pasó a encargue, todos los del grupo de su categoría."
        )
    )
    on_order_notice: str | None = Field(
        description=(
            "Aviso de encargue que edita el admin. Solo en un encargue o un agotado que pasó "
            "a encargue, y null si no está cargado."
        )
    )
    story: list[StoryItemOut] = Field(
        description=(
            "Historia del producto: hitos, después cifras y al final datos curiosos, cada "
            "tipo en su orden de carga. Vacía si el producto no tiene o si la función "
            "product_story está apagada (entonces la sección no se muestra)."
        )
    )


# --- Admin ----------------------------------------------------------------------


class AdminProductQuery(BaseModel):
    """Query string del listado del admin: búsqueda, filtro y página."""

    q: str | None = Field(
        default=None,
        max_length=MAX_SEARCH_LENGTH,
        description=(
            "Búsqueda por nombre o código, sin distinguir mayúsculas ni acentos. "
            "Cada palabra tiene que aparecer en el nombre o en el código."
        ),
    )
    filter: AdminFilter = Field(
        default=AdminFilter.ALL,
        description=(
            "all: todos menos los archivados. stock, on_order: los de esa sección (con la "
            "misma regla del catálogo público). sold_out: los agotados. draft, hidden, "
            "archived: los de ese estado. Salvo archived, ninguno trae archivados."
        ),
    )
    limit: int = Field(
        default=DEFAULT_PAGE_SIZE,
        ge=1,
        le=MAX_PAGE_SIZE,
        description="Cuántos productos traer como máximo.",
    )
    offset: int = Field(default=0, ge=0, description="Cuántos productos saltear desde el inicio.")


class AdminSizeOut(BaseModel):
    label: str
    status: SizeStatus = Field(
        description=(
            "En un producto de stock, in_stock u out_of_stock (se muestra tachado), aunque "
            "esté agotado; en un encargue, on_order para todos los talles de su grupo."
        )
    )


class AdminProductListItem(BaseModel):
    code: str = Field(
        description="Código permanente del producto: prefijo de la tienda y número (ABC-014)."
    )
    name: str
    price: int = Field(description="Precio en la unidad menor de la moneda (centavos).")
    currency: str
    status: ProductStatus
    featured: bool = Field(description="Si está destacado en la home.")
    section: Section = Field(
        description=(
            "Sección donde aparece (o aparecería, si no está publicado), con la misma "
            "regla del catálogo público."
        )
    )
    availability: Availability = Field(
        description="Disponibilidad con la regla del catálogo público: dice si está agotado."
    )
    sizes: list[AdminSizeOut] = Field(description="En el orden del grupo de talles.")
    cover: ImageOut | None = Field(description="La primera imagen del producto, si tiene.")


class AdminProductList(BaseModel):
    items: list[AdminProductListItem] = Field(
        description="La página pedida, del producto más nuevo al más viejo."
    )
    has_more: bool = Field(description="Si hay más productos después de esta página.")
    total: int = Field(description="Productos que cumplen el filtro, en todas las páginas.")
