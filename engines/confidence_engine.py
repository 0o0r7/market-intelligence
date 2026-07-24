from __future__ import annotations
from typing import List
from engines.base import BaseEngine
from models.analysis import ConfidenceResult, FundingResult, LiquidationResult, LiquidityResult, MarketStructureResult, OpenInterestResult, PositioningResult, RegimeResult
from models.enums import RiskLevel, TrendDirection

class ConfidenceEngine(BaseEngine):
    name: str = "confidence_engine"
    async def analyze(self, structure: MarketStructureResult, regime: RegimeResult, funding: FundingResult, oi: OpenInterestResult, liq: LiquidationResult, liquidity: LiquidityResult, positioning: PositioningResult) -> ConfidenceResult:
        evidence_score = 50.0; contributing_signals: List[dict] = []; conflicts: List[str] = []
        trend_score = 0.0
        if regime.regime.value.startswith("trending") and structure.trend != TrendDirection.SIDEWAYS:
            if (regime.regime.value == "trending_up" and structure.trend == TrendDirection.UP) or (regime.regime.value == "trending_down" and structure.trend == TrendDirection.DOWN):
                trend_score = 20.0; contributing_signals.append({"signal": "trend_alignment", "score": 20.0})
            else: conflicts.append("Regime and Structure trend mismatch"); trend_score = -10.0
        elif regime.regime.value in ["compression", "range"]: trend_score = 5.0; contributing_signals.append({"signal": "range_identified", "score": 5.0})
        deriv_score = 0.0
        if structure.trend == TrendDirection.UP:
            if oi.state == "rising" and oi.divergence_signal != "bearish_divergence": deriv_score += 15.0; contributing_signals.append({"signal": "oi_confirms_uptrend", "score": 15.0})
            else: conflicts.append("OI diverging from uptrend"); deriv_score -= 10.0
            if funding.state in ["bullish", "extreme_long"]: deriv_score += 5.0
            elif funding.state in ["bearish", "extreme_short"]: deriv_score += 15.0; contributing_signals.append({"signal": "short_squeeze_fuel", "score": 15.0})
        elif structure.trend == TrendDirection.DOWN:
            if oi.state == "rising" and oi.divergence_signal != "bullish_divergence": deriv_score += 15.0; contributing_signals.append({"signal": "oi_confirms_downtrend", "score": 15.0})
            else: conflicts.append("OI diverging from downtrend"); deriv_score -= 10.0
        liq_score = 0.0
        if liq.nearest_cluster_side == "above" and structure.trend == TrendDirection.UP: liq_score += 10.0; contributing_signals.append({"signal": "liquidity_pool_above", "score": 10.0})
        elif liq.nearest_cluster_side == "below" and structure.trend == TrendDirection.DOWN: liq_score += 10.0; contributing_signals.append({"signal": "liquidity_pool_below", "score": 10.0})
        pos_score = 0.0
        if positioning.state.value == "extreme_long" and structure.trend == TrendDirection.UP: pos_score -= 10.0; conflicts.append("Extreme long positioning in uptrend (late stage risk)")
        elif positioning.state.value == "extreme_short" and structure.trend == TrendDirection.DOWN: pos_score -= 10.0; conflicts.append("Extreme short positioning in downtrend (late stage risk)")
        evidence_score = 50.0 + trend_score + deriv_score + liq_score + pos_score
        evidence_score = max(10.0, min(100.0, evidence_score))
        tier = "moderate"
        if evidence_score >= 85: tier = "very_high"
        elif evidence_score >= 70: tier = "high"
        elif evidence_score >= 40: tier = "moderate"
        elif evidence_score >= 20: tier = "low"
        else: tier = "very_low"
        return ConfidenceResult(evidence_score=round(evidence_score, 2), tier=tier, contributing_signals=contributing_signals, conflicts=conflicts)

    def assess_risk(self, regime: RegimeResult, liquidity: LiquidityResult, confidence: ConfidenceResult) -> RiskLevel:
        if liquidity.state.value == "thin" or regime.volatility_rank > 0.9: return RiskLevel.EXTREME
        if confidence.tier == "very_low" or "mismatch" in " ".join(confidence.conflicts).lower(): return RiskLevel.HIGH
        if regime.regime.value == "price_discovery": return RiskLevel.ELEVATED
        if confidence.tier in ["high", "very_high"] and liquidity.state.value in ["deep", "moderate"]: return RiskLevel.LOW
        return RiskLevel.MODERATE