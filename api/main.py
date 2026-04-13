"""FastAPI application entry point.

Configures the app with CORS, lifespan management, global error handling,
middleware, and router registration.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.config import api_settings
from api.core.exceptions import AppError
from api.middleware.error_handler import app_error_handler
from api.middleware.rate_limit import RateLimitMiddleware
from api.middleware.request_id import RequestIdMiddleware
from api.routers import auth, candidates, health, jobs, recommendations, search
from api.services.redis_service import close_pool

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown lifecycle.

    Args:
        app: The FastAPI application instance.
    """
    logger.info("Starting Projet Job Intelligent API")
    logger.info("Supabase URL: %s", api_settings.supabase_url)
    yield
    logger.info("Shutting down API — closing connections")
    await close_pool()


app = FastAPI(
    title="Projet Job Intelligent",
    description=(
        "Intelligent job matching platform for data professionals. "
        "Centralizes job offers and provides AI-powered profile-to-offer matching."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ── Middleware (order matters: first added = outermost) ──────────────────────
app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    RateLimitMiddleware,
    redis_url=api_settings.redis_url,
    max_requests=100,
    window_seconds=60,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in api_settings.cors_allowed_origins.split(",")],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=3600,
)

# ── Exception handlers ──────────────────────────────────────────────────────
app.add_exception_handler(AppError, app_error_handler)


# ── Routers ──────────────────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(jobs.router)
app.include_router(candidates.router)
app.include_router(recommendations.router)
app.include_router(search.router)


# ── Global fallback exception handler ────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all exception handler returning standard JSON error.

    Args:
        request: The incoming request.
        exc: The unhandled exception.

    Returns:
        JSONResponse with error details.
    """
    logger.error("Unhandled exception on %s: %s", request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "code": "INTERNAL_ERROR"},
    )


# ── Run with uvicorn ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host=api_settings.api_host,
        port=api_settings.api_port,
        reload=api_settings.api_debug,
    )
