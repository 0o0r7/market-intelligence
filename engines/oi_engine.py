from __future__ import annotations
from engines.base import BaseEngine
from models.analysis import OpenInterestResult
from models.derivatives import OpenInterestSummary
from models.market_data import CandleSeries
import numpy as np
import pandas as pd

class OpenInterestEngine(BaseEngine):
    name: str = "open_interest_engine"
    async def analyze(self, oi: OpenInterestSummary, candles: CandleSeries) -> OpenInterestResult:
        change_24h = float(oi.oi_change_24h_pct); state = "flat"
        if change_24h > 2.0: state = "rising"
        elif change_24h < -2.0: state = "falling"
        price_corr = 0.0; divergence = None
        if len(oi.history) >= 10 and len(candles.candles) >= 10:
            oi_series = pd.Series(oi.history[-10:]); price_series = pd.Series([float(c.close) for c in candles.candles[-10:]])
            price_corr = float(oi_series.corr(price_series)); price_change = (price_series.iloc[-1] - price_series.iloc[0]) / price_series.iloc[0]
            if price_change > 0.01 and change_24h < -1.0: divergence = "bearish_divergence"
            elif price_change < -0.01 and change_24h > 1.0: divergence = "bullish_divergence"
        confidence = 0.6 if state != "flat" else 0.4
        if divergence: confidence = 0.8
        return OpenInterestResult(state=state, oi_change_24h_pct=change_24h, price_oi_correlation=price_corr, divergence_signal=divergence, confidence=confidence)