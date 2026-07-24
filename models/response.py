from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class HealthResponse(BaseModel):
    status: str = "healthy"; service: str = "crypto-data-aggregator"; version: str = "1.0.0"; environment: str; timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat()); components: Dict[str, str] = Field(default_factory=dict)

class ErrorResponse(BaseModel):
    error: str; detail: Optional[str] = None; request_id: Optional[str] = None; timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class MarketIntelligenceResponse(BaseModel):
    symbol: str; price: float; funding_rate: float; open_interest: float; oi_change_24h: float; long_short_ratio: float; liquidations: float; market_regime: str; liquidity_state: str; positioning_state: str; risk_level: str; evidence_score: float; summary: str
    timeframe: str; timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    market_structure: Optional[Dict[str, Any]] = None; regime_detail: Optional[Dict[str, Any]] = None; funding_detail: Optional[Dict[str, Any]] = None; open_interest_detail: Optional[Dict[str, Any]] = None; liquidation_detail: Optional[Dict[str, Any]] = None; liquidity_detail: Optional[Dict[str, Any]] = None; positioning_detail: Optional[Dict[str, Any]] = None
    confidence_tier: Optional[str] = None; contributing_signals: List[Dict[str, Any]] = Field(default_factory=list); conflicts: List[str] = Field(default_factory=list)
    exchanges_used: List[str] = Field(default_factory=list); data_as_of: Optional[str] = None; chart_url: Optional[str] = None

class MarketScanResponse(BaseModel):
    scan_id: str; timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat()); timeframe: str; symbols_scanned: int; results: List[Dict[str, Any]] = Field(default_factory=list); top_opportunities: List[Dict[str, Any]] = Field(default_factory=list); market_breadth: Optional[Dict[str, Any]] = None

class ChartResponse(BaseModel):
    chart_url: str; symbol: str; timeframe: str; generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat()); width: int = 1600; height: int = 900; overlays: List[str] = Field(default_factory=list)