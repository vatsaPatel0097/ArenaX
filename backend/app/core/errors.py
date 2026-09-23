from typing import Any, Dict, Optional


class AppError(Exception):
    """Base exception class for all custom application errors in ArenaX.

    All error responses across FastAPI endpoints strictly derive from this class.
    Raw HTTPException or bare Exception instances MUST NOT be raised directly in business logic.
    """

    def __init__(
        self,
        message: str,
        code: str,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class ProviderQuotaExceededError(AppError):
    """Raised when an LLM provider's rate limit or quota counter is exhausted."""

    def __init__(
        self,
        provider: str,
        reset_in_seconds: Optional[int] = None,
        message: Optional[str] = None,
    ):
        msg = message or f"Quota limit reached for provider '{provider}'."
        details = {"provider": provider}
        if reset_in_seconds is not None:
            details["reset_in_seconds"] = reset_in_seconds
        super().__init__(
            message=msg,
            code="PROVIDER_QUOTA_EXHAUSTED",
            status_code=429,
            details=details,
        )


class ProviderUnavailableError(AppError):
    """Raised when an LLM provider endpoint is offline, unreachable, or timing out."""

    def __init__(self, provider: str, message: Optional[str] = None):
        msg = message or f"LLM provider '{provider}' is currently unavailable."
        super().__init__(
            message=msg,
            code="PROVIDER_UNAVAILABLE",
            status_code=503,
            details={"provider": provider},
        )


class ModelNotFoundError(AppError):
    """Raised when a requested model ID is not registered or supported."""

    def __init__(self, model_id: str, message: Optional[str] = None):
        msg = message or f"Model '{model_id}' was not found in the model registry."
        super().__init__(
            message=msg,
            code="MODEL_NOT_FOUND",
            status_code=404,
            details={"model_id": model_id},
        )


class BattleNotFoundError(AppError):
    """Raised when a specified battle ID does not exist in the database."""

    def __init__(self, battle_id: str, message: Optional[str] = None):
        msg = message or f"Battle instance '{battle_id}' was not found."
        super().__init__(
            message=msg,
            code="BATTLE_NOT_FOUND",
            status_code=404,
            details={"battle_id": battle_id},
        )


class BattleAlreadyStreamedError(AppError):
    """Raised when an attempt is made to stream a battle that has already been streamed."""

    def __init__(self, battle_id: str, message: Optional[str] = None):
        msg = message or f"Battle instance '{battle_id}' has already been streamed."
        super().__init__(
            message=msg,
            code="BATTLE_ALREADY_STREAMED",
            status_code=400,
            details={"battle_id": battle_id},
        )


class InvalidVoteError(AppError):
    """Raised when a vote payload is invalid or the battle has already been voted on."""

    def __init__(self, reason: str, message: Optional[str] = None):
        msg = message or f"Invalid vote submission: {reason}"
        super().__init__(
            message=msg,
            code="INVALID_VOTE",
            status_code=400,
            details={"reason": reason},
        )


class AuthenticationError(AppError):
    """Raised when authentication credentials (e.g. Clerk token) are invalid or missing."""

    def __init__(self, message: str = "Authentication credentials were invalid or missing."):
        super().__init__(
            message=message,
            code="UNAUTHORIZED",
            status_code=401,
            details={},
        )
