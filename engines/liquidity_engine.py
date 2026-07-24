from __future__ import annotations
from engines.base import BaseEngine
from models.analysis import LiquidityResult
from models.enums import LiquidityState
from models.market_data import CandleSeries, OrderBook

class LiquidityEngine(BaseEngine):
    name: str = "liquidity_engine"
    async def analyze(self, order_book: OrderBook, candles: CandleSeries) -> LiquidityResult:
        if not order_book.best_bid or not order_book.best_ask: return LiquidityResult(state=LiquidityState.THIN, spread_bps=0.0, depth_1pct_usd=0.0, depth_2pct_usd=0.0, bid_ask_imbalance=0.0, confidence=0.1)
        mid = float(order_book.mid_price); spread_bps = float(order_book.spread_bps or 0.0)
        depth_1pct_usd = 0.0; depth_2pct_usd = 0.0; bid_vol = 0.0; ask_vol = 0.0
        for b in order_book.bids:
            price = float(b.price); size = float(b.size); bid_vol += size
            if price >= mid * 0.99: depth_1pct_usd += price * size
            if price >= mid * 0.98: depth_2pct_usd += price * size
        for a in order_book.asks:
            price = float(a.price); size = float(a.size); ask_vol += size
            if price <= mid * 1.01: depth_1pct_usd += price * size
            if price <= mid * 1.02: depth_2pct_usd += price * size
        total_vol = bid_vol + ask_vol; imbalance = (bid_vol - ask_vol) / total_vol if total_vol > 0 else 0.0
        state = LiquidityState.MODERATE
        if depth_1pct_usd > 500_000: state = LiquidityState.DEEP
        elif depth_1pct_usd < 50_000: state = LiquidityState.THIN
        elif imbalance > 0.3: state = LiquidityState.IMBALANCED_BID
        elif imbalance < -0.3: state = LiquidityState.IMBALANCED_ASK
        nearest_support = max((float(b.price) for b in order_book.bids if float(b.price) >= mid * 0.98), default=None)
        nearest_resistance = min((float(a.price) for a in order_book.asks if float(a.price) <= mid * 1.02), default=None)
        return LiquidityResult(state=state, spread_bps=spread_bps, depth_1pct_usd=depth_1pct_usd, depth_2pct_usd=depth_2pct_usd, bid_ask_imbalance=float(imbalance), nearest_support=nearest_support, nearest_resistance=nearest_resistance, confidence=0.8)