import httpx

from app.core.config import Settings
from app.main import create_app


async def _get_health(settings: Settings) -> httpx.Response:
    app = create_app(settings)
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            return await c.get("/health")


async def test_health_reports_database_and_storage_ok(client: httpx.AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "checks": {"database": "ok", "storage": "ok"},
    }


async def test_health_fails_clearly_when_database_is_unreachable(settings: Settings) -> None:
    broken = settings.model_copy(
        update={"database_url": "postgresql+asyncpg://nobody:nothing@localhost:1/none"}
    )

    response = await _get_health(broken)

    assert response.status_code == 503
    assert response.json() == {
        "status": "error",
        "checks": {"database": "error", "storage": "ok"},
    }


async def test_health_fails_clearly_when_storage_is_unreachable(settings: Settings) -> None:
    broken = settings.model_copy(update={"s3_endpoint_url": "http://localhost:1"})

    response = await _get_health(broken)

    assert response.status_code == 503
    assert response.json() == {
        "status": "error",
        "checks": {"database": "ok", "storage": "error"},
    }
