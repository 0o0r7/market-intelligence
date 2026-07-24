from __future__ import annotations
import asyncio
from typing import Dict, List, Optional
from config.logging import get_logger
from engines.confidence_engine import ConfidenceEngine
from engines.funding_engine import FundingEngine
from engines.liquidation_engine import LiquidationEngine
from engines.liquidity_engine import LiquidityEngine
from engines.market_structure_engine import MarketStructureEngine
from engines.oi_engine import OpenInterestEngine
from engines.positioning_engine import PositioningEngine
from engines.regime_engine import RegimeEngine
from models.response import MarketIntelligenceResponse, MarketScanResponse
from services.binance import BinanceClient
from services.bybit import BybitClient
from services.coinglass import CoinGlassClient
from services.funding import FundingAggregator
from services.liquidations import LiquidationAggregator
from services.okx import OKXClient
from services.open_interest import OpenInterestAggregator
from services.positioning import PositioningAggregator
from charts.renderer import ChartRenderer
from utils.timing import utc_now_iso
from utils.validation import validate_symbol, validate_timeframe
log = get_logger(__name__)

class Orchestrator:
    def __init__(self) -> None:
        self.binance = BinanceClient(); self.bybit = BybitClient(); self.okx = OKXClient(); self.cg = CoinGlassClient()
        self.funding_agg = FundingAggregator(self.cg, self.bybit, self.okx)
        self.oi_agg = OpenInterestAggregator(self.cg, self.bybit, self.okx)
        self.liq_agg = LiquidationAggregator(self.cg)
        self.pos_agg = PositioningAggregator(self.cg)
        self.struct_eng = MarketStructureEngine(); self.regime_eng = RegimeEngine(); self.fund_eng = FundingEngine()
        self.oi_eng = OpenInterestEngine(); self.liq_eng = LiquidationEngine(); self.liqty_eng = LiquidityEngine()
        self.pos_eng = PositioningEngine(); self.conf_eng = ConfidenceEngine()
        self.chart_renderer = ChartRenderer()

    async def get_market_intelligence(self, symbol: str, timeframe: str) -> MarketIntelligenceResponse:
        sym = validate_symbol(symbol); tf = validate_timeframe(timeframe)
        try:
            log.info("fetching_market_data", symbol=sym, timeframe=tf)
            candles, order_book, funding, oi, liq, pos = await asyncio.gather(
                self.binance.get_candles(sym, tf, limit=300), self.binance.get_order_book(sym, depth=100),
                self.funding_agg.get_summary(sym), self.oi_agg.get_summary(sym), self.liq_agg.get_summary(sym), self.pos_agg.get_summary(sym))
            log.info("running_analysis_engines", symbol=sym)
            struct_res, regime_res, fund_res, oi_res, liq_res, liqty_res, pos_res = await asyncio.gather(
                self.struct_eng.analyze(candles), self.regime_eng.analyze(candles), self.fund_eng.analyze(funding),
                self.oi_eng.analyze(oi, candles), self.liq_eng.analyze(liq, candles), self.liqty_eng.analyze(order_book, candles),
                self.pos_eng.analyze(pos, funding, oi))
            conf_res = await self.conf_eng.analyze(struct_res, regime_res, fund_res, oi_res, liq_res, liqty_res, pos_res)
            risk_level = self.conf_eng.assess_risk(regime_res, liqty_res, conf_res)
            summary = self._generate_summary(sym, tf, regime_res, struct_res, conf_res, risk_level)
            return MarketIntelligenceResponse(
                symbol=sym, price=float(candles.last_price or 0), funding_rate=float(funding.median_funding_rate),
                open_interest=float(oi.total_oi_usd), oi_change_24h=float(oi.oi_change_24h_pct), long_short_ratio=float(pos.aggregated_long_short_ratio),
                liquidations=float(liq.total_liquidations_usd_24h), market_regime=regime_res.regime.value, liquidity_state=liqty_res.state.value,
                positioning_state=pos_res.state.value, risk_level=risk_level.value, evidence_score=conf_res.evidence_score, summary=summary, timeframe=tf,
                market_structure=struct_res.model_dump(), regime_detail=regime_res.model_dump(), funding_detail=fund_res.model_dump(),
                open_interest_detail=oi_res.model_dump(), liquidation_detail=liq_res.model_dump(), liquidity_detail=liqty_res.model_dump(),
                positioning_detail=pos_res.model_dump(), confidence_tier=conf_res.tier, contributing_signals=conf_res.contributing_signals,
                conflicts=conf_res.conflicts, exchanges_used=["binance", "bybit", "okx", "coinglass"], data_as_of=utc_now_iso(), chart_url=None)
        except Exception as e:
            log.error("orchestration_failed", symbol=sym, error=str(e), exc_info=True); raise

    async def get_market_scan(self, symbols: List[str], timeframe: str) -> MarketScanResponse:
        tf = validate_timeframe(timeframe); valid_syms = [validate_symbol(s) for s in symbols]
        results = []; tasks = [self.get_market_intelligence(s, tf) for s in valid_syms]
        scan_results = await asyncio.gather(*tasks, return_exceptions=True)
        for s, res in zip(valid_syms, scan_results):
            if isinstance(res, Exception): log.warning("scan_symbol_failed", symbol=s, error=str(res)); continue
            results.append(res.model_dump())
        results.sort(key=lambda x: x.get("evidence_score", 0), reverse=True)
        return MarketScanResponse(scan_id=f"scan_{utc_now_iso()}", timeframe=tf, symbols_scanned=len(results), results=results, top_opportunities=results[:3])

    async def generate_chart(self, symbol: str, timeframe: str) -> str:
        sym = validate_symbol(symbol); tf = validate_timeframe(timeframe)
        try:
            log.info("fetching_chart_data", symbol=sym, timeframe=tf)
            candles, order_book, liq = await asyncio.gather(self.binance.get_candles(sym, tf, limit=100), self.binance.get_order_book(sym, depth=100), self.liq_agg.get_summary(sym))
            log.info("analyzing_chart_data", symbol=sym)
            struct_res, liqty_res = await asyncio.gather(self.struct_eng.analyze(candles), self.liqty_eng.analyze(order_book, candles))
            log.info("rendering_chart", symbol=sym)
            chart_url = await self.chart_renderer.generate_chart_url(candles, struct_res, liqty_res, liq, sym, tf)
            return chart_url
        except Exception as e:
            log.error("chart_orchestration_failed", symbol=sym, error=str(e), exc_info=True); raise

    def _generate_summary(self, symbol, timeframe, regime, structure, confidence, risk) -> str:
        regime_str = regime.regime.value.replace("_", " "); trend_str = structure.trend.value; risk_str = risk.value
        summary = f"{symbol} on {timeframe} timeframe is currently in a {regime_str} state with a {trend_str} market structure. "
        if confidence.conflicts: summary += f"Warning: {len(confidence.conflicts)} signal conflict(s) detected. "
        summary += f"Evidence score is {confidence.evidence_score}/100 ({confidence.tier}). Risk level: {risk_str}."
        return summary

    async def close(self) -> None:
        await asyncio.gather(self.binance.close(), self.bybit.close(), self.okx.close(), self.cg.close(), return_exceptions=True)