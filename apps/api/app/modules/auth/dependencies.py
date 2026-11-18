"""Lo que comparten todos los endpoints del admin: la cookie de sesión y el header
anti-CSRF.

- ``AdminAccess``: exige una sesión vigente (si no, 401) y renueva la cookie de una
  sesión persistente.
- ``AdminWrite``: además exige el header anti-CSRF (si no, 403). Un formulario de otro
  sitio no puede mandar headers propios; con ``SameSite=Lax``, alcanza.
- ``FromAdmin``: no exige nada; dice si el pedido trae una sesión de admin vigente.
"""

from typing import Annotated, Any

from fastapi import Cookie, Depends, Header, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Now
from app.core.config import get_settings
from app.core.db import get_session
from app.modules.auth import service

SESSION_COOKIE = "admin_session"
CSRF_HEADER = "X-Requested-With"


def _cookie_options(request: Request) -> dict[str, Any]:
    """Cookie httpOnly del mismo sitio (ADR 0003), segura cuando el sitio va por HTTPS."""
    return {
        "path": "/",
        "httponly": True,
        "samesite": "lax",
        "secure": get_settings(request).site_url.startswith("https://"),
    }


def set_session_cookie(
    request: Request, response: Response, open_session: service.OpenSession
) -> None:
    """Sin «Mantener la sesión» es una cookie de sesión del navegador; con el tilde, dura lo
    mismo que la sesión."""
    response.set_cookie(
        SESSION_COOKIE,
        open_session.token,
        max_age=(
            int(service.PERSISTENT_SESSION_TTL.total_seconds()) if open_session.persistent else None
        ),
        **_cookie_options(request),
    )


def clear_session_cookie(request: Request, response: Response) -> None:
    response.delete_cookie(
        SESSION_COOKIE,
        **_cookie_options(request),
    )


def require_csrf_header(
    requested_with: Annotated[str | None, Header(alias=CSRF_HEADER)] = None,
) -> None:
    if not requested_with:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="missing_csrf_header")


async def require_admin(
    request: Request,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
    now: Now,
    token: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
) -> service.OpenSession:
    open_session = await service.current_session(session, token, now) if token else None
    if open_session is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="not_authenticated")
    if open_session.persistent:
        set_session_cookie(request, response, open_session)
    return open_session


AdminAccess = Annotated[service.OpenSession, Depends(require_admin)]


async def optional_admin(
    session: Annotated[AsyncSession, Depends(get_session)],
    now: Now,
    token: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
) -> bool:
    """Si el pedido trae una sesión de admin vigente. No exige nada: lo usan los
    endpoints públicos que tratan distinto al admin."""
    return token is not None and await service.current_session(session, token, now) is not None


FromAdmin = Annotated[bool, Depends(optional_admin)]
CsrfChecked = Depends(require_csrf_header)
