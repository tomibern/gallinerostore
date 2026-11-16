"""Consultas del detalle: por cada talle y canal, el mensaje prearmado y su link.

La API arma todo (ADR 0005): la web solo elige el del talle y canal tocados, sin
esperar nada, así el clic abre WhatsApp o copia dentro del gesto de la persona. La
plantilla depende del caso del talle (en stock, sin stock, por encargue o agotado por
encargue); si la tienda no cargó la suya, se usa la neutra del núcleo.
"""

from typing import Any
from urllib.parse import quote, unquote

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, StoreFeatures, get_settings, get_store_config
from app.modules.settings.models import SETTINGS_ROW_ID, StoreSettings
from app.modules.settings.seed import SettingsSeed
from tests.conftest import settings_seed

WHATSAPP = "5491100000000"


@pytest.fixture
async def contact(db_session: AsyncSession, seeded: None) -> None:
    await settings_seed(db_session)


async def _detail(client: httpx.AsyncClient, slug: str) -> dict[str, Any]:
    items = (await client.get("/products")).json()["items"]
    code = next(p["code"] for p in items if p["slug"] == slug)
    response = await client.get(f"/products/{code.lower()}")
    assert response.status_code == 200
    detail: dict[str, Any] = response.json()
    return detail


def _size(detail: dict[str, Any], label: str) -> dict[str, Any]:
    size: dict[str, Any] = next(s for s in detail["sizes"] if s["label"] == label)
    return size


def _inquiry(detail: dict[str, Any], label: str, channel: str) -> dict[str, Any]:
    inquiry: dict[str, Any] = next(
        i for i in _size(detail, label)["inquiries"] if i["channel"] == channel
    )
    return inquiry


def _link(detail: dict[str, Any]) -> str:
    return f"https://tienda.test/p/{detail['code'].lower()}"


async def test_in_stock_size_uses_the_store_template_with_a_whatsapp_link(
    client: httpx.AsyncClient, contact: None
) -> None:
    detail = await _detail(client, "remera-completa")

    inquiry = _inquiry(detail, "S", "whatsapp")

    # Plantilla del fixture (sin {code}), con la URL pública de la configuración.
    message = f"Hola! Me interesa Remera completa, talle S (en stock). {_link(detail)}"
    assert inquiry["message"] == message
    assert inquiry["url"] == f"https://wa.me/{WHATSAPP}?text={quote(message, safe='')}"
    assert unquote(inquiry["url"].split("?text=", 1)[1]) == message
    assert "+" not in inquiry["url"]


async def test_each_size_has_its_own_message(client: httpx.AsyncClient, contact: None) -> None:
    detail = await _detail(client, "remera-completa")

    messages = [_inquiry(detail, label, "whatsapp")["message"] for label in ("S", "M", "L")]

    for label, message in zip(("S", "M", "L"), messages, strict=True):
        assert f", talle {label} " in message


async def test_out_of_stock_size_falls_back_to_the_neutral_template(
    client: httpx.AsyncClient, contact: None
) -> None:
    # El fixture no tiene plantilla out_of_stock: va la neutra del núcleo, con el código.
    detail = await _detail(client, "remera-basica")

    message = _inquiry(detail, "M", "whatsapp")["message"]

    assert message == (
        f"¡Hola! Me interesa Remera básica ({detail['code']}), talle M "
        f"(sin stock, consulto disponibilidad). {_link(detail)}"
    )


async def test_on_order_size_uses_the_on_order_template(
    client: httpx.AsyncClient, contact: None
) -> None:
    detail = await _detail(client, "buzo-a-pedido")

    message = _inquiry(detail, "XL", "whatsapp")["message"]

    assert message == f"Hola! Me interesa Buzo a pedido, talle XL (por encargue). {_link(detail)}"


async def test_sold_out_on_order_size_uses_its_own_template(
    client: httpx.AsyncClient, contact: None
) -> None:
    detail = await _detail(client, "remera-agotada")

    message = _inquiry(detail, "L", "whatsapp")["message"]

    assert message == (
        f"¡Hola! Me interesa Remera agotada ({detail['code']}), talle L "
        f"(se agotó, por encargue). {_link(detail)}"
    )


async def test_sold_out_on_order_uses_the_store_template_when_it_has_one(
    client: httpx.AsyncClient, db_session: AsyncSession, seeded: None
) -> None:
    await settings_seed(
        db_session, message_templates={"sold_out_on_order": "Agotado {product} {size}"}
    )

    detail = await _detail(client, "remera-agotada")

    assert _inquiry(detail, "S", "whatsapp")["message"] == "Agotado Remera agotada S"


