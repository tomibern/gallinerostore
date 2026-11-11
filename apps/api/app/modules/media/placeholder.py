"""Imágenes de prueba para el seed: un cuadro de color con el nombre y el código."""

import hashlib
import io
import textwrap

from PIL import Image, ImageDraw, ImageFont

SIZE = 1600


def placeholder_image(title: str, code: str) -> bytes:
    """PNG de 1600 × 1600. El color sale del código, así cada producto tiene el suyo."""
    hue = int(hashlib.sha256(code.encode()).hexdigest()[:2], 16)
    background = (180 + hue % 60, 60 + hue % 120, 70 + hue % 90)
    image = Image.new("RGB", (SIZE, SIZE), background)
    draw = ImageDraw.Draw(image)

    title_font = ImageFont.load_default(size=110)
    code_font = ImageFont.load_default(size=80)
    lines = textwrap.wrap(title, width=18)
    y = SIZE // 2 - 70 * len(lines)
    for line in lines:
        draw.text((SIZE // 2, y), line, font=title_font, fill="white", anchor="mm")
        y += 140
    draw.text((SIZE // 2, y + 60), code, font=code_font, fill="white", anchor="mm")

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
