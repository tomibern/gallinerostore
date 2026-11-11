"""La fila única de configuración de la tienda, cargada por el seed."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.settings import repository
from app.modules.settings.models import StoreSettings
from app.modules.settings.seed import apply_settings_seed, load_settings_seed
from tests.conftest import FIXTURES


async def test_seed_creates_the_single_settings_row_without_duplicating(
    db_session: AsyncSession,
) -> None:
    seed = load_settings_seed(FIXTURES / "seed.toml")
    assert seed is not None

    await apply_settings_seed(db_session, seed)
    await apply_settings_seed(db_session, seed)

    count = await db_session.scalar(select(func.count()).select_from(StoreSettings))
    assert count == 1
    settings = await repository.get_store_settings(db_session)
    assert settings is not None
    assert settings.contact_channels == {
        "whatsapp": {"number": "5491100000000"},
        "instagram": {"username": "tienda.de.prueba"},
    }
    assert settings.on_order_notice == "Demora a confirmar."
    assert settings.message_templates["stock"].startswith("Hola! Me interesa {product}")


async def test_seed_updates_the_settings_row_in_place(db_session: AsyncSession) -> None:
    seed = load_settings_seed(FIXTURES / "seed.toml")
    assert seed is not None
    await apply_settings_seed(db_session, seed)

    await apply_settings_seed(db_session, seed.model_copy(update={"on_order_notice": "Otra."}))

    settings = await repository.get_store_settings(db_session)
    assert settings is not None and settings.on_order_notice == "Otra."
