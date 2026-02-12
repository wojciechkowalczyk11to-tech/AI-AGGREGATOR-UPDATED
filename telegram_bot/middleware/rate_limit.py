from __future__ import annotations

import time
from collections import defaultdict

_user_requests = defaultdict(list)


def rate_limit_middleware(limit=30, window=60):
    def decorator(func):
        async def wrapper(update, context, *args, **kwargs):
            if not update.effective_user:
                return await func(update, context, *args, **kwargs)
            uid = update.effective_user.id
            now = time.time()
            _user_requests[uid] = [t for t in _user_requests[uid] if now - t < window]
            if len(_user_requests[uid]) >= limit:
                if update.message:
                    await update.message.reply_text("🚫 Szybciej się nie da!")
                return None
            _user_requests[uid].append(now)
            return await func(update, context, *args, **kwargs)

        return wrapper

    return decorator
