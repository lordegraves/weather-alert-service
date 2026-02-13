from fastapi import FastAPI, HTTPException
from starlette.responses import Response
from starlette.requests import Request

import structlog

from logging_setup import configure_logging
from observability import (
    MetricsMiddleware,
    RequestIdLoggingMiddleware,
    REGISTRY,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

from weather_client import get_weather, WeatherClientError
from rate_limit import allow_request, retry_after_seconds


configure_logging()

log = structlog.get_logger("weather-service")

app = FastAPI()

app.add_middleware(RequestIdLoggingMiddleware)
app.add_middleware(MetricsMiddleware)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_host = request.client.host if request.client else "unknown"
    key = f"{client_host}:{request.url.path}"

    if not allow_request(key):
        log.warning("rate_limited", client=client_host, path=request.url.path)
        return Response(
            content='{"detail":"rate limited"}',
            media_type="application/json",
            status_code=429,
            headers={"Retry-After": str(retry_after_seconds(key))},
        )

    return await call_next(request)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    data = generate_latest(REGISTRY)
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


@app.get("/weather/{location}")
def weather(location: str):
    try:
        return get_weather(location)
    except WeatherClientError as e:
        raise HTTPException(status_code=502, detail=str(e))