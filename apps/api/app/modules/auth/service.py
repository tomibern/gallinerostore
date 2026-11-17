"""Login del admin y sus sesiones (ADR 0008).

La cookie lleva un token al azar; la base guarda su hash. Una sesión común vence a las
24 horas de creada (y la cookie, al cerrar el navegador). Con «Mantener la sesión
iniciada» vence a los 30 días del último uso: cada pedido la renueva.
"""

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth import repository
from app.modules.auth.login_attempts import login_attempts
from app.modules.auth.models import Admin, AdminSession

SESSION_TTL = timedelta(hours=24)
PERSISTENT_SESSION_TTL = timedelta(days=30)

_hasher = PasswordHasher()
# Se verifica contra este hash cuando el email no existe, para que la respuesta tarde
# lo mismo y no revele qué emails tienen cuenta.
_DUMMY_HASH = _hasher.hash("contraseña-que-no-es-de-nadie")


class TooManyAttemptsError(Exception):
    """Esa IP o ese email gastaron sus intentos fallidos: hay que esperar."""


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
