"""Los emails de la cuenta del admin: link para elegir contraseña (recuperación o
invitación) y aviso de cambio. Los textos salen del diccionario de la API."""

from typing import Annotated
from urllib.parse import quote

from fastapi import Depends, Request

from app.core.config import Settings, get_settings
from app.core.email import EmailMessage, EmailSender, get_outbox
from app.modules.auth.models import PasswordTokenPurpose

# Pantallas de la web a las que apuntan los links. El token va en el fragmento (#): el
# navegador no lo manda al servidor ni lo deja en el Referer.
CHOOSE_PASSWORD_PATH = "/admin/elegir-contrasena"
FORGOT_PASSWORD_PATH = "/admin/recuperar"

_LINK_TEXTS = {
    PasswordTokenPurpose.RESET: "email.passwordReset",
    PasswordTokenPurpose.INVITATION: "email.invitation",
}


class PasswordMail:
    def __init__(self, settings: Settings, outbox: EmailSender) -> None:
        self._texts = settings.texts
        self._store = settings.store_config.store.name
        self._site_url = settings.site_url.rstrip("/")
        self._outbox = outbox

    def _send(self, to: str, prefix: str, link: str) -> None:
        self._outbox.send(
            EmailMessage(
                to=to,
                subject=self._texts(f"{prefix}.subject", store=self._store),
                body=self._texts(f"{prefix}.body", store=self._store, link=link),
            )
        )

    def send_password_link(self, to: str, token: str, purpose: PasswordTokenPurpose) -> None:
        link = f"{self._site_url}{CHOOSE_PASSWORD_PATH}#token={quote(token)}"
        self._send(to, _LINK_TEXTS[purpose], link)

    def send_password_changed(self, to: str) -> None:
        self._send(to, "email.passwordChanged", f"{self._site_url}{FORGOT_PASSWORD_PATH}")


def get_password_mail(
    request: Request, outbox: Annotated[EmailSender, Depends(get_outbox)]
) -> PasswordMail:
    return PasswordMail(get_settings(request), outbox)


Mail = Annotated[PasswordMail, Depends(get_password_mail)]
