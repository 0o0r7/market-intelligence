from __future__ import annotations
from typing import List, Optional
from config.logging import get_logger
from config.settings import get_settings
from models.market_data import Candle, CandleSeries, OrderBook, OrderBookLevel, Ticker, Trade
from models.derivatives import FundingRatePoint, OpenInterestPoint
from services.base.exchange_client import ExchangeClient
from services.base.http_client import AsyncHttpClient
from utils.cache import AsyncTTLCache
from utils.timing import utc_now_ms
log = get_logger(__name__)

class OKXClient(ExchangeClient):
    name: str = "okx"
    def __init__(self) -> None:
        settings = get_settings()
        self.http = AsyncHttpClient(base_url=settings.okx_rest_base_url, name=self.name)
        self._candle_cache = AsyncTTLCache(ttl_seconds=settings.candle_cache_ttl_seconds)
        self._ob_cache = AsyncTTLCache(ttl_seconds=settings.orderbook_cache_ttl_seconds)
        self._fund_cache = AsyncTTLCache(ttl_seconds=settings.funding_cache_ttl_seconds)
        self._oi_cache = AsyncTTLCache(ttl_seconds=settings.oi_cache_ttl_seconds)

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        base = symbol.upper().replace("-", "").replace("USDT", "")
        return f"{base}-USDT-SWAP"

    async def get_candles(self, symbol: str, timeframe: str, limit: int = 300) -> CandleSeries:
        sym = self._normalize_symbol(symbol); cache_key = f"candles:{sym}:{timeframe}:{limit}"
        async def _fetch() -> CandleSeries:
            params = {"instId": sym, "bar": timeframe, "limit": limit}
            data = await self.http.get("/api/v5/market/candles", params=params)
            rows = reversed(data.get("data", []))
            candles = [Candle(open_time=int(c[0]), open=float(c[1]), high=float(c[2]), low=float(c[3]), close=float(c[4]), volume=float(c[5]), close_time=int(c[0]) + 1, quote_volume=float(c[7]) if len(c) > 7 else 0.0, trades=0, closed=True if c[8] == "1" else False) for c in rows]
            return CandleSeries(symbol=sym, exchange=self.name, timeframe=timeframe, candles=candles)
        return await self._candle_cache.get_or_set(cache_key, _fetch)

    async def get_order_book(self, symbol: str, depth: int = 100) -> OrderBook:
        sym = self._normalize_symbol(symbol); cache_key = f"ob:{sym}:{depth}"
        async def _fetch() -> OrderBook:
            params = {"instId": sym, "sz": depth}
            data = await self.http.get("/api/v5/market/books", params=params)
            bids = [OrderBookLevel(price=float(b[0]), size=float(b[1])) for b in data.get("data", [{}])[0].get("bids", [])]
            asks = [OrderBookLevel(price=float(a[0]), size=float(a[1])) for a in data.get("data", [{}])[0].get("asks", [])]
            return OrderBook(symbol=sym, exchange=self.name, timestamp=utc_now_ms(), bids=bids, asks=asks)
        return await self._ob_cache.get_or_set(cache_key, _fetch)

    async def get_ticker(self, symbol: str) -> Ticker:
        sym = self._normalize_symbol(symbol); params = {"instId": sym}
        data = await self.http.get("/api/v5/market/ticker", params=params)
        t = data.get("data", [{}])[0]
        return Ticker(symbol=sym, exchange=self.name, last_price=float(t["last"]), bid=float(t["bidPx"]), ask=float(t["askPx"]), volume_24h=float(t["vol24h"]), quote_volume_24h=float(t["volCcy24h"]), high_24h=float(t["high24h"]), low_24h=float(t["low24h"]), price_change_pct_24h=0.0, timestamp=utc_now_ms())

    async def get_recent_trades(self, symbol: str, limit: int = 500) -> List[Trade]:
        sym = self._normalize_symbol(symbol); params = {"instId": sym, "limit": limit}
        data = await self.http.get("/api/v5/market/trades", params=params)
        return [Trade(symbol=sym, exchange=self.name, price=float(t["px"]), size=float(t["sz"]), side=t["side"], timestamp=int(t["ts"])) for t in data.get("data", [])]

    async def get_funding_rate(self, symbol: str) -> Optional[FundingRatePoint]:
        sym = self._normalize_symbol(symbol); cache_key = f"fund:{sym}"
        async def _fetch() -> Optional[FundingRatePoint]:
            params = {"instId": sym}
            data = await self.http.get("/api/v5/public/funding-rate", params=params)
            fr = data.get("data", [{}])[0]
            if "fundingRate" not in fr: return None
            return FundingRatePoint(exchange=self.name, symbol=sym, funding_rate=float(fr["fundingRate"]), next_funding_time=int(fr["nextFundingTime"]), timestamp=utc_now_ms())
        return await self._fund_cache.get_or_set(cache_key, _fetch)

    async def get_open_interest(self, symbol: str) -> Optional[OpenInterestPoint]:
        sym = self._normalize_symbol(symbol); cache_key = f"oi:{sym}"
        async def _fetch() -> Optional[OpenInterestPoint]:
            params = {"instType": "SWAP", "instId": sym}
            data = await self.http.get("/api/v5/public/open-interest", params=params)
            oi = data.get("data", [{}])[0]
            if "oi" not in oi: return None
            return OpenInterestPoint(exchange=self.name, symbol=sym, open_interest_base=float(oi["oi"]), timestamp=utc_now_ms())
        return await self._oi_cache.get_or_set(cache_key, _fetch)

    async def close(self) -> None: await self.http.close()