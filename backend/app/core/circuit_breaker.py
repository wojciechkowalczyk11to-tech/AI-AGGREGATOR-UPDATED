from __future__ import annotations

from datetime import datetime, timedelta, timezone


class CircuitBreaker:
    _state: dict[str, dict[str, object]] = {}

    def __init__(self, name: str, failure_threshold: int = 3, recovery_timeout: int = 300) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        if name not in self._state:
            self._state[name] = {
                "failures": 0,
                "opened_at": None,
                "status": "closed",
            }

    def record_failure(self) -> None:
        data = self._state[self.name]
        failures = int(data["failures"]) + 1
        data["failures"] = failures
        if failures >= self.failure_threshold:
            data["status"] = "open"
            data["opened_at"] = datetime.now(timezone.utc)

    def record_success(self) -> None:
        data = self._state[self.name]
        data["failures"] = 0
        data["status"] = "closed"
        data["opened_at"] = None

    def is_open(self) -> bool:
        data = self._state[self.name]
        status = str(data["status"])
        if status != "open":
            return False

        opened_at = data["opened_at"]
        if isinstance(opened_at, datetime):
            if datetime.now(timezone.utc) - opened_at >= timedelta(seconds=self.recovery_timeout):
                data["status"] = "half-open"
                return False
        return True
