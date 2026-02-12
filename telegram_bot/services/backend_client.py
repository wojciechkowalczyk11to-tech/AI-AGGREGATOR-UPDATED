from __future__ import annotations

from typing import Any

import httpx


class BackendClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(timeout=30.0)

    async def close(self) -> None:
        await self._client.aclose()

    async def _request(
        self,
        method: str,
        path: str,
        *,
        token: str | None = None,
        json_data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        headers: dict[str, str] = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            response = await self._client.request(
                method,
                url,
                headers=headers,
                json=json_data,
                params=params,
            )
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict):
                return data
            return {"ok": True, "data": data}
        except httpx.HTTPStatusError as exc:
            try:
                payload = exc.response.json()
                if isinstance(payload, dict):
                    return {
                        "ok": False,
                        "error": payload.get("detail", "Błąd backendu"),
                        "status_code": exc.response.status_code,
                        "raw": payload,
                    }
            except ValueError:
                pass
            return {
                "ok": False,
                "error": "Błąd backendu",
                "status_code": exc.response.status_code,
            }
        except httpx.HTTPError:
            return {
                "ok": False,
                "error": "Serwer chwilowo niedostępny. Spróbuj za chwilę.",
            }
        except Exception:
            return {
                "ok": False,
                "error": "Serwer chwilowo niedostępny. Spróbuj za chwilę.",
            }

    async def register(self, telegram_id: int) -> dict[str, Any]:
        return await self._request(
            "POST", "/api/v1/auth/register", json_data={"telegram_id": telegram_id}
        )

    async def unlock(self, telegram_id: int, code: str) -> dict[str, Any]:
        return await self._request(
            "POST",
            "/api/v1/auth/unlock",
            json_data={"telegram_id": telegram_id, "code": code},
        )

    async def get_me(self, token: str) -> dict[str, Any]:
        return await self._request("GET", "/api/v1/auth/me", token=token)

    async def chat(
        self,
        token: str,
        prompt: str,
        session_id: str | None,
        provider: str | None,
        mode: str,
    ) -> dict[str, Any]:
        return await self._request(
            "POST",
            "/api/v1/chat/",
            token=token,
            json_data={
                "prompt": prompt,
                "session_id": session_id,
                "provider": provider,
                "mode": mode,
            },
        )

    async def get_usage(self, token: str, days: int) -> dict[str, Any]:
        return await self._request(
            "GET", "/api/v1/usage/summary", token=token, params={"days": days}
        )

    async def get_limits(self, token: str) -> dict[str, Any]:
        return await self._request("GET", "/api/v1/usage/limits", token=token)

    async def get_plans(self) -> list[dict[str, Any]]:
        response = await self._request("GET", "/api/v1/payments/plans")
        if isinstance(response.get("data"), list):
            return response["data"]
        if isinstance(response.get("plans"), list):
            plans = response["plans"]
            return [plan for plan in plans if isinstance(plan, dict)]
        if isinstance(response, list):
            return [plan for plan in response if isinstance(plan, dict)]
        return []

    async def create_invoice(self, token: str, plan_id: str) -> dict[str, Any]:
        return await self._request(
            "POST",
            "/api/v1/payments/invoice",
            token=token,
            json_data={"plan_id": plan_id},
        )

    async def confirm_payment(
        self, token: str, plan_id: str, stars: int, charge_id: str
    ) -> dict[str, Any]:
        return await self._request(
            "POST",
            "/api/v1/payments/confirm",
            token=token,
            json_data={"plan_id": plan_id, "stars": stars, "charge_id": charge_id},
        )

    async def get_subscription(self, token: str) -> dict[str, Any]:
        return await self._request("GET", "/api/v1/payments/subscription", token=token)
