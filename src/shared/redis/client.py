"""
Redis client singleton for the trading system.

Provides a no-op fallback when Redis is unavailable so callers never
need to guard against connection errors.
"""

import json
import logging
from typing import Any, Optional

import redis

from src.config.settings import get_settings

logger = logging.getLogger(__name__)

# TTL for all debug keys - 48 hours
_TTL_SECONDS = 48 * 3600

_client: Optional[Any] = None


def get_redis() -> Optional[Any]:
    """
    Return a shared Redis connection, or None if Redis is unreachable.

    The connection is created once and reused.  If Redis is down the first
    time this is called, every subsequent call returns None so callers
    can skip Redis writes gracefully.
    """
    global _client
    if _client is not None:
        return _client

    settings = get_settings()
    try:
        r = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        r.ping()
        _client = r
        logger.info(
            "Redis connected at %s:%s", settings.redis_host, settings.redis_port
        )
    except Exception as exc:
        logger.warning("Redis unavailable - debug caching disabled: %s", exc)
        return None

    return _client


def set_json(key: str, value: Any, ttl: int = _TTL_SECONDS) -> None:
    """Serialize value to JSON and store it in Redis.  No-op if Redis is down."""
    r = get_redis()
    if r is None:
        return
    try:
        r.setex(key, ttl, json.dumps(value))
    except Exception as exc:
        logger.debug("Redis write failed for key %s: %s", key, exc)


def get_json(key: str) -> Optional[Any]:
    """Fetch and deserialize a JSON value from Redis.  Returns None on any error."""
    r = get_redis()
    if r is None:
        return None
    try:
        raw = r.get(key)
        return json.loads(raw) if raw is not None else None
    except Exception as exc:
        logger.debug("Redis read failed for key %s: %s", key, exc)
        return None
