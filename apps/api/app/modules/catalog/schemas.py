"""Modelos Pydantic de entrada y salida del catálogo."""

from pydantic import BaseModel, Field

from app.modules.catalog.models import Availability, ProductSort, Section


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
    """Query string del listado. Varios valores de un filtro se suman (O) y filtros
    distintos se cruzan (Y). Un filtro que no aplica se ignora y un valor que no
    existe deja el listado vacío, así un link compartido nunca da error."""

    section: Section | None = Field(default=None, description="Solo los productos de esa sección.")
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
    sort: ProductSort = Field(default=ProductSort.MANUAL, description="Orden del listado.")


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
    items: list[ProductListItem]
    facets: ProductFacets
