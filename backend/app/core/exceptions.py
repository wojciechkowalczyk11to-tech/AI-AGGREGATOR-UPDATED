from __future__ import annotations


class JarvisBaseError(Exception):
    def __init__(self, detail: str, status_code: int) -> None:
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


class PolicyDeniedError(JarvisBaseError):
    def __init__(self, detail: str = "Policy denied request") -> None:
        super().__init__(detail=detail, status_code=403)


class ProviderError(JarvisBaseError):
    def __init__(self, detail: str = "Provider request failed") -> None:
        super().__init__(detail=detail, status_code=502)


class AllProvidersFailedError(JarvisBaseError):
    def __init__(self, detail: str = "All providers failed") -> None:
        super().__init__(detail=detail, status_code=503)


class InsufficientCreditsError(JarvisBaseError):
    def __init__(self, detail: str = "Insufficient credits") -> None:
        super().__init__(detail=detail, status_code=402)


class RateLimitExceededError(JarvisBaseError):
    def __init__(self, detail: str = "Rate limit exceeded") -> None:
        super().__init__(detail=detail, status_code=429)


class InvalidInviteCodeError(JarvisBaseError):
    def __init__(self, detail: str = "Invalid invite code") -> None:
        super().__init__(detail=detail, status_code=400)
