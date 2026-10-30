"""Sliding Window Rate Limiter using asynchronous Redis and atomic Lua scripting."""

import asyncio
from collections import defaultdict, deque
import logging
import math
import time
from typing import Optional, Tuple
import uuid

import redis.asyncio as aioredis
from redis.exceptions import RedisError

from app.config import settings

logger = logging.getLogger(__name__)

# Atomic Lua Script for Sliding Window Rate Limiting via Redis Sorted Set (ZSET)
# KEYS[1]: Rate limit key (e.g., ratelimit:{key_prefix}:{api_key_id})
# ARGV[1]: Current epoch timestamp in milliseconds (now_ms)
# ARGV[2]: Sliding window duration in milliseconds (e.g., 60000 for 1 minute)
# ARGV[3]: Maximum requests permitted in window (rate_limit_rpm)
# ARGV[4]: Unique request identifier to prevent ZSET score/member collision
SLIDING_WINDOW_LUA_SCRIPT = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
local member = ARGV[4]

local window_start = now - window

-- 1. Prune entries outside the current sliding window
redis.call('ZREMRANGEBYSCORE', key, '-inf', '(' .. window_start)

-- 2. Count requests currently within the sliding window
local current_count = redis.call('ZCARD', key)

if current_count < limit then
    -- Allowed: Add the timestamped request to ZSET
    redis.call('ZADD', key, now, member)
    -- Set TTL to sliding window length
    redis.call('PEXPIRE', key, window)
    local remaining = limit - (current_count + 1)
    return {1, remaining, 0}
else
    -- Blocked: Compute exact Retry-After by querying the oldest element in window
    local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
    local retry_after_ms = window
    if #oldest >= 2 then
        local oldest_ts = tonumber(oldest[2])
        retry_after_ms = (oldest_ts + window) - now
    end
    if retry_after_ms <= 0 then
        retry_after_ms = 1000
    end
    local retry_after_sec = math.ceil(retry_after_ms / 1000)
    return {0, 0, retry_after_sec}
end
"""


class SlidingWindowRateLimiter:
    """Production-ready asynchronous sliding window rate limiter backed by Redis.

    Uses an atomic Lua script to eliminate race conditions.
    Gracefully falls back to an in-memory sliding window if Redis is temporarily unreachable.
    """

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or settings.REDIS_URL
        self._redis_client: Optional[aioredis.Redis] = None
        self._lua_script_sha: Optional[str] = None
        self._script_object = None

        # In-memory fallback structures
        self._local_windows = defaultdict(deque)
        self._local_lock = asyncio.Lock()
        self._last_connect_failure: float = 0.0

    async def get_redis_client(self) -> Optional[aioredis.Redis]:
        """Lazily connects and returns the asynchronous Redis client."""
        # Avoid blocking repeatedly if connection recently failed
        if time.time() - self._last_connect_failure < 10.0:
            return None

        if self._redis_client is None:
            try:
                self._redis_client = aioredis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=0.3,
                    socket_timeout=0.5,
                )
                # Register Lua script
                self._script_object = self._redis_client.register_script(SLIDING_WINDOW_LUA_SCRIPT)
            except Exception as e:
                self._last_connect_failure = time.time()
                logger.warning(f"Could not connect to Redis at {self.redis_url}: {e}. Utilizing fallback.")
                self._redis_client = None
        return self._redis_client

    async def close(self) -> None:
        """Closes the active Redis connection pool."""
        if self._redis_client is not None:
            try:
                await self._redis_client.aclose()
            except Exception as e:
                logger.debug(f"Error closing Redis client: {e}")
            finally:
                self._redis_client = None

    async def check_rate_limit(
        self,
        identifier: str,
        limit_rpm: int,
        window_seconds: int = 60,
    ) -> Tuple[bool, int, int]:
        """Checks if a request is allowed under the sliding window limit.

        Args:
            identifier: Unique rate-limit identity (e.g. 'api_key:sai_live_abc123:1')
            limit_rpm: Maximum requests allowed in the window (e.g. 60)
            window_seconds: Window duration in seconds (default 60)

        Returns:
            Tuple of (is_allowed: bool, remaining_requests: int, retry_after_seconds: int)
        """
        now_ms = int(time.time() * 1000)
        window_ms = window_seconds * 1000
        redis_key = f"ratelimit:{identifier}"
        member_id = f"{now_ms}:{uuid.uuid4().hex[:8]}"

        client = await self.get_redis_client()
        if client is not None:
            try:
                if self._script_object is None:
                    self._script_object = client.register_script(SLIDING_WINDOW_LUA_SCRIPT)

                # Execute atomic Lua script
                result = await self._script_object(
                    keys=[redis_key],
                    args=[now_ms, window_ms, limit_rpm, member_id],
                )

                allowed = bool(result[0] == 1)
                remaining = int(result[1])
                retry_after = int(result[2])
                return allowed, remaining, retry_after
            except (RedisError, ConnectionError, OSError) as ex:
                self._last_connect_failure = time.time()
                logger.warning(f"Redis rate limit check failed ({ex}); utilizing in-memory sliding window fallback.")

        # In-memory fallback
        return await self._check_in_memory_fallback(redis_key, now_ms, window_ms, limit_rpm)

    async def _check_in_memory_fallback(
        self,
        key: str,
        now_ms: int,
        window_ms: int,
        limit: int,
    ) -> Tuple[bool, int, int]:
        """Thread-safe in-memory sliding window counter implementation."""
        async with self._local_lock:
            window_start = now_ms - window_ms
            q = self._local_windows[key]

            # Prune old timestamps
            while q and q[0] < window_start:
                q.popleft()

            current_count = len(q)
            if current_count < limit:
                q.append(now_ms)
                remaining = limit - (current_count + 1)
                return True, remaining, 0
            else:
                oldest_ts = q[0] if q else now_ms
                retry_after_ms = max(1000, (oldest_ts + window_ms) - now_ms)
                retry_after_sec = math.ceil(retry_after_ms / 1000)
                return False, 0, retry_after_sec


# Global rate limiter instance
rate_limiter = SlidingWindowRateLimiter()
