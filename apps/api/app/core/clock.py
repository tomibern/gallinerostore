"""«Ahora», como dependencia: los tests la reemplazan para fijar la hora y probar
vencimientos (y, más adelante, períodos de métricas) sin esperar."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends


def get_now() -> datetime:
    return datetime.now(UTC)


Now = Annotated[datetime, Depends(get_now)]
