from typing import Literal

from pydantic import BaseModel

Status = Literal["ok", "error"]


class HealthChecks(BaseModel):
    database: Status
    storage: Status


class Health(BaseModel):
    status: Status
    checks: HealthChecks

    @property
    def is_healthy(self) -> bool:
        return self.status == "ok"
