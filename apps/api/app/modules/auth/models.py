"""El admin (único usuario con login) y sus sesiones (ADR 0008)."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base


class Admin(Base):
    __tablename__ = "admins"
    # El email se compara sin distinguir mayúsculas.
    __table_args__ = (Index("uq_admins_email_lower", text("lower(email)"), unique=True),)

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254))
    # Hash Argon2; la contraseña nunca se guarda.
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AdminSession(Base):
    """Una sesión iniciada. La cookie lleva un token al azar; acá se guarda solo su hash,
    así una copia de la base no sirve para entrar. Borrar la fila corta la sesión."""

    __tablename__ = "admin_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    admin_id: Mapped[int] = mapped_column(ForeignKey("admins.id", ondelete="CASCADE"), index=True)
    # SHA-256 del token, en hexadecimal.
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    # «Mantener la sesión iniciada»: dura 30 días y se renueva con el uso.
    persistent: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
