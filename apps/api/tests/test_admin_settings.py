"""Contacto, mensajes prearmados y aviso de encargue que edita el admin.

Lo que se guarda se ve en la tienda en la siguiente visita: el detalle arma sus
consultas con los canales y plantillas nuevos. La vista previa la arma la API con un
producto publicado real del caso (ADR 0005: la web nunca arma mensajes).
"""

from typing import Any
from urllib.parse import quote

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.service import create_admin
from tests.conftest import settings_seed

EMAIL = "admin@tienda.test"
PASSWORD = "una-clave-larga"
ADMIN_HEADERS = {"X-Requested-With": "fetch"}

TEMPLATES = {
    "stock": "Quiero {product} ({code}) en {size}. {link}",
    "out_of_stock": "¿Vuelve {product} en {size}?",
    "on_order": "Encargo {product} en {size}.",
    "sold_out_on_order": "Encargo {product} agotado, en {size}.",
    "general": "Busco algo que no está.",
}


def _body(**changes: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "contact_channels": {
            "whatsapp": {"number": "5491122223333"},
            "instagram": {"username": "otra.tienda"},
        },
        "message_templates": dict(TEMPLATES),
        "on_order_notice": "Tarda 30 días. Se pide una seña del 50%.",
    }
    return body | changes


@pytest.fixture
async def admin(client: httpx.AsyncClient, db_session: AsyncSession, seeded: None) -> None:
    """Tienda con el seed y su configuración, y el admin con la sesión abierta."""
    await settings_seed(db_session)
    await create_admin(db_session, EMAIL, PASSWORD)
    response = await client.post(
        "/admin/session",
        json={"email": EMAIL, "password": PASSWORD, "remember": False},
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 200


async def _put(client: httpx.AsyncClient, body: dict[str, Any]) -> httpx.Response:
    return await client.put("/admin/settings", json=body, headers=ADMIN_HEADERS)


async def _preview(client: httpx.AsyncClient, case: str, template: str) -> httpx.Response:
    return await client.post(
        "/admin/settings/message-preview",
        json={"case": case, "template": template},
        headers=ADMIN_HEADERS,
    )


def _errors(response: httpx.Response) -> dict[tuple[str | int, ...], str]:
    """Los errores de un 422, por campo (sin el «body» del principio)."""
    assert response.status_code == 422
    return {tuple(error["loc"][1:]): error["type"] for error in response.json()["detail"]}


async def _detail(client: httpx.AsyncClient, slug: str) -> dict[str, Any]:
    items = (await client.get("/products")).json()["items"]
    code = next(p["code"] for p in items if p["slug"] == slug)
    detail: dict[str, Any] = (await client.get(f"/products/{code.lower()}")).json()
    return detail


async def test_the_admin_sees_contact_templates_and_notice_with_the_variables_of_each_case(
    client: httpx.AsyncClient, admin: None
) -> None:
    response = await client.get("/admin/settings")

    assert response.status_code == 200
    data = response.json()
    assert data["contact_channels"] == {
        "whatsapp": {"number": "5491100000000"},
        "instagram": {"username": "tienda.de.prueba"},
    }
    # Las del fixture y, donde la tienda no cargó la suya, la neutra del núcleo.
    templates = data["message_templates"]
    assert templates["stock"] == "Hola! Me interesa {product}, talle {size} (en stock). {link}"
    assert set(templates) == set(TEMPLATES)
    assert all(templates.values())
    assert data["on_order_notice"] == "Demora a confirmar."
    assert data["message_variables"]["stock"] == ["product", "code", "size", "link"]
    assert data["message_variables"]["general"] == []


async def test_saving_contact_templates_and_notice_changes_the_store_on_the_next_visit(
    client: httpx.AsyncClient, admin: None
) -> None:
    response = await _put(client, _body())

    assert response.status_code == 200
    assert response.json()["message_templates"] == TEMPLATES
    assert (await client.get("/admin/settings")).json() == response.json()

    store = (await client.get("/store")).json()
    assert store["on_order_notice"] == "Tarda 30 días. Se pide una seña del 50%."
    assert store["general_inquiries"][0]["message"] == "Busco algo que no está."

    detail = await _detail(client, "remera-completa")
    size = next(s for s in detail["sizes"] if s["label"] == "S")
    whatsapp = next(i for i in size["inquiries"] if i["channel"] == "whatsapp")
    message = f"Quiero Remera completa ({detail['code']}) en S. https://tienda.test/p/{detail['code'].lower()}"
    assert whatsapp["message"] == message
    assert whatsapp["url"] == f"https://wa.me/5491122223333?text={quote(message, safe='')}"


async def test_the_whatsapp_number_is_saved_in_digits_as_people_write_it(
    client: httpx.AsyncClient, admin: None
) -> None:
    body = _body(contact_channels={"whatsapp": {"number": "+54 9 11 2222-3333"}, "instagram": None})

    response = await _put(client, body)

    assert response.status_code == 200
    assert response.json()["contact_channels"] == {
        "whatsapp": {"number": "5491122223333"},
        "instagram": None,
    }


async def test_an_empty_channel_is_not_offered(client: httpx.AsyncClient, admin: None) -> None:
    body = _body(contact_channels={"whatsapp": None, "instagram": {"username": "@otra.tienda"}})

    response = await _put(client, body)

    assert response.status_code == 200
    assert response.json()["contact_channels"]["instagram"] == {"username": "otra.tienda"}
    # El fixture tiene Instagram apagado: sin WhatsApp, la tienda no ofrece canales.
    assert (await client.get("/store")).json()["channels"] == []


@pytest.mark.parametrize("number", ["12345", "54 9 11 abcd 3333", "1234567890123456"])
async def test_an_invalid_whatsapp_number_is_rejected_on_its_field(
    client: httpx.AsyncClient, admin: None, number: str
) -> None:
    body = _body(contact_channels={"whatsapp": {"number": number}})

    errors = _errors(await _put(client, body))

    assert errors == {("contact_channels", "whatsapp", "number"): "string_pattern_mismatch"}
    whatsapp = (await client.get("/admin/settings")).json()["contact_channels"]["whatsapp"]
    assert whatsapp == {"number": "5491100000000"}


async def test_an_unknown_variable_is_rejected_on_its_template(
    client: httpx.AsyncClient, admin: None
) -> None:
    templates = TEMPLATES | {"on_order": "Encargo {producto} en {size}."}

    response = await _put(client, _body(message_templates=templates))

    assert _errors(response) == {("message_templates", "on_order"): "unknown_variable"}
    assert response.json()["detail"][0]["ctx"]["variable"] == "producto"


async def test_the_general_inquiry_has_no_product_variables(
    client: httpx.AsyncClient, admin: None
) -> None:
    templates = TEMPLATES | {"general": "Busco algo parecido a {product}."}

    errors = _errors(await _put(client, _body(message_templates=templates)))

    assert errors == {("message_templates", "general"): "unknown_variable"}


async def test_a_template_cannot_be_empty_and_every_error_comes_on_its_field(
    client: httpx.AsyncClient, admin: None
) -> None:
    body = _body(
        contact_channels={"instagram": {"username": "no vale"}},
        message_templates=TEMPLATES | {"stock": "   ", "general": "{link}"},
    )

    errors = _errors(await _put(client, body))

    assert errors == {
        ("contact_channels", "instagram", "username"): "string_pattern_mismatch",
        ("message_templates", "stock"): "blank",
        ("message_templates", "general"): "unknown_variable",
    }


@pytest.mark.parametrize("case", ["stock", "out_of_stock", "on_order", "sold_out_on_order"])
async def test_the_preview_uses_a_real_published_product_of_each_case(
    client: httpx.AsyncClient, admin: None, case: str
) -> None:
    response = await _preview(client, case, "{product} | {code} | {size} | {link}")

    assert response.status_code == 200
    preview = response.json()
    sample = preview["product"]
    assert sample is not None
    detail = (await client.get(f"/products/{sample['code'].lower()}")).json()
    offered = next(s for s in detail["sizes"] if s["label"] == sample["size"])
    # El talle de la muestra es de ese caso en el detalle público.
    assert _case(detail["availability"], offered["status"]) == case
    link = f"https://tienda.test/p/{sample['code'].lower()}"
    assert preview["message"] == f"{sample['name']} | {sample['code']} | {sample['size']} | {link}"


def _case(availability: str, status: str) -> str:
    if status == "on_order":
        return "sold_out_on_order" if availability == "sold_out_on_order" else "on_order"
    return "out_of_stock" if status == "out_of_stock" else "stock"


async def test_the_general_preview_has_no_product(client: httpx.AsyncClient, admin: None) -> None:
    response = await _preview(client, "general", "Hola, busco algo.")

    assert response.json() == {"message": "Hola, busco algo.", "product": None}


async def test_the_preview_rejects_an_unknown_variable(
    client: httpx.AsyncClient, admin: None
) -> None:
    errors = _errors(await _preview(client, "stock", "Hola {talle}"))

    assert errors == {("template",): "unknown_variable"}


async def test_the_preview_does_not_save_the_template(
    client: httpx.AsyncClient, admin: None
) -> None:
    await _preview(client, "stock", "Otra cosa {product}")

    stock = (await client.get("/admin/settings")).json()["message_templates"]["stock"]
    assert stock == "Hola! Me interesa {product}, talle {size} (en stock). {link}"


async def test_without_a_session_nothing_is_read_saved_or_previewed(
    client: httpx.AsyncClient, db_session: AsyncSession, seeded: None
) -> None:
    await settings_seed(db_session)

    read = await client.get("/admin/settings")
    saved = await _put(client, _body())
    previewed = await _preview(client, "stock", "{product}")

    assert read.status_code == saved.status_code == previewed.status_code == 401
    assert (await client.get("/store")).json()["on_order_notice"] == "Demora a confirmar."


async def test_saving_requires_the_anti_csrf_header(client: httpx.AsyncClient, admin: None) -> None:
    response = await client.put("/admin/settings", json=_body())

    assert response.status_code == 403
