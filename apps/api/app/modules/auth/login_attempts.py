"""Límite de intentos fallidos de login: 10 cada 15 minutos por IP y por email.

Usa el mismo almacenamiento en memoria que el límite de los eventos (``limits``, la
librería debajo de slowapi), pero cuenta solo los fallos: el admin que entra bien no gasta
cupo. Los contadores viven en el proceso, como los de los eventos (ADR 0006).
"""

from limits import RateLimitItemPerMinute
from limits.storage import MemoryStorage
from limits.strategies import FixedWindowRateLimiter

MAX_FAILED_ATTEMPTS = 10
_WINDOW = RateLimitItemPerMinute(MAX_FAILED_ATTEMPTS, 15)


class LoginAttempts:
    def __init__(self) -> None:
        self.enabled = True
        self._storage = MemoryStorage()
        self._limiter = FixedWindowRateLimiter(self._storage)

    @staticmethod
    def _keys(ip: str, email: str) -> tuple[str, str]:
        return f"login:ip:{ip}", f"login:email:{email.strip().lower()}"

    def blocked(self, ip: str, email: str) -> bool:
        """Si esa IP o ese email ya gastaron sus intentos en la ventana actual."""
        if not self.enabled:
            return False
        return not all(self._limiter.test(_WINDOW, key) for key in self._keys(ip, email))

    def record_failure(self, ip: str, email: str) -> None:
        if self.enabled:
            for key in self._keys(ip, email):
                self._limiter.hit(_WINDOW, key)

    def reset(self) -> None:
        self._storage.reset()


login_attempts = LoginAttempts()
