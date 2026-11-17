"""Entrada y salida de los endpoints de sesión del admin."""

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
