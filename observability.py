import time
import uuid
from typing import Callable

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


# ---- Prometheus metrics ----
# What we watch:
# - request_total: overall traffic + error rate (by path/method/status)
# - request_latency_seconds: latency distribution (by path/method)
#
# These are the bare minimum for production:
# - RPS (rate(request_total[5m]))
# - error rate (sum(rate(request_total{status=~"5.."}[5m])) / sum(rate(request_total[5m])))
# - latency p95/p99 (histogram_quantile over request_latency_seconds)
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
    # Prefer incoming ID, otherwise generate one
    incoming = request.headers.get("x-request-id")
    return incoming if incoming else str(uuid.uuid4())


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