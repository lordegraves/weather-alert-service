# Weather Alert Service

Production-style FastAPI service demonstrating real-world reliability
engineering patterns including caching, rate limiting, structured
logging, and metrics-driven observability.

This project demonstrates how modern backend services are hardened for
production environments.

---

## Architecture Intent

This service was built to answer a simple operational question:

> **"If this broke at 2AM, would we know why within minutes?"**

To support that goal, the service includes:

- Request-level structured logging with correlation IDs
- Prometheus metrics for service, cache, upstream dependency, and rate limiting
- Defensive upstream client behavior (timeouts, retries)
- Load protection via rate limiting
- Upstream call reduction via TTL caching

These patterns reflect safeguards commonly used in high-availability
systems.

---

## Features

### Weather Endpoint
```http
GET /weather/{location}
```
Returns normalized weather data:

- Temperature
- Conditions
- Humidity
- Wind speed


## Reliability Controls

### Caching

- TTL-based in-memory cache
- Reduces upstream dependency load
- Improves latency for repeated requests

### Rate Limiting

- Prevents request floods
- Protects both this service and the upstream API
- Provides measurable saturation signals

### Timeouts + Retries

- Avoids worker starvation
- Protects thread pool capacity
- Improves resilience to transient upstream failures

---

## Observability

### Logs

- Structured JSON output
- Correlation via `request_id`
- Request lifecycle visibility (start, end, duration, status)

### Metrics

Available at:

```http
GET /metrics
```
### Service Metrics

- `http_requests_total`
- `http_request_duration_seconds`

### Cache Metrics

- `weather_cache_hits_total`
- `weather_cache_misses_total`

### Upstream Metrics

- `weather_upstream_requests_total`
- `weather_upstream_latency_seconds`

### Rate Limiting Metrics

- `rate_limit_allowed_total`
- `rate_limit_blocked_total`

---

## Health Check

```http
GET /health
```
Intended for liveness/readiness probes and basic service validation.


## Configuration

Create a `.env` file in the repository root (**never commit this file**):

```bash
WEATHER_API_KEY=...
WEATHER_TIMEOUT_SECONDS=5

WEATHER_CACHE_TTL_SECONDS=60
WEATHER_CACHE_MAXSIZE=1024

RATE_LIMIT_REQUESTS=30
RATE_LIMIT_WINDOW_SECONDS=60
```

---

## Local Setup

```bash
cd C:\dev\weather-alert-service
.venv\Scripts\activate.bat
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

---

## Monitoring

Example configs included:

```text
monitoring/prometheus.yml
monitoring/alerts.yml
monitoring/alertmanager.yml
```

These demonstrate how the service would integrate into a production
monitoring stack.

---

## Failure Scenarios

This service is instrumented to make common production failures quickly diagnosable.

Examples:

- Upstream slowdown → visible via `weather_upstream_latency_seconds`
- Cache inefficiency → rising `weather_cache_misses_total`
- Traffic spikes → `rate_limit_blocked_total` increases
- Elevated error rates → reflected in `http_requests_total` by status code

The goal is to reduce time-to-detection and accelerate root cause analysis during incidents.

## Operational Mindset

When operating a service like this, the first questions should be:

- Are requests succeeding?
- Is latency increasing?
- Are we hitting the upstream dependency?
- Are we serving cache or making live calls?
- Are we rate limiting or being rate limited?

This project exists to make those answers measurable.
