from __future__ import annotations

from services.base import AuthenticationError, BackendServiceError


async def ensure_authenticated(update, context, auth_service, force_refresh=False):
    user_id = context.user_data.get("backend_user_id")
    token = context.user_data.get("access_token")
    if user_id and token and not force_refresh:
        return user_id, token
    if not update.effective_user:
        raise BackendServiceError("No user")
    result = await auth_service.register(update.effective_user.id)
    user_id, token = str(result["id"]), result["access_token"]
    context.user_data.update(
        {
            "backend_user_id": user_id,
            "access_token": token,
            "tier": result.get("subscription_tier", "basic"),
        }
    )
    return user_id, token


async def with_auth_retry(coro_factory, update, context, auth_service):
    user_id, token = await ensure_authenticated(update, context, auth_service)
    try:
        return await coro_factory(user_id, token)
    except AuthenticationError:
        user_id, token = await ensure_authenticated(update, context, auth_service, force_refresh=True)
        return await coro_factory(user_id, token)
