from app.core.config import StoreConfig
from app.modules.settings.schemas import PublicStore


def public_store(config: StoreConfig) -> PublicStore:
    store = config.store
    return PublicStore(
        name=store.name,
        locale=store.locale,
        currency=store.currency,
        price_decimals=store.price_decimals,
        collection_label=store.collection_label,
        features=config.features,
    )
