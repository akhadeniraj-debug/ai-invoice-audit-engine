"""API key generation, cryptographic hashing, FastAPI authentication, and rate-limiting dependencies."""

from datetime import datetime, timezone
import hashlib
import logging
import secrets
from typing import Optional

from fastapi import Depends, HTTPException, Request, Response, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import ApiKeyRecord
from app.services.rate_limiter import rate_limiter

logger = logging.getLogger(__name__)

# Security Scheme for OpenAPI and Swagger UI documentation
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False, description="Sai Arts API key header")


def generate_raw_api_key() -> str:
    """Generates a cryptographically strong live API key formatted as sai_live_<32_random_urlsafe_bytes>."""
    random_token = secrets.token_urlsafe(32)
    return f"sai_live_{random_token}"


def hash_api_key(raw_key: str) -> str:
    """Computes SHA-256 hexadecimal digest of raw API key for secure zero-knowledge storage."""
    return hashlib.sha256(raw_key.strip().encode("utf-8")).hexdigest()


def get_key_prefix(raw_key: str) -> str:
    """Extracts first 12 characters of raw key for safe display and logging (e.g. sai_live_4aB8)."""
    return raw_key.strip()[:12]


def get_current_api_key(
    raw_key: Optional[str] = Security(API_KEY_HEADER),
    db: Session = Depends(get_db),
) -> ApiKeyRecord:
    """Authenticates incoming requests by verifying SHA-256 hash of X-API-Key header against database.

    Raises:
        HTTP 401: If header is missing or key does not exist.
        HTTP 403: If key exists but is inactive / revoked.
    """
    if not raw_key or not raw_key.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key. Please provide a valid 'X-API-Key' header.",
        )

    hashed = hash_api_key(raw_key)
    record = db.query(ApiKeyRecord).filter(ApiKeyRecord.hashed_key == hashed).first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or unknown API key.",
        )

    if not record.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key is inactive or has been revoked.",
        )

    # Update last_used_at timestamp on successful verification
    try:
        record.last_used_at = datetime.now(timezone.utc)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.warning(f"Failed to update last_used_at timestamp for key {record.key_prefix}: {e}")

    return record


async def verify_api_key_and_rate_limit(
    response: Response,
    api_key: ApiKeyRecord = Depends(get_current_api_key),
) -> ApiKeyRecord:
    """Composite FastAPI dependency: Authenticates API key and enforces Redis sliding-window rate limit.

    Injects standard headers:
      - X-RateLimit-Limit
      - X-RateLimit-Remaining
      - X-RateLimit-Window-Seconds

    Raises:
        HTTP 429: If client requests exceed rate_limit_rpm in the current sliding window.
    """
    identifier = f"api_key:{api_key.key_prefix}:{api_key.id}"
    window_sec = 60

    allowed, remaining, retry_after = await rate_limiter.check_rate_limit(
        identifier=identifier,
        limit_rpm=api_key.rate_limit_rpm,
        window_seconds=window_sec,
    )

    # Standard rate limit response headers
    response.headers["X-RateLimit-Limit"] = str(api_key.rate_limit_rpm)
    response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
    response.headers["X-RateLimit-Window-Seconds"] = str(window_sec)

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Maximum permitted is {api_key.rate_limit_rpm} requests per minute.",
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(api_key.rate_limit_rpm),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Window-Seconds": str(window_sec),
            },
        )

    return api_key
