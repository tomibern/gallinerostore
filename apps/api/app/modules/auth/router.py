"""Sesión y contraseña del admin: entrar, ver quién está, salir, recuperar y cambiar la
contraseña. Sin lógica: delega en el service."""

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
from app.modules.auth.emails import Mail
from app.modules.auth.schemas import (
    AdminOut,
    LoginIn,
    PasswordChangeIn,
    PasswordResetConfirmIn,
    PasswordResetIn,
)

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


@router.post("/password-reset", status_code=status.HTTP_202_ACCEPTED, dependencies=[CsrfChecked])
async def request_password_reset(
    body: PasswordResetIn,
    session: Annotated[AsyncSession, Depends(get_session)],
    now: Now,
    mail: Mail,
) -> None:
    """«Olvidé mi contraseña». Siempre 202: no dice si el email es el del admin. Si lo es
    (y no pasó los 3 pedidos por hora), le manda un link que vence en 30 minutos."""
    await service.request_password_reset(session, body.email, now=now, mail=mail)


@router.post(
    "/password-reset/confirm",
    dependencies=[CsrfChecked],
    responses={400: {"description": "El link no existe, venció o ya se usó."}},
)
async def confirm_password_reset(
    body: PasswordResetConfirmIn,
    request: Request,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
    now: Now,
    mail: Mail,
) -> AdminOut:
    """Elige la contraseña desde el link (recuperación o invitación). Corta todas las
    sesiones, abre una en este dispositivo y pone la cookie."""
    try:
        open_session = await service.confirm_password_reset(
            session, body.token, body.password, now=now, mail=mail
        )
    except service.InvalidPasswordTokenError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="invalid_token") from error
    set_session_cookie(request, response, open_session)
    return AdminOut(email=open_session.email)


@router.put(
    "/password",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[CsrfChecked],
    responses={
        400: {"description": "La contraseña actual no es correcta."},
        401: {"description": "Sin sesión vigente."},
    },
)
async def change_password(
    body: PasswordChangeIn,
    admin: AdminAccess,
    session: Annotated[AsyncSession, Depends(get_session)],
    now: Now,
    mail: Mail,
) -> None:
    """Cambia la contraseña desde «Cuenta». Corta las demás sesiones; esta sigue."""
    try:
        await service.change_password(
            session, admin, body.current_password, body.new_password, now=now, mail=mail
        )
    except service.SessionGoneError as error:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="not_authenticated") from error
    except service.WrongPasswordError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="wrong_current_password") from error
