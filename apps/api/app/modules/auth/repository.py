"""Acceso a las tablas del admin, sus sesiones y sus links para elegir contraseña."""

from datetime import datetime

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import Admin, AdminSession, PasswordToken


async def admin_by_email(session: AsyncSession, email: str) -> Admin | None:
    stmt = select(Admin).where(func.lower(Admin.email) == email.lower())
    return (await session.scalars(stmt)).one_or_none()


async def any_admin(session: AsyncSession) -> Admin | None:
    """El admin, si ya hay uno (hay un solo usuario)."""
    return (await session.scalars(select(Admin).order_by(Admin.id).limit(1))).first()


async def add_admin(session: AsyncSession, admin: Admin) -> None:
    session.add(admin)
    await session.commit()


async def add_session(session: AsyncSession, admin_session: AdminSession) -> None:
    session.add(admin_session)
    await session.commit()


async def session_by_token_hash(
    session: AsyncSession, token_hash: str
) -> tuple[AdminSession, Admin] | None:
    stmt = (
        select(AdminSession, Admin)
        .join(Admin, Admin.id == AdminSession.admin_id)
        .where(AdminSession.token_hash == token_hash)
    )
    row = (await session.execute(stmt)).one_or_none()
    return (row[0], row[1]) if row else None


async def delete_session(session: AsyncSession, admin_session_id: int) -> None:
    await session.execute(delete(AdminSession).where(AdminSession.id == admin_session_id))
    await session.commit()


async def save(session: AsyncSession) -> None:
    """Confirma los cambios hechos a filas ya cargadas (renovar una sesión, el último login)."""
    await session.commit()


async def delete_sessions(
    session: AsyncSession, admin_id: int, *, except_id: int | None = None
) -> None:
    """Corta todas las sesiones del admin (salvo, si se indica, la de este dispositivo).
    No confirma: va en la misma transacción que el cambio de contraseña."""
    stmt = delete(AdminSession).where(AdminSession.admin_id == admin_id)
    if except_id is not None:
        stmt = stmt.where(AdminSession.id != except_id)
    await session.execute(stmt)


async def add_password_token(session: AsyncSession, token: PasswordToken) -> None:
    session.add(token)
    await session.commit()


async def password_token_by_hash(
    session: AsyncSession, token_hash: str
) -> tuple[PasswordToken, Admin] | None:
    stmt = (
        select(PasswordToken, Admin)
        .join(Admin, Admin.id == PasswordToken.admin_id)
        .where(PasswordToken.token_hash == token_hash)
        .with_for_update(of=PasswordToken)
    )
    row = (await session.execute(stmt)).one_or_none()
    return (row[0], row[1]) if row else None


async def use_password_tokens(session: AsyncSession, admin_id: int, now: datetime) -> None:
    """Marca como usados todos los links pendientes del admin: después de un cambio de
    contraseña, ningún link viejo sirve. No confirma."""
    await session.execute(
        update(PasswordToken)
        .where(PasswordToken.admin_id == admin_id, PasswordToken.used_at.is_(None))
        .values(used_at=now)
    )
