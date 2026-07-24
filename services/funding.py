from __future__ import annotations
from decimal import Decimal
from typing import List
from models.derivatives import FundingRatePoint, FundingRateSummary
from services.bybit import BybitClient
from services.coinglass import CoinGlassClient
from services.okx import OKXClient
from utils.timing import utc_now_ms

class FundingAggregator:
    def __init__(self, coinglass: CoinGlassClient, bybit: BybitClient, okx: OKXClient):
        self.coinglass = coinglass; self.bybit = bybit; self.okx = okx

    async def get_summary(self, symbol: str) -> FundingRateSummary:
        cg_data = await self.coinglass.get_funding_rates(symbol)
        bybit_fr = await self.bybit.get_funding_rate(symbol)
        okx_fr = await self.okx.get_funding_rate(symbol)
        points: List[FundingRatePoint] = []
        for item in cg_data:
            points.append(FundingRatePoint(exchange=item.get("exchangeName", "unknown").lower(), symbol=symbol, funding_rate=Decimal(str(item.get("rate", 0))), next_funding_time=int(item.get("nextFundingTime", 0)), timestamp=utc_now_ms()))
        if bybit_fr and not any(p.exchange == "bybit" for p in points): points.append(bybit_fr)
        if okx_fr and not any(p.exchange == "okx" for p in points): points.append(okx_fr)
        rates = [p.funding_rate for p in points]
        if not rates:
            return FundingRateSummary(symbol=symbol, weighted_funding_rate=Decimal("0"), median_funding_rate=Decimal("0"), max_funding_rate=Decimal("0"), min_funding_rate=Decimal("0"), exchanges_sampled=0, annualized_pct=Decimal("0"), history=points, as_of=utc_now_ms())
        sorted_rates = sorted(rates)
        median = sorted_rates[len(sorted_rates) // 2]
        annualized = median * Decimal("1095")
        return FundingRateSummary(symbol=symbol, weighted_funding_rate=median, median_funding_rate=median, max_funding_rate=max(rates), min_funding_rate=min(rates), exchanges_sampled=len(points), annualized_pct=annualized * Decimal("100"), history=points, as_of=utc_now_ms())