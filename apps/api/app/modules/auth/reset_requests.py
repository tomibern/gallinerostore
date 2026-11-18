"""Límite de pedidos de «Olvidé mi contraseña»: 3 por hora por email.

Ventana deslizante en memoria del proceso, como los otros límites (ADR 0006). Mide con el
reloj de la API (``get_now``), así los tests lo prueban sin esperar una hora. Cuenta
todos los pedidos, exista o no el email, y el que se pasa igual recibe 202: solo no sale
el email. Así el límite tampoco revela si el email tiene cuenta.
"""

from collections import defaultdict, deque
from datetime import datetime, timedelta

MAX_REQUESTS_PER_HOUR = 3
_WINDOW = timedelta(hours=1)
_MAX_TRACKED_EMAILS = 10_000


class ResetRequests:
    def __init__(self) -> None:
        self.enabled = True
        self._requests: defaultdict[str, deque[datetime]] = defaultdict(deque)

    def allow(self, email: str, now: datetime) -> bool:
        """Cuenta el pedido si entra en el cupo de la última hora y dice si entró."""
        if not self.enabled:
            return True
        if len(self._requests) > _MAX_TRACKED_EMAILS:
            self._forget_older_than(now - _WINDOW)
        recent = self._requests[email.strip().lower()]
        while recent and recent[0] <= now - _WINDOW:
            recent.popleft()
        if len(recent) >= MAX_REQUESTS_PER_HOUR:
            return False
        recent.append(now)
        return True

    def _forget_older_than(self, cutoff: datetime) -> None:
        """Saca los emails sin pedidos en la ventana: pedidos con emails inventados no
        llenan la memoria."""
        for key in [key for key, times in self._requests.items() if times[-1] <= cutoff]:
            del self._requests[key]

    def reset(self) -> None:
        self._requests.clear()


reset_requests = ResetRequests()
