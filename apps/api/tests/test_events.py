"""Eventos anónimos: visitas y consultas que manda la web, sin datos personales.

`POST /events` guarda cada tipo con sus campos y rechaza lo que no corresponde: un tipo
desconocido, un campo de otro tipo, un producto que no está en el catálogo público o un
talle que el producto no ofrece. La IP no se guarda en ningún lado.
"""

from typing import Any

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_store_config
from app.modules.catalog.models import Product, Size
from app.modules.events.models import Event

SESSION = "0123456789abcdef0123456789abcdef"


def _event(**fields: Any) -> dict[str, Any]:
    return {"session_id": SESSION, "source": "directo", "device": "mobile", **fields}


async def _code(db_session: AsyncSession, slug: str) -> str:
    code = await db_session.scalar(select(Product.code).where(Product.slug == slug))
    assert code is not None
    return code


async def _saved(db_session: AsyncSession) -> list[Event]:
    return list((await db_session.scalars(select(Event).order_by(Event.id))).all())


async def _size_label(db_session: AsyncSession, size_id: int | None) -> str | None:
    if size_id is None:
        return None
    return await db_session.scalar(select(Size.label).where(Size.id == size_id))


async def test_page_view_is_saved_with_its_page(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    response = await client.post("/events", json=_event(type="page_view", page="stock"))

    assert response.status_code == 204
    [event] = await _saved(db_session)
    assert event.type == "page_view"
    assert event.page == "stock"
    assert event.session_id == SESSION
    assert event.source == "directo"
    assert event.device == "mobile"
    assert event.product_id is None
    assert event.channel is None


@pytest.mark.parametrize("page", ["home", "stock", "on_order", "how_to_buy"])
async def test_page_view_accepts_the_home_the_listings_and_how_to_buy(
    client: httpx.AsyncClient, page: str
) -> None:
    response = await client.post("/events", json=_event(type="page_view", page=page))

    assert response.status_code == 204


async def test_product_view_is_saved_with_its_product(
    client: httpx.AsyncClient, db_session: AsyncSession, seeded: None
) -> None:
    code = await _code(db_session, "remera-basica")

    response = await client.post(
        "/events", json=_event(type="product_view", product_code=code.lower(), device="desktop")
    )

    assert response.status_code == 204
    [event] = await _saved(db_session)
    assert event.type == "product_view"
    product = await db_session.scalar(select(Product).where(Product.code == code))
    assert product is not None
    assert event.product_id == product.id
    assert event.device == "desktop"
    assert event.page is None


async def test_contact_click_is_saved_with_product_channel_and_size(
    client: httpx.AsyncClient, db_session: AsyncSession, seeded: None
) -> None:
    code = await _code(db_session, "remera-basica")

    response = await client.post(
        "/events",
        json=_event(type="contact_click", product_code=code, channel="whatsapp", size="M"),
    )

    assert response.status_code == 204
    [event] = await _saved(db_session)
    assert event.type == "contact_click"
    assert event.channel == "whatsapp"
    assert event.product_id is not None
    # M está sin stock, pero se ofrece (se consulta su disponibilidad).
    assert await _size_label(db_session, event.size_id) == "M"


async def test_contact_click_on_an_on_order_product_takes_the_size_from_its_group(
    client: httpx.AsyncClient, db_session: AsyncSession, seeded: None
) -> None:
    """Un encargue no tiene talles propios: ofrece todos los del grupo de su categoría."""
    code = await _code(db_session, "buzo-a-pedido")

    response = await client.post(
        "/events",
        json=_event(type="contact_click", product_code=code, channel="instagram", size="L"),
    )

    assert response.status_code == 204
    [event] = await _saved(db_session)
    assert await _size_label(db_session, event.size_id) == "L"


async def test_general_contact_click_is_saved_with_channel_and_page(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    response = await client.post(
        "/events",
        json=_event(type="general_contact_click", channel="instagram", page="not_found"),
    )

    assert response.status_code == 204
    [event] = await _saved(db_session)
    assert event.type == "general_contact_click"
    assert event.channel == "instagram"
    assert event.page == "not_found"
    assert event.product_id is None


async def test_source_is_trimmed_and_lowercased(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    response = await client.post(
        "/events", json=_event(type="page_view", page="home", source="  Historia ")
    )

    assert response.status_code == 204
    [event] = await _saved(db_session)
    assert event.source == "historia"


@pytest.mark.parametrize(
    "body",
    [
        pytest.param(_event(type="purchase"), id="unknown type"),
        pytest.param(_event(page="home"), id="no type"),
        pytest.param(_event(type="page_view", page="admin"), id="unknown page"),
        pytest.param(_event(type="page_view", page="product"), id="product page in a visit"),
        pytest.param(_event(type="page_view"), id="page view without page"),
        pytest.param(
            _event(type="page_view", page="home", product_code="TP-001"),
            id="field of another type",
        ),
        pytest.param(_event(type="product_view"), id="product view without product"),
        pytest.param(
            _event(type="contact_click", product_code="TP-001", channel="whatsapp"),
            id="contact click without size",
        ),
        pytest.param(
            _event(type="contact_click", product_code="TP-001", channel="email", size="M"),
            id="unknown channel",
        ),
        pytest.param(
            _event(type="general_contact_click", channel="whatsapp"),
            id="general contact click without page",
        ),
        pytest.param(
            _event(type="page_view", page="home", session_id="not-random"),
            id="malformed session id",
        ),
        pytest.param(_event(type="page_view", page="home", device="tv"), id="unknown device"),
        pytest.param(_event(type="page_view", page="home", source="  "), id="blank source"),
        pytest.param(_event(type="page_view", page="home", source="x" * 61), id="source too long"),
        pytest.param(
            {"type": "page_view", "page": "home", "source": "directo", "device": "mobile"},
            id="no session id",
        ),
    ],
)
async def test_invalid_events_are_rejected(
    client: httpx.AsyncClient, db_session: AsyncSession, body: dict[str, Any]
) -> None:
    response = await client.post("/events", json=body)

    assert response.status_code == 422
    assert await _saved(db_session) == []


@pytest.mark.parametrize("slug", ["remera-borrador", "remera-oculta", "buzo-archivado"])
async def test_products_outside_the_public_catalog_are_rejected(
    client: httpx.AsyncClient, db_session: AsyncSession, seeded: None, slug: str
) -> None:
    code = await _code(db_session, slug)

    response = await client.post("/events", json=_event(type="product_view", product_code=code))

    assert response.status_code == 422
    assert await _saved(db_session) == []


async def test_an_unknown_product_is_rejected(
    client: httpx.AsyncClient, db_session: AsyncSession, seeded: None
) -> None:
    response = await client.post(
        "/events",
        json=_event(type="contact_click", product_code="TP-999", channel="whatsapp", size="M"),
    )

    assert response.status_code == 422
    assert await _saved(db_session) == []


async def test_a_size_the_product_does_not_offer_is_rejected(
    client: httpx.AsyncClient, db_session: AsyncSession, seeded: None
) -> None:
    code = await _code(db_session, "remera-basica")  # S, M y L

    response = await client.post(
        "/events",
        json=_event(type="contact_click", product_code=code, channel="whatsapp", size="XL"),
    )

    assert response.status_code == 422
    assert await _saved(db_session) == []


async def test_with_metrics_off_events_are_accepted_but_not_saved(
    app: FastAPI, settings: Settings, client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    """La web manda igual: la regla vive en un solo lugar."""
    features = settings.store_config.features.model_copy(update={"metrics": False})
    store = settings.store_config.model_copy(update={"features": features})
    app.dependency_overrides[get_store_config] = lambda: store

    response = await client.post("/events", json=_event(type="page_view", page="home"))

    assert response.status_code == 204
    assert await _saved(db_session) == []


async def test_events_endpoints_for_e2e_are_off_by_default(client: httpx.AsyncClient) -> None:
    response = await client.get("/e2e/events", params={"session_id": SESSION})

    assert response.status_code == 404


async def test_events_endpoint_for_e2e_lists_the_events_of_a_session(
    app: FastAPI,
    settings: Settings,
    client: httpx.AsyncClient,
    db_session: AsyncSession,
    seeded: None,
) -> None:
    """Lo usa Playwright para ver que una visita y una consulta quedaron guardadas."""
    app.state.settings = settings.model_copy(update={"e2e_endpoints": True})
    code = await _code(db_session, "remera-basica")
    other = "f" * 32
    await client.post("/events", json=_event(type="product_view", product_code=code))
    await client.post(
        "/events",
        json=_event(type="contact_click", product_code=code, channel="whatsapp", size="S"),
    )
    await client.post("/events", json=_event(type="page_view", page="home", session_id=other))

    response = await client.get("/e2e/events", params={"session_id": SESSION})

    assert response.status_code == 200
    assert response.json() == [
        {
            "type": "product_view",
            "product_code": code,
            "channel": None,
            "size": None,
            "page": None,
            "source": "directo",
            "device": "mobile",
        },
        {
            "type": "contact_click",
            "product_code": code,
            "channel": "whatsapp",
            "size": "S",
            "page": None,
            "source": "directo",
            "device": "mobile",
        },
    ]


async def test_events_endpoint_for_e2e_is_not_in_the_openapi(client: httpx.AsyncClient) -> None:
    paths = (await client.get("/openapi.json")).json()["paths"]

    assert "/events" in paths
    assert not any(path.startswith("/e2e") for path in paths)
