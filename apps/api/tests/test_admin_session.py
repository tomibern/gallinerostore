"""Sesión del admin: entrar con email y contraseña, mantenerla y cerrarla (ADR 0008)."""

from datetime import timedelta

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.service import create_admin, ensure_admin
from tests.support import Clock

EMAIL = "admin@tienda.test"
PASSWORD = "una-clave-larga"
# Las escrituras del admin exigen este header (anti-CSRF).
ADMIN_HEADERS = {"X-Requested-With": "fetch"}


async def _login(client: httpx.AsyncClient, **changes: object) -> httpx.Response:
    body = {"email": EMAIL, "password": PASSWORD, "remember": False} | changes
    return await client.post("/admin/session", json=body, headers=ADMIN_HEADERS)


async def test_the_admin_logs_in_and_the_session_knows_who_they_are(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    await create_admin(db_session, EMAIL, PASSWORD)

    response = await _login(client)

    assert response.status_code == 200
    assert response.json() == {"email": EMAIL}
    me = await client.get("/admin/session")
    assert me.status_code == 200
    assert me.json() == {"email": EMAIL}


async def test_a_wrong_password_and_an_unknown_email_get_the_same_error(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    await create_admin(db_session, EMAIL, PASSWORD)

    wrong_password = await _login(client, password="otra-clave-cualquiera")
    unknown_email = await _login(client, email="otro@tienda.test")

    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()
    assert (await client.get("/admin/session")).status_code == 401


async def test_the_email_is_case_insensitive(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    await create_admin(db_session, EMAIL, PASSWORD)

    response = await _login(client, email="  ADMIN@Tienda.test ")

    assert response.status_code == 200


async def test_a_session_without_remember_lasts_until_the_browser_closes_or_24_hours(
    client: httpx.AsyncClient, db_session: AsyncSession, clock: Clock
) -> None:
    await create_admin(db_session, EMAIL, PASSWORD)

    response = await _login(client, remember=False)

    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=lax" in cookie and "secure" in cookie
    assert "max-age" not in cookie  # cookie de sesión del navegador
    clock.advance(timedelta(hours=23))
    assert (await client.get("/admin/session")).status_code == 200
    clock.advance(timedelta(hours=1))
    assert (await client.get("/admin/session")).status_code == 401


async def test_a_remembered_session_lasts_30_days_and_is_renewed_by_use(
    client: httpx.AsyncClient, db_session: AsyncSession, clock: Clock
) -> None:
    await create_admin(db_session, EMAIL, PASSWORD)

    response = await _login(client, remember=True)

    assert f"max-age={30 * 24 * 3600}" in response.headers["set-cookie"].lower()
    clock.advance(timedelta(days=29))
    renewed = await client.get("/admin/session")
    assert renewed.status_code == 200
    assert "max-age" in renewed.headers["set-cookie"].lower()  # la cookie también se renueva
    clock.advance(timedelta(days=29))
    assert (await client.get("/admin/session")).status_code == 200
    clock.advance(timedelta(days=30))
    assert (await client.get("/admin/session")).status_code == 401


async def test_logging_out_ends_the_session(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    await create_admin(db_session, EMAIL, PASSWORD)
    await _login(client)
    token = client.cookies["admin_session"]

    response = await client.delete("/admin/session", headers=ADMIN_HEADERS)

    assert response.status_code == 204
    assert "admin_session" not in client.cookies
    # Aunque alguien se haya guardado la cookie, la sesión ya no existe.
    client.cookies.set("admin_session", token)
    assert (await client.get("/admin/session")).status_code == 401


async def test_admin_writes_without_the_csrf_header_are_rejected(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    # Un formulario de otro sitio no puede mandar headers propios.
    await create_admin(db_session, EMAIL, PASSWORD)
    body = {"email": EMAIL, "password": PASSWORD}

    response = await client.post("/admin/session", json=body)

    assert response.status_code == 403
    assert (await client.get("/admin/session")).status_code == 401


async def test_the_development_seed_admin_can_log_in_and_seeding_again_changes_nothing(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    assert await ensure_admin(db_session, EMAIL, PASSWORD) is True

    assert await ensure_admin(db_session, EMAIL, "otra-clave-larga") is False
    assert (await _login(client)).status_code == 200
