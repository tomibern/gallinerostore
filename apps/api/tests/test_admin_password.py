"""Contraseña del admin: recuperarla con un link por email, cambiarla desde «Cuenta» y la
invitación de la cuenta inicial."""

from datetime import timedelta

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from app.cli import create_admin_command
from app.core.config import Settings
from app.core.email import EmailMessage
from app.modules.auth.emails import PasswordMail
from app.modules.auth.reset_requests import MAX_REQUESTS_PER_HOUR
from app.modules.auth.service import create_admin
from tests.support import Clock, Inbox, http_client, link_token

EMAIL = "admin@tienda.test"
PASSWORD = "una-clave-larga"
NEW_PASSWORD = "otra-clave-bien-larga"
ADMIN_HEADERS = {"X-Requested-With": "fetch"}


@pytest.fixture
async def admin(db_session: AsyncSession) -> None:
    await create_admin(db_session, EMAIL, PASSWORD)


async def _login(client: httpx.AsyncClient, password: str = PASSWORD) -> httpx.Response:
    body = {"email": EMAIL, "password": password, "remember": True}
    return await client.post("/admin/session", json=body, headers=ADMIN_HEADERS)


async def _request_reset(client: httpx.AsyncClient, email: str = EMAIL) -> httpx.Response:
    return await client.post("/admin/password-reset", json={"email": email}, headers=ADMIN_HEADERS)


async def _confirm(
    client: httpx.AsyncClient, token: str, password: str = NEW_PASSWORD
) -> httpx.Response:
    return await client.post(
        "/admin/password-reset/confirm",
        json={"token": token, "password": password},
        headers=ADMIN_HEADERS,
    )


async def _change(
    client: httpx.AsyncClient, current: str = PASSWORD, new: str = NEW_PASSWORD
) -> httpx.Response:
    return await client.put(
        "/admin/password",
        json={"current_password": current, "new_password": new},
        headers=ADMIN_HEADERS,
    )


def _only(messages: list[EmailMessage]) -> EmailMessage:
    assert len(messages) == 1, messages
    return messages[0]


# Recuperar la contraseña


@pytest.mark.usefixtures("admin", "clock")
async def test_the_answer_is_the_same_whether_the_email_exists_or_not(
    client: httpx.AsyncClient, inbox: Inbox
) -> None:
    known = await _request_reset(client)
    unknown = await _request_reset(client, "otro@tienda.test")

    assert known.status_code == unknown.status_code == 202
    assert known.content == unknown.content
    # Solo el admin recibe el link.
    email = _only(inbox.sent)
    assert email.to == EMAIL
    assert "Tienda de Prueba" in email.subject
    assert email.body.count("https://tienda.test/admin/elegir-contrasena#token=") == 1


@pytest.mark.usefixtures("admin", "clock")
async def test_the_link_sets_the_password_and_logs_in_on_that_device(
    client: httpx.AsyncClient, inbox: Inbox
) -> None:
    await _request_reset(client)

    response = await _confirm(client, link_token(_only(inbox.sent)))

    assert response.status_code == 200
    assert response.json() == {"email": EMAIL}
    assert (await client.get("/admin/session")).json() == {"email": EMAIL}
    assert (await _login(client, PASSWORD)).status_code == 401
    assert (await _login(client, NEW_PASSWORD)).status_code == 200


@pytest.mark.usefixtures("admin")
async def test_the_link_expires_after_30_minutes(
    client: httpx.AsyncClient, inbox: Inbox, clock: Clock
) -> None:
    await _request_reset(client)
    token = link_token(_only(inbox.sent))

    clock.advance(timedelta(minutes=30))
    response = await _confirm(client, token)

    assert response.status_code == 400
    assert response.json() == {"detail": "invalid_token"}
    assert (await _login(client, PASSWORD)).status_code == 200


@pytest.mark.usefixtures("admin")
async def test_the_link_still_works_just_before_30_minutes(
    client: httpx.AsyncClient, inbox: Inbox, clock: Clock
) -> None:
    await _request_reset(client)

    clock.advance(timedelta(minutes=29, seconds=59))

    assert (await _confirm(client, link_token(_only(inbox.sent)))).status_code == 200


@pytest.mark.usefixtures("admin", "clock")
async def test_the_link_works_only_once(client: httpx.AsyncClient, inbox: Inbox) -> None:
    await _request_reset(client)
    token = link_token(_only(inbox.sent))
    assert (await _confirm(client, token)).status_code == 200

    again = await _confirm(client, token, "una-tercera-clave")

    assert again.status_code == 400
    assert (await _login(client, NEW_PASSWORD)).status_code == 200


