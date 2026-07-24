from __future__ import annotations
from decimal import Decimal
from typing import List
from models.derivatives import LongShortRatioPoint, LongShortRatioSummary
from services.coinglass import CoinGlassClient
from utils.timing import utc_now_ms

class PositioningAggregator:
    def __init__(self, coinglass: CoinGlassClient): self.coinglass = coinglass

    async def get_summary(self, symbol: str) -> LongShortRatioSummary:
        lsr_data = await self.coinglass.get_long_short_ratio(symbol, interval="1h", limit=24)
        points: List[LongShortRatioPoint] = []; agg_long = Decimal("0"); agg_short = Decimal("0")
        for item in lsr_data:
            long_ratio = Decimal(str(item.get("longAccount", item.get("longRate", 0.5))))
            short_ratio = Decimal(str(item.get("shortAccount", item.get("shortRate", 0.5))))
            points.append(LongShortRatioPoint(exchange=item.get("exchangeName", "aggregated").lower(), symbol=symbol, long_ratio=long_ratio, short_ratio=short_ratio, long_short_ratio=long_ratio / short_ratio if short_ratio > 0 else Decimal("0"), timestamp=int(item.get("time", utc_now_ms()))))
            agg_long += long_ratio; agg_short += short_ratio
        exchanges_count = len(points) if points else 1
        final_long = agg_long / Decimal(exchanges_count)
        final_short = agg_short / Decimal(exchanges_count)
        final_ratio = final_long / final_short if final_short > 0 else Decimal("0")
        return LongShortRatioSummary(symbol=symbol, aggregated_long_ratio=final_long, aggregated_short_ratio=final_short, aggregated_long_short_ratio=final_ratio, by_exchange=points, as_of=utc_now_ms())