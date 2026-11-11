"""Imágenes de prueba para el seed: un cuadro de color con el nombre y el código."""

import hashlib
import io
import textwrap
import unicodedata

from PIL import Image, ImageDraw, ImageFont

SIZE = 1600


def _ascii(text: str) -> str:
    """La fuente que trae Pillow solo dibuja ASCII: sin tildes, eñes ni rayas."""
    text = text.replace("—", "-").replace("–", "-").replace("¿", "").replace("¡", "")
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if c.isascii())


def placeholder_image(title: str, code: str) -> bytes:
    """PNG de 1600 × 1600. El color sale del código, así cada producto tiene el suyo."""
    hue = int(hashlib.sha256(code.encode()).hexdigest()[:2], 16)
    background = (180 + hue % 60, 60 + hue % 120, 70 + hue % 90)
    image = Image.new("RGB", (SIZE, SIZE), background)
    draw = ImageDraw.Draw(image)

    title_font = ImageFont.load_default(size=110)
    code_font = ImageFont.load_default(size=80)
    lines = textwrap.wrap(_ascii(title), width=18)
    y = SIZE // 2 - 70 * len(lines)
    for line in lines:
        draw.text((SIZE // 2, y), line, font=title_font, fill="white", anchor="mm")
        y += 140
    draw.text((SIZE // 2, y + 60), _ascii(code), font=code_font, fill="white", anchor="mm")

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
