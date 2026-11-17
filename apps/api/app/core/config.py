"""Configuración de la API.

Dos fuentes:

- Variables de entorno (o el ``.env`` de la raíz): conexiones e infraestructura.
- ``config/store.toml``: datos de la tienda del cliente (nombre, moneda, features).
"""

import tomllib
from functools import cached_property
from pathlib import Path
from typing import Annotated

from fastapi import Request
from pydantic import AfterValidator, BaseModel, Field, StringConstraints
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


# Clave de un bloque de la home: une la config, las fotos (home_slides.block) y los
# textos del diccionario (home.blocks.<clave>.*). Cabe en home_slides.block.
BlockKey = Annotated[str, StringConstraints(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$", max_length=40)]


def _unique(keys: list[str]) -> list[str]:
    repeated = sorted({key for key in keys if keys.count(key) > 1})
    if repeated:
        raise ValueError(f"Bloques repetidos en [home]: {', '.join(repeated)}")
    return keys


class StoreHome(BaseModel):
    # Bloques con carrusel, en el orden en que aparecen en la home.
    blocks: Annotated[list[BlockKey], AfterValidator(_unique)] = []


class StoreConfig(BaseModel):
    store: StoreInfo
    features: StoreFeatures = StoreFeatures()
    home: StoreHome = StoreHome()

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
    # Prefijo público de las fotos. Next reenvía /media/* al bucket (ADR 0003).
    media_base_url: str = "/media"
    # Dirección pública del sitio, para los links que salen de la API (por ejemplo,
    # el del producto en el mensaje prearmado). Cambia por entorno, no por cliente.
    site_url: str = "http://localhost:3000"
    # Proxies de confianza delante de la API que agregan la IP del visitante al final de
    # X-Forwarded-For (ADR 0006). Con 0 se usa la dirección de la conexión.
    trusted_proxy_hops: int = Field(default=1, ge=0)
    # Límite de frecuencia de los eventos. Se apaga para el e2e, que manda todo desde
    # la misma IP.
    rate_limit_enabled: bool = True
    # Endpoints de solo lectura para verificar los e2e (por ejemplo, los eventos de una
    # sesión). Nunca en producción.
    e2e_endpoints: bool = False
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
