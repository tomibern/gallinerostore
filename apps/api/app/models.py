"""Registro de todos los modelos, para Alembic: importa cada módulo que tenga tablas."""

from app.core.models import Base
from app.modules.auth import models as auth_models
from app.modules.catalog import models as catalog_models
from app.modules.events import models as events_models
from app.modules.settings import models as settings_models

__all__ = ["Base", "auth_models", "catalog_models", "events_models", "settings_models"]
