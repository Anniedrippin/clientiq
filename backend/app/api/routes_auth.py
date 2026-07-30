from fastapi import APIRouter, HTTPException, status

from app.core.logging_config import get_logger, log_event, Timer
from app.core.security import create_access_token, verify_password, hash_password
from app.models.schemas import LoginRequest, LoginResponse

logger = get_logger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])

# Demo user directory. In production this lives in Postgres / your IdP.
_DEMO_USERS = {
    "analyst@clientiq.ai": {
        "password_hash": hash_password("Analyst123!"),
        "role": "analyst",
        "display_name": "Priya Analyst",
    },
    "partner@clientiq.ai": {
        "password_hash": hash_password("Partner123!"),
        "role": "partner",
        "display_name": "Daniel Partner",
    },
}


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest):
    timer = Timer()
    log_event(logger, "login_attempt_started", username=payload.username)

    user = _DEMO_USERS.get(payload.username.lower())
    if not user or not verify_password(payload.password, user["password_hash"]):
        log_event(
            logger,
            "login_attempt_failed",
            level="warning",
            username=payload.username,
            reason="bad_credentials",
            duration_ms=timer.ms(),
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    token = create_access_token(subject=payload.username.lower(), role=user["role"])
    log_event(
        logger,
        "login_attempt_completed",
        username=payload.username,
        role=user["role"],
        duration_ms=timer.ms(),
        status="success",
    )
    return LoginResponse(access_token=token, username=payload.username.lower(), role=user["role"])
