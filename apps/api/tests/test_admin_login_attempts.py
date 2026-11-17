"""Límite de intentos fallidos de login: 10 cada 15 minutos por IP y por email, así nadie
adivina la contraseña probando. Los intentos correctos no cuentan."""

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.login_attempts import MAX_FAILED_ATTEMPTS
from app.modules.auth.service import create_admin

EMAIL = "admin@tienda.test"
PASSWORD = "una-clave-larga"


async def _login(
    client: httpx.AsyncClient, ip: str, email: str = EMAIL, password: str = PASSWORD
) -> int:
    response = await client.post(
        "/admin/session",
        json={"email": email, "password": password},
        headers={"X-Requested-With": "fetch", "X-Forwarded-For": ip},
    )
    return response.status_code


async def _fail(client: httpx.AsyncClient, ip: str, email: str = EMAIL, times: int = 1) -> None:
    for _ in range(times):
        assert await _login(client, ip, email, password="no-es-esta") == 401


async def test_too_many_failures_from_an_ip_block_it_even_with_the_right_password(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    await create_admin(db_session, EMAIL, PASSWORD)
    for n in range(MAX_FAILED_ATTEMPTS):
        await _fail(client, "1.1.1.1", email=f"otro{n}@tienda.test")

    assert await _login(client, "1.1.1.1") == 429
    assert await _login(client, "2.2.2.2") == 200


async def test_too_many_failures_for_an_email_block_it_from_any_ip(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    await create_admin(db_session, EMAIL, PASSWORD)
    for n in range(MAX_FAILED_ATTEMPTS):
        await _fail(client, f"1.1.1.{n}")

    assert await _login(client, "2.2.2.2") == 429


async def test_successful_logins_do_not_count(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    await create_admin(db_session, EMAIL, PASSWORD)
    for _ in range(MAX_FAILED_ATTEMPTS + 1):
        assert await _login(client, "1.1.1.1") == 200
