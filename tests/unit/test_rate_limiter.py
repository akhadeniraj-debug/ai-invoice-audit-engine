"""Unit tests for sliding window rate limiter, Redis Lua script, and HTTP 429 responses."""

import asyncio
from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi.testclient import TestClient

from app.database.connection import init_db
from app.main import app
from app.services.rate_limiter import (
    SLIDING_WINDOW_LUA_SCRIPT,
    SlidingWindowRateLimiter,
    rate_limiter,
)


@pytest.fixture(autouse=True)
def setup_test_db():
    init_db()


@pytest.fixture
def client():
    return TestClient(app)


class TestSlidingWindowRateLimiterUnit:
    """Unit tests verifying the sliding window counter algorithm and Lua script specification."""

    def test_lua_script_contains_required_zset_commands(self):
        """Lua script must execute ZREMRANGEBYSCORE, ZCARD, ZADD, PEXPIRE, and ZRANGE."""
        script = SLIDING_WINDOW_LUA_SCRIPT
        assert "ZREMRANGEBYSCORE" in script, "Lua script missing ZREMRANGEBYSCORE"
        assert "ZCARD" in script, "Lua script missing ZCARD"
        assert "ZADD" in script, "Lua script missing ZADD"
        assert "PEXPIRE" in script, "Lua script missing PEXPIRE"
        assert "ZRANGE" in script, "Lua script missing ZRANGE"

    @pytest.mark.asyncio
    async def test_in_memory_sliding_window_allows_up_to_limit(self):
        """Sliding window must allow requests up to the specified limit and decrement remaining."""
        limiter = SlidingWindowRateLimiter(redis_url="redis://localhost:9999/0")  # forces fallback
        ident = "test_client_alpha"
        limit = 5

        for i in range(limit):
            allowed, remaining, retry_after = await limiter.check_rate_limit(ident, limit_rpm=limit, window_seconds=60)
            assert allowed is True
            assert remaining == limit - (i + 1)
            assert retry_after == 0

        # Next request must be blocked
        allowed, remaining, retry_after = await limiter.check_rate_limit(ident, limit_rpm=limit, window_seconds=60)
        assert allowed is False
        assert remaining == 0
        assert retry_after > 0

    @pytest.mark.asyncio
    async def test_redis_script_execution_mock(self):
        """Verifies that when Redis is connected, the registered Lua script is invoked with correct keys and args."""
        limiter = SlidingWindowRateLimiter()

        mock_script = AsyncMock()
        mock_script.return_value = [1, 59, 0]  # [allowed, remaining, retry_after]

        mock_client = AsyncMock()
        mock_client.register_script.return_value = mock_script

        limiter._redis_client = mock_client
        limiter._script_object = mock_script

        allowed, remaining, retry_after = await limiter.check_rate_limit(
            identifier="test_mock_key",
            limit_rpm=60,
            window_seconds=60,
        )

        assert allowed is True
        assert remaining == 59
        assert retry_after == 0

        mock_script.assert_awaited_once()
        call_kwargs = mock_script.await_args.kwargs
        assert call_kwargs["keys"] == ["ratelimit:test_mock_key"]
        assert len(call_kwargs["args"]) == 4
        assert call_kwargs["args"][1] == 60000  # window_ms
        assert call_kwargs["args"][2] == 60     # limit_rpm


class TestRateLimitingIntegrationEndpoints:
    """Tests HTTP 429 Too Many Requests enforcement on protected endpoints."""

    def test_rate_limit_exceeded_triggers_http_429(self, client: TestClient):
        """Exceeding the client's rate_limit_rpm must raise HTTP 429 with Retry-After header."""
        # 1. Issue a key with a low limit of 3 requests per minute
        issue_res = client.post(
            "/api/v1/auth/keys",
            json={"client_name": "Low Quota Client", "rate_limit_rpm": 3},
        )
        assert issue_res.status_code == 201
        raw_key = issue_res.json()["raw_key"]

        payload = {
            "unit_type": "sqft",
            "width_ft": 8,
            "height_ft": 4,
        }

        # Request 1: Allowed (remaining: 2)
        r1 = client.post("/api/v1/pricing/calculate", headers={"X-API-Key": raw_key}, json=payload)
        assert r1.status_code == 200
        assert r1.headers.get("X-RateLimit-Limit") == "3"
        assert r1.headers.get("X-RateLimit-Remaining") == "2"
        assert r1.headers.get("X-RateLimit-Window-Seconds") == "60"

        # Request 2: Allowed (remaining: 1)
        r2 = client.post("/api/v1/pricing/calculate", headers={"X-API-Key": raw_key}, json=payload)
        assert r2.status_code == 200
        assert r2.headers.get("X-RateLimit-Remaining") == "1"

        # Request 3: Allowed (remaining: 0)
        r3 = client.post("/api/v1/pricing/calculate", headers={"X-API-Key": raw_key}, json=payload)
        assert r3.status_code == 200
        assert r3.headers.get("X-RateLimit-Remaining") == "0"

        # Request 4: Blocked -> HTTP 429 Too Many Requests
        r4 = client.post("/api/v1/pricing/calculate", headers={"X-API-Key": raw_key}, json=payload)
        assert r4.status_code == 429
        assert "Rate limit exceeded" in r4.json()["detail"]
        assert "Retry-After" in r4.headers
        assert int(r4.headers["Retry-After"]) >= 1
        assert r4.headers.get("X-RateLimit-Remaining") == "0"
        assert r4.headers.get("X-RateLimit-Limit") == "3"

    def test_different_keys_have_independent_rate_limits(self, client: TestClient):
        """Rate limits are isolated per API key identity."""
        # Key A: limit 2
        k1_res = client.post("/api/v1/auth/keys", json={"client_name": "Tenant A", "rate_limit_rpm": 2})
        key_a = k1_res.json()["raw_key"]

        # Key B: limit 2
        k2_res = client.post("/api/v1/auth/keys", json={"client_name": "Tenant B", "rate_limit_rpm": 2})
        key_b = k2_res.json()["raw_key"]

        payload = {"unit_type": "letter", "letter_count": 5, "letter_height_in": 12}

        # Exhaust Tenant A's quota
        client.post("/api/v1/pricing/calculate", headers={"X-API-Key": key_a}, json=payload)
        client.post("/api/v1/pricing/calculate", headers={"X-API-Key": key_a}, json=payload)
        blocked_a = client.post("/api/v1/pricing/calculate", headers={"X-API-Key": key_a}, json=payload)
        assert blocked_a.status_code == 429

        # Tenant B should still be allowed
        allowed_b = client.post("/api/v1/pricing/calculate", headers={"X-API-Key": key_b}, json=payload)
        assert allowed_b.status_code == 200
        assert allowed_b.headers.get("X-RateLimit-Remaining") == "1"
