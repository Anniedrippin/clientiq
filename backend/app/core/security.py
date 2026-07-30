"""JWT-based authentication for ClientIQ.

Uses the same logging template as the rest of the app so every
login / token issue / token failure is auditable.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import settings
from app.core.logging_config import get_logger, log_event

logger = get_logger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str, role: str, extra_claims: Optional[dict] = None) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": subject,
        "role": role,
        "iat": now,
        "exp": expire,
        **(extra_claims or {}),
    }
    token = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    log_event(
        logger,
        "jwt_token_issued",
        user=subject,
        role=role,
        expires_at=expire.isoformat(),
    )
    return token


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        log_event(logger, "jwt_token_validated", user=payload.get("sub"), status="success")
        return payload
    except JWTError as exc:
        log_event(logger, "jwt_token_validation_failed", status="error", error=str(exc), level="warning")
        return None
