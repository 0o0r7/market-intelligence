from __future__ import annotations
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

class Candle(BaseModel):
    open_time: int
    close_time: int
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    quote_volume: Decimal = Decimal("0")
    trades: int = 0
    closed: bool = True
    @field_validator("open_time", "close_time")
    @classmethod
    def _validate_ts(cls, v: int) -> int:
        if v <= 0: raise ValueError("timestamp must be positive epoch ms")
        return v

class CandleSeries(BaseModel):
    symbol: str
    exchange: str
    timeframe: str
    candles: List[Candle]
    @property
    def empty(self) -> bool: return len(self.candles) == 0
    @property
    def last_price(self) -> Optional[Decimal]: return self.candles[-1].close if self.candles else None
    def to_arrays(self) -> dict:
        if not self.candles: return {"t": [], "o": [], "h": [], "l": [], "c": [], "v": [], "qv": []}
        return {"t": [c.open_time for c in self.candles], "o": [float(c.open) for c in self.candles], "h": [float(c.high) for c in self.candles], "l": [float(c.low) for c in self.candles], "c": [float(c.close) for c in self.candles], "v": [float(c.volume) for c in self.candles], "qv": [float(c.quote_volume) for c in self.candles]}

class Trade(BaseModel):
    symbol: str; price: Decimal; size: Decimal; side: str; timestamp: int; exchange: str

class OrderBookLevel(BaseModel):
    price: Decimal; size: Decimal

class OrderBook(BaseModel):
    symbol: str; exchange: str; timestamp: int; bids: List[OrderBookLevel]; asks: List[OrderBookLevel]
    @property
    def best_bid(self) -> Optional[OrderBookLevel]: return self.bids[0] if self.bids else None
    @property
    def best_ask(self) -> Optional[OrderBookLevel]: return self.asks[0] if self.asks else None
    @property
    def mid_price(self) -> Optional[Decimal]:
        if self.best_bid and self.best_ask: return (self.best_bid.price + self.best_ask.price) / 2
        return None
    @property
    def spread_bps(self) -> Optional[float]:
        if not (self.best_bid and self.best_ask): return None
        mid = float(self.mid_price)
        if mid == 0: return None
        return (float(self.best_ask.price) - float(self.best_bid.price)) / mid * 10_000

class Ticker(BaseModel):
    symbol: str; exchange: str; last_price: Decimal; bid: Decimal; ask: Decimal; volume_24h: Decimal; quote_volume_24h: Decimal; high_24h: Decimal; low_24h: Decimal; price_change_pct_24h: Decimal; timestamp: int