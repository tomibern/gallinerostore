"""Ayudas compartidas por los tests."""

import re
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

import httpx
from fastapi import FastAPI

from app.core.config import Settings
from app.core.email import EmailMessage
from app.main import create_app


def http_client(app: FastAPI) -> httpx.AsyncClient:
    """Cliente HTTP que le habla a la app en memoria, como lo haría la web."""
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="https://test")


@asynccontextmanager
async def client_for(settings: Settings) -> AsyncIterator[httpx.AsyncClient]:
    """Levanta una app con otra configuración (por ejemplo, con una pieza rota)."""
    app = create_app(settings)
    async with app.router.lifespan_context(app), http_client(app) as client:
        yield client


class Clock:
    """La hora que ve la API en el test (fixture ``clock``); se fija o se adelanta a mano."""

    def __init__(self) -> None:
        self.now = datetime(2026, 11, 17, 12, 0, tzinfo=UTC)

    def advance(self, delta: timedelta) -> None:
        self.now += delta


@dataclass
class Inbox:
    """Bandeja en memoria: reemplaza al envío por SMTP en los tests."""

    sent: list[EmailMessage] = field(default_factory=list)

    def send(self, message: EmailMessage) -> None:
        self.sent.append(message)

    def to(self, address: str) -> list[EmailMessage]:
        return [message for message in self.sent if message.to == address]


def link_token(message: EmailMessage) -> str:
    """El token del link para elegir contraseña de un email."""
    match = re.search(r"/admin/elegir-contrasena#token=([\w-]+)", message.body)
    assert match, message.body
    return match.group(1)
