import json
import logging
import time
import uuid
from collections.abc import Callable
from contextvars import ContextVar
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

request_id_ctx: ContextVar[str | None] = ContextVar("request_id_ctx", default=None)


def get_request_id() -> str | None:
    """Get the current request ID from context."""
    return request_id_ctx.get()


class StructuredJsonFormatter(logging.Formatter):
    """Custom formatter emitting single-line JSON log events with request_id tracking."""

    def format(self, record: logging.LogRecord) -> str:
        log_record: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", None) or get_request_id(),
        }

        # Include custom extra fields if present
        for key in ("method", "path", "status_code", "duration_ms", "client_ip", "error_code"):
            if hasattr(record, key):
                log_record[key] = getattr(record, key)

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record)


logger = logging.getLogger("app.access")


class RequestIdAndLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that assigns a unique request ID, injects it into headers & context,

    and emits structured audit/access log records.
    """

    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        incoming_request_id = request.headers.get("x-request-id")
        request_id = incoming_request_id if incoming_request_id else str(uuid.uuid4())

        # Set context variables and request state
        token = request_id_ctx.set(request_id)
        request.state.request_id = request_id

        start_time = time.perf_counter()
        client_ip = request.client.host if request.client else None

        try:
            response = await call_next(request)
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

            # Ensure response has the request-id header
            response.headers["x-request-id"] = request_id

            # Emit structured access log
            log_level = logging.WARNING if response.status_code >= 400 else logging.INFO
            logger.log(
                log_level,
                f"{request.method} {request.url.path} HTTP/{request.scope.get('http_version', '1.1')} {response.status_code}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                    "client_ip": client_ip,
                },
            )
            return response

        except Exception as exc:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(
                f"Unhandled exception during {request.method} {request.url.path}: {exc}",
                exc_info=True,
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": 500,
                    "duration_ms": duration_ms,
                    "client_ip": client_ip,
                },
            )
            raise
        finally:
            request_id_ctx.reset(token)
