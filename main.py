from fastapi import FastAPI
from starlette.responses import Response

from observability import MetricsMiddleware, REGISTRY, generate_latest, CONTENT_TYPE_LATEST

app = FastAPI()
app.add_middleware(MetricsMiddleware)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    data = generate_latest(REGISTRY)
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)