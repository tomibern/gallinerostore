"""Sesión del admin: entrar, ver quién está y salir. Sin lógica: delega en el service."""

from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.client_ip import client_ip
from app.core.clock import Now
from app.core.db import get_session
from app.modules.auth import service
from app.modules.auth.dependencies import (
    SESSION_COOKIE,
    AdminAccess,
    CsrfChecked,
    clear_session_cookie,
    set_session_cookie,
)
from app.modules.auth.schemas import AdminOut, LoginIn

router = APIRouter(prefix="/admin", tags=["admin-auth"])


@router.post(
    "/session",
    dependencies=[CsrfChecked],
    responses={
        401: {"description": "Email o contraseña incorrectos."},
        429: {"description": "Demasiados intentos fallidos: hay que esperar 15 minutos."},
    },
)
async def log_in(
    body: LoginIn,
    request: Request,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
    now: Now,
) -> AdminOut:
    """Abre una sesión y pone la cookie. El error no dice si falló el email o la contraseña."""
    try:
        open_session = await service.log_in(
            session,
            body.email,
            body.password,
            remember=body.remember,
            ip=client_ip(request),
            now=now,
        )
    except service.TooManyAttemptsError as error:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, detail="too_many_attempts"
        ) from error
    if open_session is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials")
    set_session_cookie(request, response, open_session)
    return AdminOut(email=open_session.email)


@router.get("/session", responses={401: {"description": "Sin sesión vigente."}})
async def current_admin(admin: AdminAccess) -> AdminOut:
    """El admin de la sesión actual."""
    return AdminOut(email=admin.email)


@router.delete("/session", status_code=status.HTTP_204_NO_CONTENT, dependencies=[CsrfChecked])
async def log_out(
    request: Request,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
    token: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
) -> None:
    """Corta la sesión (si había) y borra la cookie."""
    await service.log_out(session, token)
    clear_session_cookie(request, response)
