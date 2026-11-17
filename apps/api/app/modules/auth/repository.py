"""Acceso a las tablas del admin y sus sesiones."""

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import Admin, AdminSession


async def admin_by_email(session: AsyncSession, email: str) -> Admin | None:
    stmt = select(Admin).where(func.lower(Admin.email) == email.lower())
    return (await session.scalars(stmt)).one_or_none()


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
