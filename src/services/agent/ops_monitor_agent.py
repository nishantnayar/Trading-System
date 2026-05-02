"""
Ops Monitor Agent

Runs after each pairs trading cycle. Reads Redis cycle state and DB trade
counts, then asks a local Ollama LLM to reason over the data and flag
anomalies. Sends an email alert if anything warrants attention.

Never raises -- all errors are caught so the agent never blocks the flow.
"""

import json
from typing import Any, Dict, Optional

import ollama
from loguru import logger

from src.config.settings import get_settings
from src.shared.redis.client import get_redis

# Anomaly thresholds
_MAX_ZERO_ZSCORE_PAIRS = 1   # alert if this many pairs have |z| < 0.1
_MAX_STALE_BAR_HOURS = 3     # alert if last bar is older than this many hours
_LOW_BAR_COUNT = 20          # alert if a symbol has fewer bars than this


_SYSTEM_PROMPT = """You are an anomaly detection assistant for an algorithmic pairs trading system.

You will receive a JSON snapshot of the current cycle state. Your job is to:
1. Identify any operational anomalies that warrant human attention.
2. Return a JSON object with two fields:
   - "anomalies": a list of short strings describing each problem found (empty list if none)
   - "summary": one sentence summarising the overall cycle health

Anomalies to look for:
- Pairs with z_score near zero (|z| < 0.1) -- spread may have collapsed
- Symbols with very few bars (bar_count < 20) -- data ingestion may be failing
- Stale bar timestamps (last_bar_hours_ago > 3 during market hours)
- Cycle errors (error count > 0)
- No active pairs evaluated

Respond with valid JSON only. No explanation outside the JSON object."""


def _build_context(cycle_summary: dict) -> dict:
    """Pull Redis state and merge with cycle summary into one snapshot."""
    r = get_redis()
    pairs_state = []

    if r is not None:
        try:
            keys = r.keys("pairs:cycle:*")
            for key in keys:
                raw = r.get(key)
                if raw:
                    try:
                        pairs_state.append(json.loads(raw))
                    except Exception:
                        pass
        except Exception as exc:
            logger.debug("ops_monitor: redis scan failed: %s", exc)

    bars_state = []
    if r is not None:
        try:
            bar_keys = r.keys("pairs:bars:*")
            for key in bar_keys:
                raw = r.get(key)
                if raw:
                    try:
                        bars_state.append(json.loads(raw))
                    except Exception:
                        pass
        except Exception as exc:
            logger.debug("ops_monitor: redis bars scan failed: %s", exc)

    return {
        "cycle_summary": cycle_summary,
        "pairs_cycle_state": pairs_state,
        "bars_state": bars_state,
    }


def _call_ollama(context: dict) -> Optional[dict]:
    """Call local Ollama and return parsed JSON response."""
    settings = get_settings()
    prompt = json.dumps(context, default=str, indent=2)

    try:
        response = ollama.chat(
            model=settings.ollama_model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            options={"temperature": 0.0},
        )
        content = (response["message"]["content"] or "").strip()
        # Strip markdown code fences if model wraps output
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        return dict(json.loads(content))
    except json.JSONDecodeError as exc:
        logger.warning("ops_monitor: LLM returned non-JSON: %s", exc)
        return None
    except Exception as exc:
        logger.warning("ops_monitor: Ollama call failed: %s", exc)
        return None


async def run(cycle_summary: dict) -> Optional[dict]:
    """
    Entry point called from the Prefect task.

    Returns the agent result dict, or None if the agent was skipped/errored.
    """
    settings = get_settings()
    if not settings.agent_enabled:
        logger.debug("ops_monitor: agent disabled, skipping")
        return None

    try:
        context = _build_context(cycle_summary)
        result = _call_ollama(context)

        if result is None:
            return None

        anomalies: list = result.get("anomalies", [])
        summary: str = result.get("summary", "")

        logger.info(
            "ops_monitor: %d anomaly(s) detected. %s", len(anomalies), summary
        )

        if anomalies:
            from src.services.notification.email_notifier import get_notifier

            await get_notifier().send_ops_alert(
                anomalies=anomalies,
                summary=summary,
                cycle_summary=cycle_summary,
            )

        return result

    except Exception as exc:
        logger.warning("ops_monitor: unhandled error, skipping: %s", exc)
        return None
