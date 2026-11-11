"""Modelos Pydantic de entrada y salida del catálogo."""

from pydantic import BaseModel, Field

from app.modules.catalog.models import SaleMode


class ProductSizeOut(BaseModel):
    label: str
    in_stock: bool


class ProductListItem(BaseModel):
    code: str = Field(description="Código permanente del producto, por ejemplo GS-014.")
    name: str
    slug: str
    price: int = Field(description="Precio en la unidad menor de la moneda (centavos).")
    currency: str
    sale_mode: SaleMode
    out_of_stock: bool = Field(
        description="Producto de stock sin ningún talle disponible. Nunca en encargues."
    )
    sizes: list[ProductSizeOut] = Field(description="En el orden de su grupo de talles.")
