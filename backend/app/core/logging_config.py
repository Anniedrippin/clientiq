"""
ClientIQ unified logging template.

Every module in this application logs through `get_logger()` + `log_event()`.
This guarantees one consistent JSON log shape everywhere: API routes, MCP
connectors, LangGraph agent nodes, vector store, LLM calls, auth, exports.

Log record shape (single line JSON):
{
  "timestamp":  "2026-07-22T10:15:32.123Z",
  "level":      "INFO",
  "service":    "clientiq-backend",
  "module":     "mcp.postgres_mcp",
  "event":      "mcp_tool_call_completed",
  "request_id": "b3f1...",           # correlates a whole user request end-to-end
  "duration_ms": 42.1,               # present on *_completed / *_failed events
  "status":     "success" | "error",
  ...extra structured fields (query, tool, rows_returned, error, etc.)
}

Usage pattern (identical everywhere):

    from app.core.logging_config import get_logger, log_event
    logger = get_logger(__name__)

    log_event(logger, "kpi_fetch_started", region="north")
    ... do work ...
    log_event(logger, "kpi_fetch_completed", duration_ms=12.3, rows=42)
"""

import logging
import sys
import json
import time
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Optional

SERVICE_NAME = "clientiq-backend"

# request_id is set once per HTTP request (see api/deps.py RequestContextMiddleware)
# and automatically stitched into every log line + every agent trace step so a
# single question can be followed end-to-end across the whole system.
_request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")


def set_request_id(request_id: Optional[str] = None) -> str:
    rid = request_id or uuid.uuid4().hex[:16]
    _request_id_ctx.set(rid)
    return rid


def get_request_id() -> str:
    return _request_id_ctx.get()


class JsonFormatter(logging.Formatter):
    """Renders every log record in the same JSON template."""

    def format(self, record: logging.LogRecord) -> str:
        base = {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "level": record.levelname,
            "service": SERVICE_NAME,
            "module": record.name,
            "request_id": getattr(record, "request_id", get_request_id()),
        }
        # Structured payload passed via log_event(...) lives in record.payload
        payload = getattr(record, "payload", None)
        if isinstance(payload, dict):
            base.update(payload)
        else:
            base["message"] = record.getMessage()

        if record.exc_info:
            base["exception"] = self.formatException(record.exc_info)

        return json.dumps(base, default=str)


def setup_logging(level: str = "INFO") -> None:
    """Call once at process start (app.main)."""
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(JsonFormatter())
    root.addHandler(console)

    file_handler = logging.FileHandler("clientiq.log")
    file_handler.setFormatter(JsonFormatter())
    root.addHandler(file_handler)

    # keep noisy third-party libs quieter but still using our formatter
    for noisy in ("uvicorn.access", "httpx", "chromadb"):
        logging.getLogger(noisy).setLevel("WARNING")


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def log_event(logger: logging.Logger, event: str, level: str = "info", **fields: Any) -> None:
    """
    THE single logging template every part of ClientIQ must use.

    Args:
        logger: module logger from get_logger(__name__)
        event:  snake_case event name, e.g. "mcp_tool_call_started"
        level:  "info" | "warning" | "error" | "debug"
        fields: any structured context (status, duration_ms, query, tool, error, ...)
    """
    payload = {"event": event, "request_id": get_request_id(), **fields}
    log_fn = getattr(logger, level.lower(), logger.info)
    log_fn(event, extra={"payload": payload, "request_id": get_request_id()})


class Timer:
    """Small helper so every '_started' / '_completed' pair reports duration_ms
    the same way across the whole codebase."""

    def __init__(self):
        self._start = time.perf_counter()

    def ms(self) -> float:
        return round((time.perf_counter() - self._start) * 1000, 2)