@pytest.mark.usefixtures("admin", "clock")
async def test_changing_the_password_voids_the_other_pending_links(
    client: httpx.AsyncClient, inbox: Inbox
) -> None:
    await _request_reset(client)
    await _request_reset(client)
    first, second = (link_token(message) for message in inbox.to(EMAIL))

    assert (await _confirm(client, second)).status_code == 200

    assert (await _confirm(client, first, "una-tercera-clave")).status_code == 400


@pytest.mark.usefixtures("clock")
async def test_an_unknown_token_is_rejected(client: httpx.AsyncClient) -> None:
    response = await _confirm(client, "no-es-un-token")

    assert response.status_code == 400


@pytest.mark.usefixtures("admin", "clock")
async def test_using_the_link_cuts_every_session_and_opens_a_new_one(
    app: FastAPI, client: httpx.AsyncClient, inbox: Inbox
) -> None:
    async with http_client(app) as phone, http_client(app) as computer:
        assert (await _login(phone)).status_code == 200
        assert (await _login(computer)).status_code == 200
        await _request_reset(client)

        assert (await _confirm(client, link_token(_only(inbox.sent)))).status_code == 200

        assert (await phone.get("/admin/session")).status_code == 401
        assert (await computer.get("/admin/session")).status_code == 401
    assert (await client.get("/admin/session")).status_code == 200


@pytest.mark.usefixtures("admin", "clock")
async def test_using_the_link_sends_a_notice(client: httpx.AsyncClient, inbox: Inbox) -> None:
    await _request_reset(client)

    await _confirm(client, link_token(_only(inbox.sent)))

    reset_link, notice = inbox.to(EMAIL)
    assert "Cambió tu contraseña" in notice.subject
    assert "https://tienda.test/admin/recuperar" in notice.body
    assert "#token=" not in notice.body


@pytest.mark.usefixtures("admin", "clock")
async def test_a_short_password_is_rejected(client: httpx.AsyncClient, inbox: Inbox) -> None:
    await _request_reset(client)
    token = link_token(_only(inbox.sent))

    response = await _confirm(client, token, "corta-123")

    assert response.status_code == 422
    # El link no se gastó: con una contraseña válida, sirve.
    assert (await _confirm(client, token, "diez-chars")).status_code == 200


@pytest.mark.usefixtures("admin", "clock")
async def test_only_three_requests_per_hour_per_email_send_a_link(
    client: httpx.AsyncClient, inbox: Inbox
) -> None:
    responses = [await _request_reset(client) for _ in range(MAX_REQUESTS_PER_HOUR + 1)]

    # El que se pasa del límite recibe lo mismo, pero no sale el email.
    assert [r.status_code for r in responses] == [202] * (MAX_REQUESTS_PER_HOUR + 1)
    assert len(inbox.to(EMAIL)) == MAX_REQUESTS_PER_HOUR
    # El límite es por email: el formato no lo saltea.
    await _request_reset(client, "  ADMIN@tienda.test ")
    assert len(inbox.to(EMAIL)) == MAX_REQUESTS_PER_HOUR


@pytest.mark.usefixtures("admin")
async def test_the_quota_comes_back_an_hour_after_each_request(
    client: httpx.AsyncClient, inbox: Inbox, clock: Clock
) -> None:
    for _ in range(MAX_REQUESTS_PER_HOUR):
        await _request_reset(client)
        clock.advance(timedelta(minutes=10))

    # 30 minutos después del primero, todavía no hay cupo.
    await _request_reset(client)
    assert len(inbox.to(EMAIL)) == MAX_REQUESTS_PER_HOUR

    # A la hora del primero se libera uno (ventana deslizante, no por hora de reloj).
    clock.advance(timedelta(minutes=30))
    await _request_reset(client)
    await _request_reset(client)
    assert len(inbox.to(EMAIL)) == MAX_REQUESTS_PER_HOUR + 1


@pytest.mark.usefixtures("admin", "clock")
async def test_requesting_a_reset_needs_the_csrf_header(
    client: httpx.AsyncClient, inbox: Inbox
) -> None:
    response = await client.post("/admin/password-reset", json={"email": EMAIL})

    assert response.status_code == 403
    assert inbox.sent == []


# Cambiar la contraseña desde «Cuenta»


