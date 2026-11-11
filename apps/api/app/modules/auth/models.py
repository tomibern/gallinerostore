"""El admin: único usuario con login. Los endpoints llegan con el panel (fase 4)."""

from datetime import datetime

from sqlalchemy import DateTime, Index, String, func, text
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
