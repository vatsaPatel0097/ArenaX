from datetime import datetime, timezone
from typing import Any, Dict
from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.errors import AppError


def get_iso_timestamp() -> str:
    """Helper to return current UTC timestamp formatted in ISO 8601."""
    return datetime.now(timezone.utc).isoformat()


def build_error_payload(code: str, message: str, details: Dict[str, Any]) -> Dict[str, Any]:
    """Helper function to construct standard JSON error payload following DRY principle."""
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details,
            "timestamp": get_iso_timestamp(),
        },
    }


def create_error_response(
    status_code: int, code: str, message: str, details: Dict[str, Any]
) -> JSONResponse:
    """Helper function to create a JSONResponse from error fields following DRY principle."""
    payload = build_error_payload(code=code, message=message, details=details)
    return JSONResponse(status_code=status_code, content=payload)


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Global exception handler for all AppError subclasses."""
    return create_error_response(
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        details=exc.details,
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Fallback exception handler for unhandled generic exceptions."""
    return create_error_response(
        status_code=500,
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected internal server error occurred.",
        details={"raw_error": str(exc)} if str(exc) else {},
    )
