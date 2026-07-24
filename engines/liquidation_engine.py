from __future__ import annotations
from engines.base import BaseEngine
from models.analysis import LiquidationResult
from models.derivatives import LiquidationSummary
from models.market_data import CandleSeries

class LiquidationEngine(BaseEngine):
    name: str = "liquidation_engine"
    async def analyze(self, liq: LiquidationSummary, candles: CandleSeries) -> LiquidationResult:
        current_price = float(candles.last_price or 0.0); long_liq = float(liq.long_liquidations_usd_24h); short_liq = float(liq.short_liquidations_usd_24h)
        dominant = "balanced"
        if long_liq > short_liq * 1.5: dominant = "long"
        elif short_liq > long_liq * 1.5: dominant = "short"
        cluster_above_usd = 0.0; cluster_below_usd = 0.0; nearest_side = None; nearest_dist = float("inf")
        for c in liq.clusters:
            price = float(c.get("price", 0)); vol = float(c.get("volUsd", 0))
            if price == 0: continue
            if price > current_price:
                cluster_above_usd += vol; dist = (price - current_price) / current_price
                if dist < nearest_dist: nearest_dist = dist; nearest_side = "above"
            else:
                cluster_below_usd += vol; dist = (current_price - price) / current_price
                if dist < nearest_dist: nearest_dist = dist; nearest_side = "below"
        confidence = 0.7 if dominant != "balanced" else 0.4
        return LiquidationResult(dominant_side=dominant, long_liq_usd_24h=long_liq, short_liq_usd_24h=short_liq, cluster_above_price_usd=cluster_above_usd, cluster_below_price_usd=cluster_below_usd, nearest_cluster_side=nearest_side, nearest_cluster_distance_pct=float(nearest_dist) if nearest_dist != float("inf") else None, confidence=confidence)