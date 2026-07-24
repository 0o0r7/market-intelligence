from __future__ import annotations
from decimal import Decimal
from typing import List
from models.derivatives import LiquidationEvent, LiquidationSummary
from services.coinglass import CoinGlassClient
from utils.timing import utc_now_ms

class LiquidationAggregator:
    def __init__(self, coinglass: CoinGlassClient): self.coinglass = coinglass

    async def get_summary(self, symbol: str) -> LiquidationSummary:
        liq_data = await self.coinglass.get_liquidations(symbol, interval="1h", lookback=24)
        clusters = await self.coinglass.get_liquidation_clusters(symbol)
        long_liq = Decimal("0"); short_liq = Decimal("0"); events: List[LiquidationEvent] = []; largest_single = Decimal("0")
        for item in liq_data:
            l = Decimal(str(item.get("longVolUsd", item.get("longs", 0))))
            s = Decimal(str(item.get("shortVolUsd", item.get("shorts", 0))))
            long_liq += l; short_liq += s
            if l > largest_single: largest_single = l
            if s > largest_single: largest_single = s
            for ev in item.get("data", []):
                events.append(LiquidationEvent(exchange=ev.get("exchangeName", "unknown").lower(), symbol=symbol, side=ev.get("side", "long"), price=Decimal(str(ev.get("price", 0))), size_usd=Decimal(str(ev.get("volUsd", 0))), timestamp=int(ev.get("time", 0))))
        total = long_liq + short_liq
        return LiquidationSummary(symbol=symbol, total_liquidations_usd_24h=total, long_liquidations_usd_24h=long_liq, short_liquidations_usd_24h=short_liq, largest_single_usd=largest_single, events=events, clusters=clusters, as_of=utc_now_ms())