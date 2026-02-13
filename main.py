from fastapi import FastAPI
from starlette.responses import Response

from logging_setup import configure_logging
from observability import (
    MetricsMiddleware,
    RequestIdLoggingMiddleware,
    REGISTRY,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

configure_logging()

app = FastAPI()
app.add_middleware(RequestIdLoggingMiddleware)
app.add_middleware(MetricsMiddleware)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    data = generate_latest(REGISTRY)
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)