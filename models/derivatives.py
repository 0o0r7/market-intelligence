from __future__ import annotations
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field

class FundingRatePoint(BaseModel):
    exchange: str; symbol: str; funding_rate: Decimal; next_funding_time: Optional[int] = None; timestamp: int

class FundingRateSummary(BaseModel):
    symbol: str; weighted_funding_rate: Decimal; median_funding_rate: Decimal; max_funding_rate: Decimal; min_funding_rate: Decimal; exchanges_sampled: int; annualized_pct: Decimal; history: List[FundingRatePoint] = Field(default_factory=list); as_of: int

class OpenInterestPoint(BaseModel):
    exchange: str; symbol: str; open_interest_usd: Decimal; open_interest_base: Optional[Decimal] = None; timestamp: int

class OpenInterestSummary(BaseModel):
    symbol: str; total_oi_usd: Decimal; oi_change_1h_pct: Decimal; oi_change_4h_pct: Decimal; oi_change_24h_pct: Decimal; by_exchange: List[OpenInterestPoint] = Field(default_factory=list); history: List[Decimal] = Field(default_factory=list); as_of: int

class LongShortRatioPoint(BaseModel):
    exchange: str; symbol: str; long_ratio: Decimal; short_ratio: Decimal; long_short_ratio: Decimal; timestamp: int

class LongShortRatioSummary(BaseModel):
    symbol: str; aggregated_long_ratio: Decimal; aggregated_short_ratio: Decimal; aggregated_long_short_ratio: Decimal; by_exchange: List[LongShortRatioPoint] = Field(default_factory=list); as_of: int

class LiquidationEvent(BaseModel):
    exchange: str; symbol: str; side: str; price: Decimal; size_usd: Decimal; timestamp: int

class LiquidationSummary(BaseModel):
    symbol: str; total_liquidations_usd_24h: Decimal; long_liquidations_usd_24h: Decimal; short_liquidations_usd_24h: Decimal; largest_single_usd: Decimal; events: List[LiquidationEvent] = Field(default_factory=list); clusters: List[dict] = Field(default_factory=list); as_of: int

class DerivativesSnapshot(BaseModel):
    funding: Optional[FundingRateSummary] = None; open_interest: Optional[OpenInterestSummary] = None; long_short_ratio: Optional[LongShortRatioSummary] = None; liquidations: Optional[LiquidationSummary] = None