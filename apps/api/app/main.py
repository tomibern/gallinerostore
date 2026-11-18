"""Punto de entrada de la API."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.config import Settings
from app.core.db import create_engine
from app.core.storage import create_s3_client
from app.health.router import router as health_router
from app.modules.auth.login_attempts import login_attempts
from app.modules.auth.router import router as auth_router
from app.modules.catalog.router import router as catalog_router
from app.modules.events.rate_limit import limiter
from app.modules.events.router import e2e_router
from app.modules.events.router import router as events_router
from app.modules.settings.router import admin_router as admin_settings_router
from app.modules.settings.router import router as settings_router


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()  # lee del entorno

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_engine(settings.database_url)
        app.state.settings = settings
        app.state.engine = engine
        app.state.sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
        app.state.s3 = create_s3_client(settings)
        yield
        await engine.dispose()

    # Título genérico: el OpenAPI (y el cliente generado) es del núcleo, no del cliente.
    app = FastAPI(title="Catalog API", lifespan=lifespan)
    app.include_router(health_router)
    app.include_router(settings_router)
    app.include_router(catalog_router)
    app.include_router(events_router)
    app.include_router(e2e_router)
    app.include_router(auth_router)
    app.include_router(admin_settings_router)
    # El limiter es uno por proceso (slowapi lo aplica al importar el router).
    limiter.enabled = settings.rate_limit_enabled
    login_attempts.enabled = settings.rate_limit_enabled
    return app
