"""Global error handler middleware for AppError exceptions."""

import logging

from fastapi import Request
from fastapi.responses import JSONResponse

from api.core.exceptions import AppError

logger = logging.getLogger(__name__)


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Handle AppError subclasses and return structured JSON.

    Args:
        request: The incoming request.
        exc: The AppError exception.

    Returns:
        JSONResponse with detail and code.
    """
    logger.warning(
        "AppError on %s: [%s] %s",
        request.url.path,
        exc.code,
        exc.message,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "code": exc.code},
    )
