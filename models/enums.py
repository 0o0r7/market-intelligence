from __future__ import annotations
from enum import Enum

class Timeframe(str, Enum):
    M1 = "1m"; M5 = "5m"; M15 = "15m"; M30 = "30m"; H1 = "1h"; H4 = "4h"; D1 = "1d"; W1 = "1w"
    @classmethod
    def parse(cls, value: str) -> "Timeframe":
        v = value.strip().lower()
        for member in cls:
            if member.value == v: return member
        raise ValueError(f"Unsupported timeframe: {value!r}")

class Exchange(str, Enum):
    BINANCE = "binance"; BYBIT = "bybit"; OKX = "okx"; COINGLASS = "coinglass"

class MarketRegime(str, Enum):
    TRENDING_UP = "trending_up"; TRENDING_DOWN = "trending_down"; RANGE = "range"
    PRICE_DISCOVERY = "price_discovery"; ACCUMULATION = "accumulation"; DISTRIBUTION = "distribution"
    COMPRESSION = "compression"; EXPANSION = "expansion"

class LiquidityState(str, Enum):
    THIN = "thin"; MODERATE = "moderate"; DEEP = "deep"; IMBALANCED_BID = "imbalanced_bid"; IMBALANCED_ASK = "imbalanced_ask"

class PositioningState(str, Enum):
    EXTREME_LONG = "extreme_long"; LONG = "long"; NEUTRAL = "neutral"; SHORT = "short"; EXTREME_SHORT = "extreme_short"

class RiskLevel(str, Enum):
    LOW = "low"; MODERATE = "moderate"; ELEVATED = "elevated"; HIGH = "high"; EXTREME = "extreme"

class TrendDirection(str, Enum):
    UP = "up"; DOWN = "down"; SIDEWAYS = "sideways"

class ConfidenceTier(str, Enum):
    VERY_LOW = "very_low"; LOW = "low"; MODERATE = "moderate"; HIGH = "high"; VERY_HIGH = "very_high"