import time
import uuid

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging_config import get_logger, log_event, set_request_id, Timer
from app.core.security import decode_access_token

logger = get_logger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Assigns a request_id to every inbound HTTP request and logs
    start/completion using the same template as the rest of the app.
    This request_id is what ties an Ask-the-AI question to every
    MCP call + agent trace step shown in the Agent Trace View."""

    async def dispatch(self, request: Request, call_next):
        incoming = request.headers.get("x-request-id")
        request_id = set_request_id(incoming)
        timer = Timer()

        log_event(
            logger,
            "http_request_started",
            method=request.method,
            path=request.url.path,
        )
        try:
            response = await call_next(request)
        except Exception as exc:  # noqa: BLE001
            log_event(
                logger,
                "http_request_failed",
                level="error",
                method=request.method,
                path=request.url.path,
                error=str(exc),
                duration_ms=timer.ms(),
            )
            raise
        response.headers["x-request-id"] = request_id
        log_event(
            logger,
            "http_request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=timer.ms(),
        )
        return response


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    payload = decode_access_token(token)
    if payload is None:
        log_event(logger, "auth_guard_rejected", level="warning", reason="invalid_or_expired_token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    log_event(logger, "auth_guard_passed", user=payload.get("sub"))
    return payload
