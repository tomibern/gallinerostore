"""Login del admin y sus sesiones (ADR 0008).

La cookie lleva un token al azar; la base guarda su hash. Una sesión común vence a las
24 horas de creada (y la cookie, al cerrar el navegador). Con «Mantener la sesión
iniciada» vence a los 30 días del último uso: cada pedido la renueva.

La contraseña se elige desde un link de un solo uso (recuperación: 30 minutos;
invitación de la cuenta inicial: 7 días) o se cambia desde «Cuenta» con la actual. Cada
cambio corta las demás sesiones y manda un aviso por email.
"""

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth import repository
from app.modules.auth.emails import PasswordMail
from app.modules.auth.login_attempts import login_attempts
from app.modules.auth.models import Admin, AdminSession, PasswordToken, PasswordTokenPurpose
from app.modules.auth.reset_requests import reset_requests

SESSION_TTL = timedelta(hours=24)
PERSISTENT_SESSION_TTL = timedelta(days=30)
PASSWORD_TOKEN_TTL = {
    PasswordTokenPurpose.RESET: timedelta(minutes=30),
    PasswordTokenPurpose.INVITATION: timedelta(days=7),
}

_hasher = PasswordHasher()
# Se verifica contra este hash cuando el email no existe, para que la respuesta tarde
# lo mismo y no revele qué emails tienen cuenta.
_DUMMY_HASH = _hasher.hash("contraseña-que-no-es-de-nadie")


class TooManyAttemptsError(Exception):
    """Esa IP o ese email gastaron sus intentos fallidos: hay que esperar."""


class InvalidPasswordTokenError(Exception):
    """El link no existe, venció o ya se usó (no se distingue cuál)."""


class SessionGoneError(Exception):
    """La sesión se cortó mientras llegaba el pedido."""


class WrongPasswordError(Exception):
    """La contraseña actual no es la del admin."""


class OtherAdminExistsError(Exception):
    """Ya hay un admin con otro email: hay un solo usuario."""


