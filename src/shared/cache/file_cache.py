"""
File-based debug cache for the trading system.

Replaces the previous Redis-backed cache. Each key maps to one JSON file
under CACHE_DIR, storing {"expires_at": <epoch>, "value": <value>}. Reads
past expiry are treated as a miss and the stale file is removed.

Same call contract as the old src.shared.redis.client module (set_json /
get_json) so callers did not need to change beyond the import path.
"""

import json
import time
from pathlib import Path
from typing import Any, Optional

from loguru import logger

CACHE_DIR = Path("data/cache")

# TTL for all debug keys - 48 hours
_TTL_SECONDS = 48 * 3600


def _path_for(key: str) -> Path:
    safe_name = key.replace(":", "__").replace("/", "_")
    return CACHE_DIR / f"{safe_name}.json"


def set_json(key: str, value: Any, ttl: int = _TTL_SECONDS) -> None:
    """Serialize value to JSON and store it in a per-key file."""
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        payload = {"expires_at": time.time() + ttl, "value": value}
        path = _path_for(key)
        tmp_path = path.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(payload, default=str))
        tmp_path.replace(path)
    except Exception as exc:
        logger.debug(f"File cache write failed for key {key}: {exc}")


def get_json(key: str) -> Optional[Any]:
    """Fetch and deserialize a JSON value. Returns None if missing/expired/on error."""
    path = _path_for(key)
    try:
        if not path.exists():
            return None
        payload = json.loads(path.read_text())
        if time.time() >= payload.get("expires_at", 0):
            path.unlink(missing_ok=True)
            return None
        return payload.get("value")
    except Exception as exc:
        logger.debug(f"File cache read failed for key {key}: {exc}")
        return None


def keys(pattern_prefix: str) -> list[str]:
    """
    Return original keys matching a prefix (e.g. "pairs:cycle:").

    Only prefix matching is supported - sufficient for how this cache is
    queried (scanning all pairs:cycle:* or pairs:bars:* entries).
    """
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        safe_prefix = pattern_prefix.replace(":", "__").replace("/", "_")
        matched = []
        for path in CACHE_DIR.glob(f"{safe_prefix}*.json"):
            original = path.stem.replace("__", ":")
            matched.append(original)
        return matched
    except Exception as exc:
        logger.debug(f"File cache key scan failed for prefix {pattern_prefix}: {exc}")
        return []
