"""Procesamiento de imágenes: la API redimensiona y convierte a WebP al subir.

Cada imagen se guarda en dos tamaños: completa (lado mayor 1600 px) para el
detalle y miniatura (400 px) para los listados.
"""

import io
from dataclasses import dataclass

from PIL import Image, ImageOps

from app.core.storage import ObjectStorage

FULL_SIZE = 1600
THUMB_SIZE = 400
WEBP_QUALITY = 82
# method=2: el doble de rápido que el default (4) con archivos apenas ~4 % más grandes.
WEBP_METHOD = 2


@dataclass(frozen=True)
class StoredImage:
    # Posición entre las fotos del producto (0 = portada).
    position: int
    path_full: str
    path_thumb: str
    width: int
    height: int


def _to_webp(image: Image.Image, longest_side: int) -> tuple[bytes, int, int]:
    resized = image.copy()
    resized.thumbnail((longest_side, longest_side), Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    resized.save(buffer, format="WEBP", quality=WEBP_QUALITY, method=WEBP_METHOD)
    return buffer.getvalue(), resized.width, resized.height


def store_product_image(
    storage: ObjectStorage, product_code: str, position: int, data: bytes
) -> StoredImage:
    """Procesa una foto y la sube en los dos tamaños. Devuelve las rutas para guardar."""
    with Image.open(io.BytesIO(data)) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")
    full, width, height = _to_webp(image, FULL_SIZE)
    thumb, _, _ = _to_webp(image, THUMB_SIZE)

    base = f"products/{product_code}/{position + 1}"
    path_full, path_thumb = f"{base}-{FULL_SIZE}.webp", f"{base}-{THUMB_SIZE}.webp"
    storage.put(path_full, full, "image/webp")
    storage.put(path_thumb, thumb, "image/webp")
    return StoredImage(
        position=position, path_full=path_full, path_thumb=path_thumb, width=width, height=height
    )
