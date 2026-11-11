"""Configuración de la API.

Dos fuentes:

- Variables de entorno (o el ``.env`` de la raíz): conexiones e infraestructura.
- ``config/store.toml``: datos de la tienda del cliente (nombre, moneda, features).
"""

import tomllib
from functools import cached_property
from pathlib import Path

from fastapi import Request
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

# Raíz del monorepo en desarrollo. En la imagen de Docker no existe esa
# estructura: ahí STORE_CONFIG_PATH se define por variable de entorno.
_HERE = Path(__file__).resolve()
REPO_ROOT = _HERE.parents[4] if len(_HERE.parents) > 4 else _HERE.parents[-1]


class StoreInfo(BaseModel):
    name: str
    brand: str
    locale: str
    currency: str
    price_decimals: int
    code_prefix: str
    collection_label: str


class StoreFeatures(BaseModel):
    collections: bool = True
    versions: bool = True
    on_order: bool = True
    instagram: bool = True
    metrics: bool = True
    product_story: bool = True


class StoreConfig(BaseModel):
    store: StoreInfo
    features: StoreFeatures = StoreFeatures()

    @classmethod
    def from_toml(cls, path: Path) -> "StoreConfig":
        with path.open("rb") as f:
            return cls.model_validate(tomllib.load(f))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", extra="ignore")

    database_url: str
    s3_endpoint_url: str
    s3_access_key: str
    s3_secret_key: str
    s3_region: str = "us-east-1"
    s3_bucket: str = "media"
    store_config_path: Path = REPO_ROOT / "config" / "store.toml"
    seed_path: Path = REPO_ROOT / "config" / "seed.toml"

    @cached_property
    def store_config(self) -> StoreConfig:
        return StoreConfig.from_toml(self.store_config_path)


def get_settings(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


def get_store_config(request: Request) -> StoreConfig:
    return get_settings(request).store_config
