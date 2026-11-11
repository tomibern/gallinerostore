import httpx


async def test_store_exposes_public_configuration(client: httpx.AsyncClient) -> None:
    response = await client.get("/store")

    assert response.status_code == 200
    assert response.json() == {
        "name": "Tienda de Prueba",
        "locale": "es-AR",
        "currency": "USD",
        "price_decimals": 2,
        "collection_label": "Marca",
        "features": {
            "collections": True,
            "versions": False,
            "on_order": True,
            "instagram": False,
            "metrics": True,
            "product_story": False,
        },
    }
