"""unaccent extension for the listing text search

La búsqueda del listado (``GET /products?q=``) no distingue acentos: compara
``unaccent(nombre)`` con ``unaccent(texto)``. ``unaccent`` es una extensión
confiable de PostgreSQL: la instala cualquier usuario con permiso ``CREATE`` en
la base.

Revision ID: c01cd12c30a5
Revises: a3c1e5b7d902
Create Date: 2026-11-16 12:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c01cd12c30a5"
down_revision: str | Sequence[str] | None = "a3c1e5b7d902"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")


def downgrade() -> None:
    # Sin CASCADE: si algo más llegara a depender de la extensión, la bajada falla
    # en vez de borrarlo.
    op.execute("DROP EXTENSION IF EXISTS unaccent")
