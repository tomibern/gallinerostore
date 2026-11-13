"""on-order products have no sizes of their own; the catalog view exposes sold_out

Un encargue se pide en cualquier talle del grupo de su categoría: no tiene filas en
``product_sizes``. La vista del catálogo público pasa a llamar «agotado»
(``sold_out``) a un producto de stock sin ningún talle disponible.

Revision ID: a3c1e5b7d902
Revises: 398992582d68
Create Date: 2026-11-13 12:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a3c1e5b7d902"
down_revision: str | Sequence[str] | None = "398992582d68"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _create_view(column: str) -> None:
    op.execute(
        f"""
        CREATE VIEW catalog_products AS
        SELECT
            p.id,
            (
                p.sale_mode = 'stock'
                AND NOT EXISTS (
                    SELECT 1 FROM product_sizes ps
                    WHERE ps.product_id = p.id AND ps.in_stock
                )
            ) AS {column}
        FROM products p
        """
    )


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        """
        DELETE FROM product_sizes ps
        USING products p
        WHERE ps.product_id = p.id AND p.sale_mode = 'on_order'
        """
    )
    op.execute("DROP VIEW catalog_products")
    _create_view("sold_out")


def downgrade() -> None:
    """Downgrade schema.

    Los talles borrados de los encargues no vuelven: el encargue sigue pidiéndose en
    cualquier talle de su grupo.
    """
    op.execute("DROP VIEW catalog_products")
    _create_view("out_of_stock")
