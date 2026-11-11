"""Registro de todos los modelos, para Alembic: importa cada módulo que tenga tablas."""

from app.core.models import Base
from app.modules.catalog import models as catalog_models

__all__ = ["Base", "catalog_models"]
