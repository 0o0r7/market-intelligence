from __future__ import annotations
import re
from models.enums import Timeframe
_SYMBOL_RE = re.compile(r"^[A-Z0-9]{2,20}USDT$", re.IGNORECASE)

def validate_symbol(symbol: str) -> str:
    if not symbol or not isinstance(symbol, str): raise ValueError("symbol must be a non-empty string")
    s = symbol.strip().upper()
    if not _SYMBOL_RE.match(s): raise ValueError(f"Invalid symbol: {symbol!r}. Expected format like 'BTCUSDT', 'ETHUSDT'.")
    return s

def validate_timeframe(timeframe: str) -> str: return Timeframe.parse(timeframe).value
def parse_symbol_to_base(symbol: str) -> str:
    s = validate_symbol(symbol)
    return s[:-4] if s.endswith("USDT") else s