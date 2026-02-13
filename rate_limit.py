import os
import time
from cachetools import TTLCache
from prometheus_client import Counter


# Requests allowed per window (per client key)
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "30"))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))

# key -> count, entries expire after window seconds
_counters = TTLCache(maxsize=10000, ttl=RATE_LIMIT_WINDOW_SECONDS)

rate_limit_allowed_total = Counter(
    "rate_limit_allowed_total",
    "Requests allowed by rate limiter",
)

rate_limit_blocked_total = Counter(
    "rate_limit_blocked_total",
    "Requests blocked by rate limiter",
)


def allow_request(client_key: str) -> bool:
    """
    Returns True if allowed, False if blocked.
    This is a simple fixed-window counter with TTL.
    Good enough for take-home; easy to reason about.
    """
    current = _counters.get(client_key, 0) + 1
    _counters[client_key] = current

    if current <= RATE_LIMIT_REQUESTS:
        rate_limit_allowed_total.inc()
        return True

    rate_limit_blocked_total.inc()
    return False


def retry_after_seconds(client_key: str) -> int:
    """
    Approximate retry-after: TTLCache doesn't expose per-key expiry directly,
    so we give a conservative value: the full window.
    """
    return RATE_LIMIT_WINDOW_SECONDS