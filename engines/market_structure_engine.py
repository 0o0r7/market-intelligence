from __future__ import annotations
from typing import List, Tuple
import numpy as np
import pandas as pd
from engines.base import BaseEngine
from models.analysis import MarketStructureResult, SwingPoint
from models.enums import TrendDirection
from models.market_data import CandleSeries

class MarketStructureEngine(BaseEngine):
    name: str = "market_structure_engine"
    def __init__(self, lookback: int = 2): self.lookback = lookback

    async def analyze(self, candles: CandleSeries) -> MarketStructureResult:
        if candles.empty or len(candles.candles) < self.lookback * 2 + 1: return MarketStructureResult(trend=TrendDirection.SIDEWAYS)
        df = pd.DataFrame([c.model_dump() for c in candles.candles])
        highs = df["high"].values; lows = df["low"].values; close = df["close"].values
        swing_highs, swing_lows = self._find_swings(highs, lows)
        if not swing_highs or not swing_lows: return MarketStructureResult(trend=TrendDirection.SIDEWAYS)
        trend = self._determine_trend(swing_highs, swing_lows, close[-1])
        bos, choch, last_bos, last_choch = self._detect_smc(swing_highs, swing_lows, close[-1])
        return MarketStructureResult(trend=trend, swing_highs=swing_highs[-5:], swing_lows=swing_lows[-5:], bos_detected=bos, choch_detected=choch, last_bos_price=last_bos, last_choch_price=last_choch)

    def _find_swings(self, highs: np.ndarray, lows: np.ndarray) -> Tuple[List[SwingPoint], List[SwingPoint]]:
        swing_highs: List[SwingPoint] = []; swing_lows: List[SwingPoint] = []; lb = self.lookback
        for i in range(lb, len(highs) - lb):
            window_high = highs[i - lb : i + lb + 1]
            if highs[i] == max(window_high) and np.sum(window_high == highs[i]) == 1: swing_highs.append(SwingPoint(index=i, price=float(highs[i]), type="high", confirmed=True))
            window_low = lows[i - lb : i + lb + 1]
            if lows[i] == min(window_low) and np.sum(window_low == lows[i]) == 1: swing_lows.append(SwingPoint(index=i, price=float(lows[i]), type="low", confirmed=True))
        return swing_highs, swing_lows

    def _determine_trend(self, sh: List[SwingPoint], sl: List[SwingPoint], current_price: float) -> TrendDirection:
        if len(sh) >= 2 and len(sl) >= 2:
            hh = sh[-1].price > sh[-2].price; hl = sl[-1].price > sl[-2].price; lh = sh[-1].price < sh[-2].price; ll = sl[-1].price < sl[-2].price
            if hh and hl: return TrendDirection.UP
            if lh and ll: return TrendDirection.DOWN
        return TrendDirection.SIDEWAYS

    def _detect_smc(self, sh: List[SwingPoint], sl: List[SwingPoint], current_price: float) -> Tuple[bool, bool, float, float]:
        bos = False; choch = False; last_bos = 0.0; last_choch = 0.0
        if not sh or not sl: return bos, choch, last_bos, last_choch
        last_sh = sh[-1].price; last_sl = sl[-1].price
        if current_price > last_sh: bos = True; last_bos = float(last_sh)
        elif current_price < last_sl: bos = True; last_bos = float(last_sl)
        return bos, choch, last_bos, last_choch