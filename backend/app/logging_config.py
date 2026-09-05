import logging
import time
from collections.abc import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

SENSITIVE = {"otp", "password", "token", "api_key", "authorization", "secret"}


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def sanitize_log_payload(payload: dict) -> dict:
    cleaned = {}
    for key, value in payload.items():
        if any(s in key.lower() for s in SENSITIVE):
            cleaned[key] = "[REDACTED]"
        else:
            cleaned[key] = value
    return cleaned


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        start = time.perf_counter()
        logger = logging.getLogger("weathergpt.api")
        try:
            response = await call_next(request)
        except Exception:
            latency_ms = (time.perf_counter() - start) * 1000
            logger.exception(
                "request_failed method=%s path=%s latency_ms=%.1f",
                request.method,
                request.url.path,
                latency_ms,
            )
            raise
        latency_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "request method=%s path=%s status=%s latency_ms=%.1f",
            request.method,
            request.url.path,
            response.status_code,
            latency_ms,
        )
        response.headers["X-Response-Time-ms"] = f"{latency_ms:.1f}"
        return response
