"""Ayudas compartidas por los tests."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta

import httpx
from fastapi import FastAPI

from app.core.config import Settings
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
