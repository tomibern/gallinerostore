"""Base declarativa de SQLAlchemy. Los modelos de cada módulo heredan de ``Base``."""

from enum import StrEnum

from sqlalchemy import Enum, MetaData
from sqlalchemy.orm import DeclarativeBase

# Nombres de constraints estables: Alembic genera migraciones reproducibles.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def text_enum(enum_cls: type[StrEnum], name: str, length: int = 20) -> Enum:
    """Columna para un StrEnum: texto con CHECK en vez de enum nativo de Postgres,
    así sumar un valor es una migración simple. Guarda el valor, no el nombre."""
    return Enum(
        enum_cls,
        name=name,
        native_enum=False,
        create_constraint=True,
        length=length,
        values_callable=lambda e: [m.value for m in e],
    )