@dataclass(frozen=True)
class OpenSession:
    """Una sesión válida: de quién es, el token de la cookie y hasta cuándo dura."""

    email: str
    token: str
    persistent: bool
    expires_at: datetime


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _password_matches(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


async def create_admin(session: AsyncSession, email: str, password: str) -> None:
    """Crea el admin con su contraseña hasheada (seed, comando de la cuenta inicial y tests)."""
    await repository.add_admin(
        session, Admin(email=email.strip(), password_hash=_hasher.hash(password))
    )


async def ensure_admin(session: AsyncSession, email: str, password: str) -> bool:
    """Crea el admin si todavía no existe uno con ese email (el admin de prueba del seed de
    desarrollo). No toca uno existente. Devuelve si lo creó."""
    if await repository.admin_by_email(session, email.strip()) is not None:
        return False
    await create_admin(session, email, password)
    return True


async def log_in(
    session: AsyncSession, email: str, password: str, *, remember: bool, ip: str, now: datetime
) -> OpenSession | None:
    """Abre una sesión si el email y la contraseña son los del admin; si no, None (sin
    decir cuál de los dos falló). Tras demasiados fallos desde esa IP o para ese email,
    TooManyAttemptsError, aunque la contraseña sea correcta."""
    if login_attempts.blocked(ip, email):
        raise TooManyAttemptsError
    admin = await repository.admin_by_email(session, email.strip())
    matches = _password_matches(admin.password_hash if admin else _DUMMY_HASH, password)
    if admin is None or not matches:
        login_attempts.record_failure(ip, email)
        return None

    return await _open_session(session, admin, remember=remember, now=now)


async def _open_session(
    session: AsyncSession, admin: Admin, *, remember: bool, now: datetime
) -> OpenSession:
    """Abre una sesión nueva del admin y confirma todo lo pendiente en la transacción."""
    token = secrets.token_urlsafe(32)
    expires_at = now + (PERSISTENT_SESSION_TTL if remember else SESSION_TTL)
    admin.last_login_at = now
    await repository.add_session(
        session,
        AdminSession(
            admin_id=admin.id,
            token_hash=_token_hash(token),
            persistent=remember,
            created_at=now,
            last_seen_at=now,
            expires_at=expires_at,
        ),
    )
    return OpenSession(admin.email, token, remember, expires_at)


async def current_session(session: AsyncSession, token: str, now: datetime) -> OpenSession | None:
    """La sesión de ese token si sigue vigente (y renovada, si es persistente); si no, None.
    Una sesión vencida se borra."""
    found = await repository.session_by_token_hash(session, _token_hash(token))
    if found is None:
        return None
    admin_session, admin = found
    if admin_session.expires_at <= now:
        await repository.delete_session(session, admin_session.id)
        return None
    if admin_session.persistent:
        admin_session.last_seen_at = now
        admin_session.expires_at = now + PERSISTENT_SESSION_TTL
        await repository.save(session)
    return OpenSession(admin.email, token, admin_session.persistent, admin_session.expires_at)


async def log_out(session: AsyncSession, token: str | None) -> None:
    """Corta la sesión de ese token, si había una."""
    if not token:
        return
    found = await repository.session_by_token_hash(session, _token_hash(token))
    if found is not None:
        await repository.delete_session(session, found[0].id)


async def _send_password_link(
    session: AsyncSession,
    admin: Admin,
    purpose: PasswordTokenPurpose,
    *,
    now: datetime,
    mail: PasswordMail,
) -> None:
    token = secrets.token_urlsafe(32)
    await repository.add_password_token(
        session,
        PasswordToken(
            admin_id=admin.id,
            token_hash=_token_hash(token),
            purpose=purpose,
            created_at=now,
            expires_at=now + PASSWORD_TOKEN_TTL[purpose],
        ),
    )
    mail.send_password_link(admin.email, token, purpose)


async def request_password_reset(
    session: AsyncSession, email: str, *, now: datetime, mail: PasswordMail
) -> None:
    """«Olvidé mi contraseña»: si el email es el del admin y no pasó el límite de la hora,
    le manda un link. Para afuera la respuesta es la misma, y lo lento (mandar el email)
    pasa después de responder, así el tiempo tampoco delata si el email existe."""
    if not reset_requests.allow(email, now):
        return
    admin = await repository.admin_by_email(session, email.strip())
    if admin is not None:
        await _send_password_link(session, admin, PasswordTokenPurpose.RESET, now=now, mail=mail)


async def _set_password(session: AsyncSession, admin: Admin, password: str, now: datetime) -> None:
    """Cambia la contraseña e invalida los links pendientes. No confirma."""
    admin.password_hash = _hasher.hash(password)
    await repository.use_password_tokens(session, admin.id, now)


async def confirm_password_reset(
    session: AsyncSession, token: str, password: str, *, now: datetime, mail: PasswordMail
) -> OpenSession:
    """Elige la contraseña desde un link (recuperación o invitación): lo gasta, corta todas
    las sesiones y abre una nueva en este dispositivo. Avisa del cambio por email."""
    found = await repository.password_token_by_hash(session, _token_hash(token))
    if found is None:
        raise InvalidPasswordTokenError
    password_token, admin = found
    if password_token.used_at is not None or password_token.expires_at <= now:
        raise InvalidPasswordTokenError
    await _set_password(session, admin, password, now)
    await repository.delete_sessions(session, admin.id)
    open_session = await _open_session(session, admin, remember=False, now=now)
    mail.send_password_changed(admin.email)
    return open_session


async def change_password(
    session: AsyncSession,
    open_session: OpenSession,
    current_password: str,
    new_password: str,
    *,
    now: datetime,
    mail: PasswordMail,
) -> None:
    """Cambio desde «Cuenta» con la contraseña actual: corta las demás sesiones y deja
    viva la de este dispositivo. Avisa del cambio por email."""
    found = await repository.session_by_token_hash(session, _token_hash(open_session.token))
    if found is None:
        raise SessionGoneError
    admin_session, admin = found
    if not _password_matches(admin.password_hash, current_password):
        raise WrongPasswordError
    await _set_password(session, admin, new_password, now)
    await repository.delete_sessions(session, admin.id, except_id=admin_session.id)
    await repository.save(session)
    mail.send_password_changed(admin.email)


async def invite_admin(
    session: AsyncSession, email: str, *, now: datetime, mail: PasswordMail
) -> bool:
    """La cuenta inicial (``make admin EMAIL=…``): crea el único admin, sin contraseña
    usable, y le manda la invitación para que la elija. Si ya existe con ese email, le
    reenvía la invitación. Si existe uno con otro email, OtherAdminExistsError. Devuelve
    si lo creó."""
    email = email.strip()
    admin = await repository.any_admin(session)
    if admin is not None and admin.email.lower() != email.lower():
        raise OtherAdminExistsError(admin.email)
    created = admin is None
    if admin is None:
        # Una contraseña al azar que nadie conoce: hasta usar la invitación, no se entra.
        admin = Admin(email=email, password_hash=_hasher.hash(secrets.token_urlsafe(32)))
        await repository.add_admin(session, admin)
    await _send_password_link(session, admin, PasswordTokenPurpose.INVITATION, now=now, mail=mail)
    return created
