# weather-alert-service
Production-grade weather service demonstrating reliability patterns, caching, observability, and upstream resilience.

## Operational Readiness

This service is designed with production operation in mind.

**Failure Handling**
- Upstream requests use timeouts and retries to prevent thread exhaustion.
- Failures return controlled 502 responses rather than leaking exceptions.

**Traffic Protection**
- Rate limiting protects both this service and the third-party API from abuse or runaway clients.

**Performance**
- TTL caching dramatically reduces upstream dependency load and improves latency.
- Cache metrics expose hit/miss ratios for tuning.

**Observability**
- Structured logs with correlation IDs enable fast incident debugging.
- Prometheus metrics support SLO-driven alerting.
- Upstream latency is explicitly measured to detect dependency degradation.

**Predictability Under Load**
The system is designed to degrade gracefully:
- Cached responses continue serving during upstream instability.
- Rate limiting prevents resource exhaustion.
