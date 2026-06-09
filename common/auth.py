"""Optional API-key auth for local registry and A2A HTTP services."""

from __future__ import annotations

import os
from collections.abc import Callable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

API_KEY_HEADER = "X-A2A-API-Key"


def get_api_key() -> str:
    """Return the configured shared service API key, or an empty string if disabled."""
    return os.getenv("A2A_API_KEY", "").strip()


def auth_headers() -> dict[str, str]:
    """Return outbound auth headers for service-to-service calls."""
    api_key = get_api_key()
    return {API_KEY_HEADER: api_key} if api_key else {}


def add_api_key_middleware(app: FastAPI) -> None:
    """Protect a FastAPI app with optional shared API-key auth.

    Auth is disabled when A2A_API_KEY is empty. Health checks stay public so
    orchestration scripts can confirm that services have started.
    """

    @app.middleware("http")
    async def require_api_key(request: Request, call_next: Callable):
        expected = get_api_key()
        if not expected or request.url.path in {"/health", "/metrics"}:
            return await call_next(request)

        provided = request.headers.get(API_KEY_HEADER, "")
        if provided != expected:
            return JSONResponse({"detail": "Invalid or missing API key"}, status_code=401)

        return await call_next(request)
