"""Pydantic schemas for API key creation, issuance, and inspection."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ApiKeyCreateRequest(BaseModel):
    """Payload to issue a new API key."""

    client_name: str = Field(..., min_length=1, max_length=255, description="Name of the client application or user")
    rate_limit_rpm: int = Field(default=60, ge=1, le=10000, description="Rate limit in requests per minute")


class ApiKeyIssueResponse(BaseModel):
    """Response returned upon API key creation containing the raw key (shown only once)."""

    id: int
    client_name: str
    key_prefix: str
    raw_key: str = Field(..., description="Raw API key. Store securely; this is shown only once.")
    is_active: bool
    rate_limit_rpm: int
    created_at: datetime


class ApiKeyItemResponse(BaseModel):
    """Metadata response for active or existing API keys (never exposes raw key or hash)."""

    id: int
    client_name: str
    key_prefix: str
    is_active: bool
    rate_limit_rpm: int
    created_at: datetime
    last_used_at: Optional[datetime] = None