async def test_sold_out_with_on_order_turned_off_asks_for_availability(
    app: FastAPI, client: httpx.AsyncClient, settings: Settings, contact: None
) -> None:
    store = settings.store_config.model_copy(update={"features": StoreFeatures(on_order=False)})
    app.dependency_overrides[get_store_config] = lambda: store

    detail = await _detail(client, "remera-agotada")

    assert "(sin stock, consulto disponibilidad)" in _inquiry(detail, "S", "whatsapp")["message"]


async def test_instagram_is_left_out_with_its_feature_turned_off(
    client: httpx.AsyncClient, contact: None
) -> None:
    detail = await _detail(client, "remera-completa")

    assert [i["channel"] for i in _size(detail, "S")["inquiries"]] == ["whatsapp"]


async def test_instagram_has_the_same_message_and_a_link_to_the_chat(
    client: httpx.AsyncClient, contact: None, instagram_on: None
) -> None:
    detail = await _detail(client, "remera-completa")

    whatsapp, instagram = _size(detail, "M")["inquiries"]

    assert whatsapp["channel"] == "whatsapp"
    assert instagram["channel"] == "instagram"
    # Instagram no acepta texto en el link: el mensaje va aparte, para copiarlo.
    assert instagram["message"] == whatsapp["message"]
    assert instagram["url"] == "https://ig.me/m/tienda.de.prueba"


async def test_a_channel_that_is_not_loaded_is_left_out(
    client: httpx.AsyncClient, db_session: AsyncSession, seeded: None, instagram_on: None
) -> None:
    await settings_seed(db_session, contact_channels={"instagram": {"username": "solo.ig"}})

    detail = await _detail(client, "remera-completa")

    assert [i["channel"] for i in _size(detail, "S")["inquiries"]] == ["instagram"]


async def test_without_store_settings_there_are_no_inquiries(
    client: httpx.AsyncClient, seeded: None
) -> None:
    detail = await _detail(client, "remera-completa")

    assert all(size["inquiries"] == [] for size in detail["sizes"])


@pytest.mark.parametrize(
    "template", ["Hola {product", "Hola {nombre}", "Hola {product.__class__}", "{0} {}"]
)
async def test_a_broken_template_is_left_as_is_instead_of_failing(
    client: httpx.AsyncClient, db_session: AsyncSession, seeded: None, template: str
) -> None:
    # En la Fase 4 las plantillas las edita el admin: una mal escrita no tira el detalle.
    await settings_seed(db_session, message_templates={"stock": template})

    detail = await _detail(client, "remera-completa")

    assert _inquiry(detail, "S", "whatsapp")["message"] == template


async def test_site_url_with_a_trailing_slash_gives_a_clean_link(
    app: FastAPI, client: httpx.AsyncClient, settings: Settings, contact: None
) -> None:
    with_slash = settings.model_copy(update={"site_url": "https://tienda.test/"})
    app.dependency_overrides[get_settings] = lambda: with_slash

    detail = await _detail(client, "remera-completa")

    assert _inquiry(detail, "S", "whatsapp")["message"].endswith(_link(detail))


@pytest.mark.parametrize(
    "channels",
    [
        {"whatsapp": {"number": "+5491100000000"}},
        {"whatsapp": {"number": "54 9 11 0000-0000"}},
        {"whatsapp": {"number": "1234"}},
        {"instagram": {"username": "tienda/de?prueba"}},
        {"telegram": {"username": "tienda"}},
    ],
)
def test_seed_rejects_malformed_contact_channels(channels: dict[str, Any]) -> None:
    with pytest.raises(ValueError):
        SettingsSeed.model_validate({"contact_channels": channels})


async def test_a_malformed_channel_in_the_settings_row_is_left_out(
    client: httpx.AsyncClient, db_session: AsyncSession, seeded: None, instagram_on: None
) -> None:
    # La forma se valida al cargar, pero un dato mal guardado no tira el detalle.
    db_session.add(
        StoreSettings(
            id=SETTINGS_ROW_ID,
            contact_channels={
                "whatsapp": {"number": "+54 9 11"},
                "instagram": {"username": "tienda.de.prueba"},
            },
        )
    )
    await db_session.flush()

    detail = await _detail(client, "remera-completa")

    assert [i["channel"] for i in _size(detail, "S")["inquiries"]] == ["instagram"]
