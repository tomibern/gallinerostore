"""«Cómo comprar» y preguntas frecuentes que edita el admin, como listas.

El admin manda secciones (título y texto) y preguntas (pregunta y respuesta) en su
orden; la API las guarda como Markdown, un ``##`` por cada una, y la tienda las muestra
desde la próxima visita (``GET /store``).
"""

from typing import Any

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.service import create_admin
from tests.conftest import settings_seed

EMAIL = "admin@tienda.test"
PASSWORD = "una-clave-larga"
ADMIN_HEADERS = {"X-Requested-With": "fetch"}
URL = "/admin/settings/how-to-buy"


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


async def _get(client: httpx.AsyncClient) -> dict[str, Any]:
    response = await client.get(URL)
    assert response.status_code == 200
    body: dict[str, Any] = response.json()
    return body


async def _put(client: httpx.AsyncClient, body: dict[str, Any]) -> httpx.Response:
    return await client.put(URL, json=body, headers=ADMIN_HEADERS)


def _topic(title: str, text: str = "") -> dict[str, str]:
    return {"title": title, "text": text}


def _entry(question: str, answer: str = "") -> dict[str, str]:
    return {"question": question, "answer": answer}


async def test_the_admin_gets_both_texts_split_into_lists(
    client: httpx.AsyncClient, admin: None
) -> None:
    assert await _get(client) == {
        "topics": [_topic("Cómo comprar", "Escribinos.")],
        "faq": [
            _entry("¿Envían?", "Sí, a todo el país."),
            _entry("¿Cómo pago?", "Por **transferencia**."),
        ],
    }


async def test_adding_reordering_and_removing_round_trips(
    client: httpx.AsyncClient, admin: None
) -> None:
    content = await _get(client)
    topics = [
        _topic("Pagos", "Por **transferencia**.\n\n1. Uno\n2. Dos"),
        content["topics"][0],
        _topic("Envíos"),
    ]
    # Se da vuelta el orden, se borra «¿Envían?» y se agrega una al final.
    faq = [content["faq"][1], _entry("¿Hacen cambios?", "Sí, dentro de los 30 días.")]

    saved = await _put(client, {"topics": topics, "faq": faq})

    assert saved.status_code == 200
    assert saved.json() == {"topics": topics, "faq": faq}
    assert await _get(client) == {"topics": topics, "faq": faq}


async def test_what_the_admin_saves_is_what_the_store_shows(
    client: httpx.AsyncClient, admin: None
) -> None:
    saved = await _put(
        client,
        {
            "topics": [
                _topic("Pagos", "Transferencia."),
                _topic("Envíos", "A todo el país."),
            ],
            "faq": [_entry("¿Hacen cambios?", "Sí.")],
        },
    )
    assert saved.status_code == 200

    store = (await client.get("/store")).json()

    assert store["how_to_buy_md"] == "## Pagos\n\nTransferencia.\n\n## Envíos\n\nA todo el país.\n"
    # El texto antes de la primera pregunta no lo edita el admin: se conserva.
    assert store["faq_intro_md"] == "Respondemos por chat."
    assert store["faq"] == [{"question": "¿Hacen cambios?", "answer_md": "Sí."}]


async def test_titles_and_texts_are_trimmed_and_a_title_ending_in_hash_keeps_it(
    client: httpx.AsyncClient, admin: None
) -> None:
    saved = await _put(
        client,
        {"topics": [_topic("  Talle #  ", "\n  Texto.  \n")], "faq": []},
    )

    assert saved.status_code == 200
    assert saved.json()["topics"] == [_topic("Talle #", "Texto.")]


async def test_empty_lists_leave_the_texts_empty(client: httpx.AsyncClient, admin: None) -> None:
    saved = await _put(client, {"topics": [], "faq": []})

    assert saved.status_code == 200
    store = (await client.get("/store")).json()
    assert store["how_to_buy_md"] == ""
    assert store["faq"] == []


@pytest.mark.parametrize(
    ("body", "loc"),
    [
        ({"topics": [_topic("Pagos"), _topic("   ")], "faq": []}, ["topics", 1, "title"]),
        ({"topics": [], "faq": [_entry("", "Una respuesta.")]}, ["faq", 0, "question"]),
    ],
)
async def test_an_empty_title_or_question_is_rejected_on_its_field(
    client: httpx.AsyncClient, admin: None, body: dict[str, Any], loc: list[Any]
) -> None:
    before = await _get(client)

    response = await _put(client, body)

    assert response.status_code == 422
    errors = response.json()["detail"]
    assert [(error["loc"][1:], error["type"]) for error in errors] == [(loc, "blank")]
    assert await _get(client) == before


@pytest.mark.parametrize(
    ("text", "error_type"),
    [
        ("Primero.\n## Otro tema", "section_heading"),
        ("```\ncódigo sin cerrar", "unclosed_fence"),
    ],
)
async def test_a_text_that_would_break_the_topics_is_rejected(
    client: httpx.AsyncClient, admin: None, text: str, error_type: str
) -> None:
    response = await _put(client, {"topics": [_topic("Pagos", text)], "faq": []})

    assert response.status_code == 422
    [error] = response.json()["detail"]
    assert error["loc"] == ["body", "topics", 0, "text"]
    assert error["type"] == error_type


async def test_a_heading_inside_a_code_block_is_just_text(
    client: httpx.AsyncClient, admin: None
) -> None:
    text = "Ejemplo:\n\n```\n## no es un tema\n```"

    saved = await _put(client, {"topics": [_topic("Pagos", text)], "faq": []})

    assert saved.status_code == 200
    assert (await _get(client))["topics"] == [_topic("Pagos", text)]


async def test_a_title_with_a_line_break_is_rejected(
    client: httpx.AsyncClient, admin: None
) -> None:
    response = await _put(client, {"topics": [], "faq": [_entry("¿Una\nPregunta?")]})

    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "multiline"


async def test_without_a_session_nothing_is_read_or_saved(
    client: httpx.AsyncClient, seeded: None
) -> None:
    read = await client.get(URL)
    saved = await _put(client, {"topics": [], "faq": []})

    assert read.status_code == saved.status_code == 401


async def test_saving_requires_the_anti_csrf_header(client: httpx.AsyncClient, admin: None) -> None:
    response = await client.put(URL, json={"topics": [], "faq": []})

    assert response.status_code == 403
