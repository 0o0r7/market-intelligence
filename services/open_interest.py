from __future__ import annotations
from decimal import Decimal
from typing import List
from models.derivatives import OpenInterestPoint, OpenInterestSummary
from services.bybit import BybitClient
from services.coinglass import CoinGlassClient
from services.okx import OKXClient
from utils.timing import utc_now_ms

class OpenInterestAggregator:
    def __init__(self, coinglass: CoinGlassClient, bybit: BybitClient, okx: OKXClient):
        self.coinglass = coinglass; self.bybit = bybit; self.okx = okx

    async def get_summary(self, symbol: str) -> OpenInterestSummary:
        cg_history = await self.coinglass.get_open_interest_history(symbol, interval="1h", limit=24)
        bybit_oi = await self.bybit.get_open_interest(symbol)
        okx_oi = await self.okx.get_open_interest(symbol)
        points: List[OpenInterestPoint] = []
        if bybit_oi: points.append(bybit_oi)
        if okx_oi: points.append(okx_oi)
        history_usd = [Decimal(str(h.get("openInterest", 0))) for h in reversed(cg_history)]
        oi_change_1h = Decimal("0"); oi_change_4h = Decimal("0"); oi_change_24h = Decimal("0")
        if len(history_usd) >= 2:
            prev, curr = history_usd[-2], history_usd[-1]
            if prev > 0: oi_change_1h = ((curr - prev) / prev) * Decimal("100")
        if len(history_usd) >= 5:
            prev, curr = history_usd[-5], history_usd[-1]
            if prev > 0: oi_change_4h = ((curr - prev) / prev) * Decimal("100")
        if len(history_usd) >= 24:
            prev, curr = history_usd[-24], history_usd[-1]
            if prev > 0: oi_change_24h = ((curr - prev) / prev) * Decimal("100")
        total_oi_usd = history_usd[-1] if history_usd else Decimal("0")
        return OpenInterestSummary(symbol=symbol, total_oi_usd=total_oi_usd, oi_change_1h_pct=oi_change_1h, oi_change_4h_pct=oi_change_4h, oi_change_24h_pct=oi_change_24h, by_exchange=points, history=history_usd, as_of=utc_now_ms())