"""Punto de entrada de la API."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.config import Settings
from app.core.db import create_engine
from app.core.storage import create_s3_client
from app.health.router import router as health_router
from app.modules.settings.router import router as store_router


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

    app = FastAPI(title=f"{settings.store_config.store.name} API", lifespan=lifespan)
    app.include_router(health_router)
    app.include_router(store_router)
    return app
