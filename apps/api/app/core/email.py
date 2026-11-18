"""Envío de emails por SMTP genérico (Mailpit en local; el proveedor real se elige por
variables de entorno, sin tocar código).

- ``EmailSender``: lo que manda un email. En la app es ``SmtpEmailSender``; los tests
  reemplazan la dependencia ``get_email_sender`` por una bandeja en memoria.
- ``get_outbox``: el ``EmailSender`` que usan los services en un pedido HTTP. Manda en
  segundo plano, después de responder, así la respuesta tarda lo mismo haya o no email
  (y no revela, por ejemplo, si un email tiene cuenta). La CLI usa el SMTP directo.
"""

import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage as MimeMessage
from email.utils import formataddr
from typing import Annotated, Protocol

from fastapi import BackgroundTasks, Depends, Request

from app.core.config import Settings


@dataclass(frozen=True)
class EmailMessage:
    to: str
    subject: str
    body: str


class EmailSender(Protocol):
    def send(self, message: EmailMessage) -> None: ...


class SmtpEmailSender:
    """Manda cada email en su propia conexión SMTP: son pocos y esporádicos."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        sender = settings.store_config.email
        self._from = formataddr(
            (sender.from_name or settings.store_config.store.name, sender.from_address)
        )

    def send(self, message: EmailMessage) -> None:
        settings = self._settings
        mime = MimeMessage()
        mime["From"] = self._from
        mime["To"] = message.to
        mime["Subject"] = message.subject
        mime.set_content(message.body)

        smtp_class = smtplib.SMTP_SSL if settings.smtp_security == "ssl" else smtplib.SMTP
        with smtp_class(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
            if settings.smtp_security == "starttls":
                smtp.starttls(context=ssl.create_default_context())
            if settings.smtp_username:
                smtp.login(settings.smtp_username, settings.smtp_password or "")
            smtp.send_message(mime)


class BackgroundOutbox:
    """Encola el envío para después de responder el pedido."""

    def __init__(self, background_tasks: BackgroundTasks, sender: EmailSender) -> None:
        self._background_tasks = background_tasks
        self._sender = sender

    def send(self, message: EmailMessage) -> None:
        self._background_tasks.add_task(self._sender.send, message)


def get_email_sender(request: Request) -> EmailSender:
    sender: EmailSender = request.app.state.email_sender
    return sender


def get_outbox(
    background_tasks: BackgroundTasks,
    sender: Annotated[EmailSender, Depends(get_email_sender)],
) -> EmailSender:
    return BackgroundOutbox(background_tasks, sender)
