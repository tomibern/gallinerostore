"""Entrada y salida de los endpoints de sesión y contraseña del admin."""

from pydantic import BaseModel, Field


class LoginIn(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(max_length=200)
    remember: bool = Field(
        default=False,
        description="«Mantener la sesión iniciada»: 30 días renovables en vez de hasta "
        "cerrar el navegador.",
    )


class AdminOut(BaseModel):
    email: str


# Mínimo de 10 caracteres, sin reglas de composición (spec #57).
MIN_PASSWORD_LENGTH = 10
NewPassword = Field(min_length=MIN_PASSWORD_LENGTH, max_length=200)


class PasswordResetIn(BaseModel):
    email: str = Field(max_length=254)


class PasswordResetConfirmIn(BaseModel):
    token: str = Field(max_length=200, description="El token del link del email.")
    password: str = NewPassword


class PasswordChangeIn(BaseModel):
    current_password: str = Field(max_length=200)
    new_password: str = NewPassword
