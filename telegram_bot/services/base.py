from __future__ import annotations
import httpx
import logging
from typing import Any

logger = logging.getLogger(__name__)

class BackendServiceError(Exception):
    """Base error for backend communication."""

class AuthenticationError(BackendServiceError):
    """401 from backend."""

class RateLimitError(BackendServiceError):
    """429 from backend."""
    def __init__(self, message: str = "Rate limited", retry_after: int | None = None):
        super().__init__(message)
        self.retry_after = retry_after

class ClientError(BackendServiceError):
    """4xx (except 401, 429) from backend."""

class BackendTimeoutError(BackendServiceError):
    """Timeout connecting to backend."""

class BackendUnavailableError(BackendServiceError):
    """Cannot connect to backend."""

class AllProvidersFailedError(BackendServiceError):
    """All providers in fallback chain failed."""

class BaseService:
    def __init__(self, base_url: str, timeout: float = 60.0) -> None:
        self._client = httpx.AsyncClient(base_url=base_url, timeout=timeout)

    async def _request(self, method: str, path: str, token: str | None = None, **kwargs: Any) -> Any:
        headers = kwargs.pop("headers", {})
        if token:
            headers["Authorization"] = f"Bearer {token}"
        try:
            resp = await self._client.request(method, path, headers=headers, **kwargs)
            if resp.status_code == 401:
                raise AuthenticationError("Token expired")
            if resp.status_code == 429:
                raise RateLimitError(resp.json().get("detail", "Rate limited"))
            if resp.status_code == 402:
                raise RateLimitError("Daily cap reached")
            if 400 <= resp.status_code < 500:
                raise ClientError(str(resp.json().get("detail", "Client error")))
            resp.raise_for_status()
            return resp.json()
        except httpx.TimeoutException as exc:
            raise BackendTimeoutError("Backend timeout") from exc
        except httpx.RequestError as exc:
            raise BackendUnavailableError(f"Cannot reach backend: {exc}") from exc

    async def close(self) -> None:
        await self._client.aclose()
