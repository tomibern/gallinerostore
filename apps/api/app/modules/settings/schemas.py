from pydantic import BaseModel

from app.core.config import StoreFeatures


class PublicStore(BaseModel):
    """Lo que la web necesita saber de la tienda. Nada secreto."""

    name: str
    locale: str
    currency: str
    price_decimals: int
    collection_label: str
    features: StoreFeatures
