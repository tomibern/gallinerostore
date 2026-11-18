"""password tokens

Links para elegir contraseña: «Olvidé mi contraseña» (vence en 30 minutos) y la
invitación de la cuenta inicial (vence en 7 días). Se guarda el hash del token, nunca
el token.

Revision ID: 7d4a9c2e1f63
Revises: 5b2e8f0c4a71
Create Date: 2026-11-18 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7d4a9c2e1f63"
down_revision: str | Sequence[str] | None = "5b2e8f0c4a71"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "password_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("admin_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "purpose",
            sa.Enum(
                "reset",
                "invitation",
                name="password_token_purpose",
                native_enum=False,
                create_constraint=True,
                length=20,
            ),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["admin_id"],
            ["admins.id"],
            name=op.f("fk_password_tokens_admin_id_admins"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_password_tokens")),
        sa.UniqueConstraint("token_hash", name=op.f("uq_password_tokens_token_hash")),
    )
    op.create_index(
        op.f("ix_password_tokens_admin_id"), "password_tokens", ["admin_id"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_password_tokens_admin_id"), table_name="password_tokens")
    op.drop_table("password_tokens")
