from __future__ import annotations
from engines.base import BaseEngine
from models.analysis import PositioningResult
from models.derivatives import FundingRateSummary, LongShortRatioSummary, OpenInterestSummary
from models.enums import PositioningState

class PositioningEngine(BaseEngine):
    name: str = "positioning_engine"
    async def analyze(self, lsr: LongShortRatioSummary, funding: FundingRateSummary, oi: OpenInterestSummary) -> PositioningResult:
        ratio = float(lsr.aggregated_long_short_ratio)
        lsr_zscore = (ratio - 1.0) * 2.0; fr_zscore = float(funding.median_funding_rate) * 2000.0; oi_zscore = float(oi.oi_change_24h_pct) / 5.0
        composite = (lsr_zscore * 0.4) + (fr_zscore * 0.4) + (oi_zscore * 0.2)
        state = PositioningState.NEUTRAL
        if composite > 1.0: state = PositioningState.EXTREME_LONG
        elif composite > 0.3: state = PositioningState.LONG
        elif composite < -1.0: state = PositioningState.EXTREME_SHORT
        elif composite < -0.3: state = PositioningState.SHORT
        confidence = 0.7 if state in [PositioningState.EXTREME_LONG, PositioningState.EXTREME_SHORT] else 0.5
        return PositioningResult(state=state, lsr_zscore=float(lsr_zscore), funding_zscore=float(fr_zscore), oi_zscore=float(oi_zscore), composite_positioning=float(composite), confidence=float(confidence))