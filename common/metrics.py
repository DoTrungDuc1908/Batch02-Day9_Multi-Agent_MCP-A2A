"""Tiny Prometheus-style metrics for FastAPI services."""

from __future__ import annotations

import time
from collections import defaultdict
from collections.abc import Callable

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse


def add_metrics(app: FastAPI, service_name: str) -> None:
    """Add request counters, duration totals, and a /metrics endpoint."""
    counters: dict[tuple[str, str, int], int] = defaultdict(int)
    durations: dict[tuple[str, str, int], float] = defaultdict(float)

    @app.middleware("http")
    async def collect_metrics(request: Request, call_next: Callable):
        started = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - started
        route = getattr(request.scope.get("route"), "path", request.url.path)
        key = (request.method, route, response.status_code)
        counters[key] += 1
        durations[key] += elapsed
        return response

    @app.get("/metrics", response_class=PlainTextResponse)
    async def metrics() -> str:
        lines = [
            "# HELP a2a_http_requests_total Total HTTP requests.",
            "# TYPE a2a_http_requests_total counter",
        ]
        for (method, route, status), value in sorted(counters.items()):
            lines.append(
                'a2a_http_requests_total{'
                f'service="{service_name}",method="{method}",route="{route}",status="{status}"'
                f"}} {value}"
            )

        lines.extend(
            [
                "# HELP a2a_http_request_duration_seconds_total Total HTTP request duration.",
                "# TYPE a2a_http_request_duration_seconds_total counter",
            ]
        )
        for (method, route, status), value in sorted(durations.items()):
            lines.append(
                'a2a_http_request_duration_seconds_total{'
                f'service="{service_name}",method="{method}",route="{route}",status="{status}"'
                f"}} {value:.6f}"
            )
        return "\n".join(lines) + "\n"
