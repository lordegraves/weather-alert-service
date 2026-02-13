import os
import time
import requests
from cachetools import TTLCache
from prometheus_client import Counter, Histogram
from dotenv import load_dotenv


load_dotenv()

BASE_URL = "https://api.openweathermap.org/data/2.5/weather"


class WeatherClientError(Exception):
    pass


# -----------------------------
# Cache
# -----------------------------

cache = TTLCache(maxsize=100, ttl=300)

weather_cache_hits_total = Counter(
    "weather_cache_hits_total",
    "Total number of cache hits for /weather requests",
)

weather_cache_misses_total = Counter(
    "weather_cache_misses_total",
    "Total number of cache misses for /weather requests",
)


# -----------------------------
# Upstream Metrics
# -----------------------------

weather_upstream_requests_total = Counter(
    "weather_upstream_requests_total",
    "Total upstream OpenWeatherMap requests",
    ["status"],
)

weather_upstream_latency_seconds = Histogram(
    "weather_upstream_latency_seconds",
    "Latency of upstream OpenWeatherMap requests in seconds",
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
)


# -----------------------------
# Client
# -----------------------------

def get_weather(location: str):

    api_key = os.getenv("WEATHER_API_KEY")
    if not api_key:
        raise WeatherClientError("Missing WEATHER_API_KEY")

    timeout = float(os.getenv("WEATHER_TIMEOUT_SECONDS", "5"))

    # Normalize cache key
    cache_key = location.lower()

    # Cache hit
    if cache_key in cache:
        weather_cache_hits_total.inc()
        return cache[cache_key]

    weather_cache_misses_total.inc()

    params = {
        "q": location,
        "appid": api_key,
        "units": "metric",
    }

    attempts = 2  # 1 try + 1 retry

    for attempt in range(attempts):

        start = time.perf_counter()

        try:
            response = requests.get(
                BASE_URL,
                params=params,
                timeout=timeout,
            )

            elapsed = time.perf_counter() - start
            weather_upstream_latency_seconds.observe(elapsed)
            weather_upstream_requests_total.labels(
                status=str(response.status_code)
            ).inc()

            # Retry ONLY upstream server errors
            if response.status_code >= 500 and attempt < attempts - 1:
                time.sleep(0.2)
                continue

            break

        except requests.Timeout:
            elapsed = time.perf_counter() - start
            weather_upstream_latency_seconds.observe(elapsed)
            weather_upstream_requests_total.labels(status="timeout").inc()

            if attempt < attempts - 1:
                time.sleep(0.2)
                continue

            raise WeatherClientError("Weather API timeout")

        except requests.RequestException as e:
            elapsed = time.perf_counter() - start
            weather_upstream_latency_seconds.observe(elapsed)
            weather_upstream_requests_total.labels(
                status="request_exception"
            ).inc()

            if attempt < attempts - 1:
                time.sleep(0.2)
                continue

            raise WeatherClientError(f"Weather API request failed: {e}")

    if response.status_code != 200:
        raise WeatherClientError(
            f"Weather API returned {response.status_code}: {response.text}"
        )

    data = response.json()

    result = {
        "temperature": data["main"]["temp"],
        "conditions": data["weather"][0]["description"],
        "humidity": data["main"]["humidity"],
        "wind_speed": data["wind"]["speed"],
    }

    cache[cache_key] = result

    return result