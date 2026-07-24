from __future__ import annotations
import numpy as np
import pandas as pd
from analytics.indicators import adx, atr, bollinger_width, rolling_zscore
from engines.base import BaseEngine
from models.analysis import RegimeResult
from models.enums import MarketRegime
from models.market_data import CandleSeries

class RegimeEngine(BaseEngine):
    name: str = "regime_engine"
    async def analyze(self, candles: CandleSeries) -> RegimeResult:
        if candles.empty: return RegimeResult(regime=MarketRegime.RANGE, adx=0.0, atr_pct=0.0, bb_width=0.0, volatility_rank=0.5, compression_score=0.5, expansion_score=0.5, confidence=0.0)
        df = pd.DataFrame([c.model_dump() for c in candles.candles])
        close = df["close"]; high = df["high"]; low = df["low"]
        adx_val = adx(high, low, close).iloc[-1]; atr_val = atr(high, low, close).iloc[-1]
        atr_pct = (atr_val / close.iloc[-1]) * 100 if close.iloc[-1] > 0 else 0.0
        bb_w = bollinger_width(close).iloc[-1]
        vol_rank = rolling_zscore(atr_pct, 100).iloc[-1]
        bb_rank = rolling_zscore(bb_w, 100).iloc[-1]
        vol_rank = 0.5 if np.isnan(vol_rank) else 1 / (1 + np.exp(-vol_rank))
        compression_score = 1.0 - (bb_rank if not np.isnan(bb_rank) else 0.5)
        expansion_score = bb_rank if not np.isnan(bb_rank) else 0.5
        lookback = min(len(close), 200)
        is_price_discovery = close.iloc[-1] >= close.iloc[-lookback:].max() or close.iloc[-1] <= close.iloc[-lookback:].min()
        regime = MarketRegime.RANGE; confidence = 0.5
        if is_price_discovery: regime = MarketRegime.PRICE_DISCOVERY; confidence = 0.9
        elif adx_val > 25:
            if close.iloc[-1] > close.iloc[-20:].mean(): regime = MarketRegime.TRENDING_UP
            else: regime = MarketRegime.TRENDING_DOWN
            confidence = min(1.0, adx_val / 50)
        elif adx_val < 20 and compression_score > 0.7: regime = MarketRegime.COMPRESSION; confidence = 0.7
        elif expansion_score > 0.7 and adx_val > 20: regime = MarketRegime.EXPANSION; confidence = 0.7
        if regime == MarketRegime.RANGE and atr_pct < 1.0:
            range_high = close.iloc[-50:].max(); range_low = close.iloc[-50:].min(); mid = (range_high + range_low) / 2
            if close.iloc[-1] < mid: regime = MarketRegime.ACCUMULATION
            else: regime = MarketRegime.DISTRIBUTION
        return RegimeResult(regime=regime, adx=float(adx_val), atr_pct=float(atr_pct), bb_width=float(bb_w), volatility_rank=float(vol_rank), compression_score=float(compression_score), expansion_score=float(expansion_score), confidence=float(confidence))