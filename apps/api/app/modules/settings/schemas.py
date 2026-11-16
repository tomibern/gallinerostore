from pydantic import BaseModel, Field

from app.core.config import StoreFeatures


class HomeSlideOut(BaseModel):
    full: str = Field(description="Ruta de la foto (lado mayor 1600 px), bajo /media.")
    alt: str


class HomeBlock(BaseModel):
    """Un bloque con carrusel de la home. Sus textos salen del diccionario de la web
    (``home.blocks.<key>.*``); la API solo da la clave y las fotos."""

    key: str = Field(description="Clave del bloque, declarada en la configuración de la tienda.")
    slides: list[HomeSlideOut] = Field(
        description="Hasta 4 fotos, en su orden. Vacía si el bloque todavía no tiene fotos."
    )


class PublicStore(BaseModel):
    """Lo que la web necesita saber de la tienda. Nada secreto."""

    name: str
    locale: str
    currency: str
    price_decimals: int
    collection_label: str
    features: StoreFeatures
    home_blocks: list[HomeBlock] = Field(
        description="Bloques con carrusel de la home, en el orden de la configuración."
    )
