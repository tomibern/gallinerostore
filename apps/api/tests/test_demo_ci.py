"""Test que falla a propósito para ver la CI en rojo. No se mergea."""

import httpx


async def test_demo_store_name_is_wrong_on_purpose(client: httpx.AsyncClient) -> None:
    response = await client.get("/store")

    assert response.json()["name"] == "Un nombre que no es"
