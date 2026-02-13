import time
import uuid
from typing import Callable

import structlog
from prometheus_client import (
    Counter,
    Histogram,
    REGISTRY,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


# -----------------------------
# Metrics
# -----------------------------

request_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)

request_latency_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
)


def get_request_id(request: Request) -> str:
    incoming = request.headers.get("x-request-id")
    return incoming if incoming else str(uuid.uuid4())


log = structlog.get_logger("weather-service")


# -----------------------------
# Metrics Middleware
# -----------------------------

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        start = time.perf_counter()
        response: Response | None = None
        status = "500"

        try:
            response = await call_next(request)
            status = str(response.status_code)
            return response
        finally:
            elapsed = time.perf_counter() - start
            path = request.url.path
            method = request.method

            request_total.labels(method=method, path=path, status=status).inc()
            request_latency_seconds.labels(method=method, path=path).observe(elapsed)


# -----------------------------
# Request ID + Structured Logging
# -----------------------------

class RequestIdLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        request_id = get_request_id(request)

        request.state.request_id = request_id

        start = time.perf_counter()
        response: Response | None = None
        status_code = 500

        try:
            log.info(
                "request_start",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
            )

            response = await call_next(request)
            status_code = response.status_code
            return response

        finally:
            duration_ms = (time.perf_counter() - start) * 1000.0

            log.info(
                "request_end",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status=status_code,
                duration_ms=round(duration_ms, 2),
            )

            if response is not None:
                response.headers["X-Request-Id"] = request_id