@pytest.mark.usefixtures("admin", "clock")
async def test_the_admin_changes_the_password_from_the_account(
    app: FastAPI, client: httpx.AsyncClient, inbox: Inbox
) -> None:
    async with http_client(app) as phone:
        await _login(phone)
        await _login(client)

        response = await _change(client)

        assert response.status_code == 204
        # Esta sesión sigue; la del otro dispositivo, no.
        assert (await client.get("/admin/session")).status_code == 200
        assert (await phone.get("/admin/session")).status_code == 401
    assert (await _login(client, NEW_PASSWORD)).status_code == 200
    assert "Cambió tu contraseña" in _only(inbox.to(EMAIL)).subject


@pytest.mark.usefixtures("admin", "clock")
async def test_a_wrong_current_password_is_rejected(
    client: httpx.AsyncClient, inbox: Inbox
) -> None:
    await _login(client)

    response = await _change(client, current="no-es-la-actual")

    assert response.status_code == 400
    assert response.json() == {"detail": "wrong_current_password"}
    assert (await _login(client, PASSWORD)).status_code == 200
    assert inbox.sent == []


@pytest.mark.usefixtures("admin", "clock")
async def test_a_short_new_password_is_rejected_from_the_account(
    client: httpx.AsyncClient,
) -> None:
    await _login(client)

    response = await _change(client, new="corta")

    assert response.status_code == 422
    assert (await _login(client, PASSWORD)).status_code == 200


@pytest.mark.usefixtures("admin")
async def test_changing_the_password_needs_a_session_and_the_csrf_header(
    client: httpx.AsyncClient,
) -> None:
    assert (await _change(client)).status_code == 401
    await _login(client)
    response = await client.put(
        "/admin/password", json={"current_password": PASSWORD, "new_password": NEW_PASSWORD}
    )
    assert response.status_code == 403


# La cuenta inicial (`make admin EMAIL=…`)


@pytest.fixture
def mail(settings: Settings) -> tuple[PasswordMail, Inbox]:
    """Lo que usa el comando: los emails salen directo, acá a una bandeja en memoria."""
    inbox = Inbox()
    return PasswordMail(settings, inbox), inbox


async def _command(
    db_session: AsyncSession, email: str, clock: Clock, mail: tuple[PasswordMail, Inbox]
) -> int:
    return await create_admin_command(db_session, email, mail=mail[0], now=clock.now)


async def test_the_command_creates_the_admin_with_an_invitation_valid_for_7_days(
    client: httpx.AsyncClient,
    db_session: AsyncSession,
    clock: Clock,
    mail: tuple[PasswordMail, Inbox],
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = await _command(db_session, EMAIL, clock, mail)

    assert exit_code == 0
    assert "creado" in capsys.readouterr().out
    invitation = _only(mail[1].sent)
    assert invitation.to == EMAIL
    assert "7 días" in invitation.body
    # Hasta elegir la contraseña, no se entra con ninguna.
    assert (await _login(client, PASSWORD)).status_code == 401
    clock.advance(timedelta(days=6, hours=23))
    assert (await _confirm(client, link_token(invitation))).status_code == 200
    assert (await _login(client, NEW_PASSWORD)).status_code == 200


async def test_the_invitation_expires_after_7_days(
    client: httpx.AsyncClient,
    db_session: AsyncSession,
    clock: Clock,
    mail: tuple[PasswordMail, Inbox],
) -> None:
    await _command(db_session, EMAIL, clock, mail)

    clock.advance(timedelta(days=7))

    assert (await _confirm(client, link_token(_only(mail[1].sent)))).status_code == 400


async def test_the_command_resends_the_invitation_to_the_same_email(
    client: httpx.AsyncClient,
    db_session: AsyncSession,
    clock: Clock,
    mail: tuple[PasswordMail, Inbox],
    capsys: pytest.CaptureFixture[str],
) -> None:
    await _command(db_session, EMAIL, clock, mail)
    capsys.readouterr()

    exit_code = await _command(db_session, " Admin@Tienda.test", clock, mail)

    assert exit_code == 0
    assert "ya existía" in capsys.readouterr().out
    first, second = mail[1].to(EMAIL)
    assert link_token(first) != link_token(second)
    assert (await _confirm(client, link_token(second))).status_code == 200


async def test_the_command_fails_if_there_is_an_admin_with_another_email(
    db_session: AsyncSession,
    clock: Clock,
    mail: tuple[PasswordMail, Inbox],
    capsys: pytest.CaptureFixture[str],
) -> None:
    await create_admin(db_session, EMAIL, PASSWORD)

    exit_code = await _command(db_session, "otro@tienda.test", clock, mail)

    assert exit_code == 1
    error = capsys.readouterr().err
    assert EMAIL in error
    assert "hay un solo usuario" in error
    assert mail[1].sent == []
