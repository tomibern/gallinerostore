from urllib.parse import quote

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.settings.schemas import FaqItem
from app.modules.settings.service import split_faq
from tests.conftest import settings_seed


async def test_store_exposes_public_configuration(client: httpx.AsyncClient) -> None:
    response = await client.get("/store")

    assert response.status_code == 200
    assert response.json() == {
        "name": "Tienda de Prueba",
        "locale": "es-AR",
        "currency": "USD",
        "price_decimals": 2,
        "collection_label": "Marca",
        "features": {
            "collections": True,
            "versions": False,
            "on_order": True,
            "instagram": False,
            "metrics": True,
            "product_story": False,
        },
        "home_blocks": [
            {"key": "galeria", "slides": []},
            {"key": "sin-fotos", "slides": []},
        ],
        # Sin la fila de configuración no hay contenido ni a quién escribirle.
        "channels": [],
        "general_inquiries": [],
        "on_order_notice": None,
        "how_to_buy_md": "",
        "faq_intro_md": "",
        "faq": [],
    }


# «Cómo comprar», preguntas frecuentes y consulta general salen de la configuración
# que edita el admin (la fila de `settings`). Las preguntas se parten en la API: cada
# encabezado `##` abre una, así la web solo dibuja el acordeón.

WHATSAPP = "5491100000000"


async def test_store_exposes_how_to_buy_and_the_faq_split_by_question(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    await settings_seed(db_session)

    body = (await client.get("/store")).json()

    assert body["how_to_buy_md"] == "## Cómo comprar\n\nEscribinos."
    assert body["on_order_notice"] == "Demora a confirmar."
    assert body["faq_intro_md"] == "Respondemos por chat."
    assert body["faq"] == [
        {"question": "¿Envían?", "answer_md": "Sí, a todo el país."},
        {"question": "¿Cómo pago?", "answer_md": "Por **transferencia**."},
    ]


async def test_general_inquiry_uses_the_core_template_when_the_store_has_none(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    # El fixture no tiene plantilla `general` y tiene Instagram apagado.
    await settings_seed(db_session)

    body = (await client.get("/store")).json()

    message = "¡Hola! Busco algo que no está en el catálogo."
    assert body["channels"] == ["whatsapp"]
    assert body["general_inquiries"] == [
        {
            "channel": "whatsapp",
            "message": message,
            "url": f"https://wa.me/{WHATSAPP}?text={quote(message, safe='')}",
        }
    ]


async def test_general_inquiry_opens_both_channels_with_the_store_template(
    client: httpx.AsyncClient, db_session: AsyncSession, instagram_on: None
) -> None:
    # El espacio final es a propósito: la persona sigue escribiendo en el chat.
    message = "Hola! Busco algo que no está: "
    await settings_seed(db_session, message_templates={"general": message})

    body = (await client.get("/store")).json()

    assert body["channels"] == ["whatsapp", "instagram"]
    assert body["general_inquiries"] == [
        {
            "channel": "whatsapp",
            "message": message,
            "url": f"https://wa.me/{WHATSAPP}?text=Hola%21%20Busco%20algo%20que%20no%20est%C3%A1%3A%20",
        },
        {
            "channel": "instagram",
            "message": message,
            "url": "https://ig.me/m/tienda.de.prueba",
        },
    ]


async def test_a_variable_without_value_stays_as_text_instead_of_breaking_the_store(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    # La consulta general no tiene producto: si el admin escribe {product}, queda así.
    await settings_seed(db_session, message_templates={"general": "Busco {product}. {link}"})

    response = await client.get("/store")

    assert response.status_code == 200
    assert response.json()["general_inquiries"][0]["message"] == "Busco {product}. {link}"


@pytest.mark.parametrize(
    ("faq_md", "intro", "faq"),
    [
        pytest.param("", "", [], id="vacía"),
        pytest.param(
            "Solo texto, sin preguntas.", "Solo texto, sin preguntas.", [], id="sin-encabezados"
        ),
        pytest.param("## ¿Envían? ##\nSí.", "", [("¿Envían?", "Sí.")], id="encabezado-con-cierre"),
        pytest.param(
            "##   \nHuérfano.\n## ¿Cambios?\nNo.",
            "",
            [("¿Cambios?", "No.")],
            id="pregunta-vacía-se-descarta",
        ),
        pytest.param(
            "## ¿Código?\n```\n## no es pregunta\n```\nListo.",
            "",
            [("¿Código?", "```\n## no es pregunta\n```\nListo.")],
            id="ignora-bloques-de-código",
        ),
        pytest.param(
            "### Subtítulo\n\n## ¿Envían?\n\n### Detalle\n\nSí.",
            "### Subtítulo",
            [("¿Envían?", "### Detalle\n\nSí.")],
            id="solo-parte-con-dos-numerales",
        ),
    ],
)
def test_split_faq(faq_md: str, intro: str, faq: list[tuple[str, str]]) -> None:
    assert split_faq(faq_md) == (
        intro,
        [FaqItem(question=question, answer_md=answer) for question, answer in faq],
    )
