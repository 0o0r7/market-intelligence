from __future__ import annotations
import re
from datetime import datetime, timezone
_TIMEFRAME_RE = re.compile(r"^(\d+)([smhdw])$", re.IGNORECASE)
_UNIT_TO_MS = {"s": 1_000, "m": 60_000, "h": 3_600_000, "d": 86_400_000, "w": 604_800_000}

def utc_now_ms() -> int: return int(datetime.now(timezone.utc).timestamp() * 1000)
def utc_now_iso() -> str: return datetime.now(timezone.utc).isoformat()
def timeframe_to_ms(timeframe: str) -> int:
    match = _TIMEFRAME_RE.match(timeframe or "")
    if not match: raise ValueError(f"Invalid timeframe: {timeframe!r}")
    n, unit = int(match.group(1)), match.group(2).lower()
    return n * _UNIT_TO_MS[unit]
def timeframe_to_seconds(timeframe: str) -> int: return timeframe_to_ms(timeframe) // 1000