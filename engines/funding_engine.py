from __future__ import annotations
from engines.base import BaseEngine
from models.analysis import FundingResult
from models.derivatives import FundingRateSummary

class FundingEngine(BaseEngine):
    name: str = "funding_engine"
    async def analyze(self, funding: FundingRateSummary) -> FundingResult:
        rate = float(funding.median_funding_rate); annualized = float(funding.annualized_pct); state = "neutral"; confidence = 0.5
        if rate > 0.0005: state = "bullish" if rate < 0.001 else "extreme_long"; confidence = 0.8
        elif rate < -0.0001: state = "bearish" if rate > -0.0005 else "extreme_short"; confidence = 0.8
        return FundingResult(state=state, annualized_pct=annualized, skew_vs_oi=0.0, momentum_4h=0.0, confidence=confidence)