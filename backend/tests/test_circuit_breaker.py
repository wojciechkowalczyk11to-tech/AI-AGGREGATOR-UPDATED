from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.core.circuit_breaker import CircuitBreaker


def test_circuit_opens_after_failures() -> None:
    breaker = CircuitBreaker("provider-a", failure_threshold=3, recovery_timeout=60)
    breaker.record_failure()
    breaker.record_failure()
    breaker.record_failure()

    assert breaker.is_open() is True


def test_circuit_recovers_after_timeout() -> None:
    breaker = CircuitBreaker("provider-b", failure_threshold=1, recovery_timeout=1)
    breaker.record_failure()
    CircuitBreaker._state["provider-b"]["opened_at"] = datetime.now(timezone.utc) - timedelta(seconds=2)

    assert breaker.is_open() is False


def test_circuit_half_open_success_closes() -> None:
    breaker = CircuitBreaker("provider-c", failure_threshold=1, recovery_timeout=1)
    breaker.record_failure()
    CircuitBreaker._state["provider-c"]["opened_at"] = datetime.now(timezone.utc) - timedelta(seconds=2)

    assert breaker.is_open() is False
    breaker.record_success()
    assert breaker.is_open() is False
