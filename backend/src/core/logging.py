import json
import logging
import time
from collections.abc import Awaitable, Callable

from starlette.requests import Request
from starlette.responses import Response

from src.core.config import settings


class _JsonFormatter(logging.Formatter):
    # Plain text logging on Lambda still lands in CloudWatch fine, but each
    # entry is an opaque string - JSON lines let CloudWatch Logs Insights query
    # individual fields (status_code, duration_ms, path) instead of regexing
    # message text.
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "extra_fields"):
            payload.update(record.extra_fields)
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def configure_logging() -> None:
    root = logging.getLogger()
    root.setLevel(settings.log_level)

    # Lambda's runtime already attaches a handler to the root logger before
    # this ever runs - replace it rather than adding a second one, or every
    # line logs twice (once plain, once JSON).
    handler = logging.StreamHandler()
    handler.setFormatter(_JsonFormatter())
    root.handlers = [handler]


access_logger = logging.getLogger("tally.access")


async def log_requests(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 2)

    access_logger.info(
        "request",
        extra={
            "extra_fields": {
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            }
        },
    )
    return response
