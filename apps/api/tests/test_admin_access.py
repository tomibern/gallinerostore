"""Todo endpoint del admin exige sesión. Recorre el OpenAPI, así cada endpoint nuevo
bajo /admin queda cubierto sin escribir otro test."""

import httpx
import pytest

from app.core.config import Settings
from app.main import create_app

# Los únicos endpoints del admin que se usan sin sesión: entrar, salir y recuperar la
# contraseña.
PUBLIC = {
    ("POST", "/admin/session"),
    ("DELETE", "/admin/session"),
    ("POST", "/admin/password-reset"),
    ("POST", "/admin/password-reset/confirm"),
}


def _admin_operations() -> list[tuple[str, str]]:
    # Construir la app no la levanta ni se conecta a nada: alcanza para leer sus rutas.
    # Se arma en la colección, sin el entorno de los tests.
    paths = create_app(Settings.model_construct()).openapi()["paths"]
    return sorted(
        (method.upper(), path)
        for path, operations in paths.items()
        if path.startswith("/admin/")
        for method in operations
        if (method.upper(), path) not in PUBLIC
    )


def test_there_are_admin_endpoints_to_check() -> None:
    assert ("GET", "/admin/session") in _admin_operations()


@pytest.mark.parametrize(("method", "path"), _admin_operations())
async def test_admin_endpoints_need_a_session(
    client: httpx.AsyncClient, method: str, path: str
) -> None:
    # Los parámetros de ruta llevan un valor cualquiera: el 401 llega antes de buscarlo.
    url = path.replace("{", "").replace("}", "")
    response = await client.request(method, url, headers={"X-Requested-With": "fetch"})

    assert response.status_code == 401
