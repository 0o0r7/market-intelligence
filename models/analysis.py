from __future__ import annotations
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field
from models.enums import LiquidityState, MarketRegime, PositioningState, RiskLevel, TrendDirection

class SwingPoint(BaseModel):
    index: int; price: Decimal; type: str; confirmed: bool

class MarketStructureResult(BaseModel):
    trend: TrendDirection; swing_highs: List[SwingPoint] = Field(default_factory=list); swing_lows: List[SwingPoint] = Field(default_factory=list); bos_detected: bool = False; choch_detected: bool = False; last_bos_price: Optional[Decimal] = None; last_choch_price: Optional[Decimal] = None; htf_alignment: Optional[TrendDirection] = None

class RegimeResult(BaseModel):
    regime: MarketRegime; adx: float; atr_pct: float; bb_width: float; volatility_rank: float; compression_score: float; expansion_score: float; confidence: float

class FundingResult(BaseModel):
    state: str; annualized_pct: float; skew_vs_oi: float; momentum_4h: float; confidence: float

class OpenInterestResult(BaseModel):
    state: str; oi_change_24h_pct: float; price_oi_correlation: float; divergence_signal: Optional[str] = None; confidence: float

class LiquidationResult(BaseModel):
    dominant_side: str; long_liq_usd_24h: float; short_liq_usd_24h: float; cluster_above_price_usd: float; cluster_below_price_usd: float; nearest_cluster_side: Optional[str] = None; nearest_cluster_distance_pct: Optional[float] = None; confidence: float

class LiquidityResult(BaseModel):
    state: LiquidityState; spread_bps: float; depth_1pct_usd: float; depth_2pct_usd: float; bid_ask_imbalance: float; nearest_support: Optional[float] = None; nearest_resistance: Optional[float] = None; confidence: float

class PositioningResult(BaseModel):
    state: PositioningState; lsr_zscore: float; funding_zscore: float; oi_zscore: float; composite_positioning: float; confidence: float

class ConfidenceResult(BaseModel):
    evidence_score: float; tier: str; contributing_signals: List[dict] = Field(default_factory=list); conflicts: List[str] = Field(default_factory=list)