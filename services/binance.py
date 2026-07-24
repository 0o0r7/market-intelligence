from __future__ import annotations
from typing import List
from config.logging import get_logger
from config.settings import get_settings
from models.market_data import Candle, CandleSeries, OrderBook, OrderBookLevel, Ticker, Trade
from services.base.exchange_client import ExchangeClient
from services.base.http_client import AsyncHttpClient
from utils.cache import AsyncTTLCache
from utils.timing import utc_now_ms
log = get_logger(__name__)

class BinanceClient(ExchangeClient):
    name: str = "binance"
    def __init__(self) -> None:
        settings = get_settings()
        self.http = AsyncHttpClient(base_url=settings.binance_rest_base_url, name=self.name)
        self._candle_cache = AsyncTTLCache(ttl_seconds=settings.candle_cache_ttl_seconds)
        self._ob_cache = AsyncTTLCache(ttl_seconds=settings.orderbook_cache_ttl_seconds)

    @staticmethod
    def _normalize_symbol(symbol: str) -> str: return symbol.upper().replace("-", "")

    async def get_candles(self, symbol: str, timeframe: str, limit: int = 300) -> CandleSeries:
        sym = self._normalize_symbol(symbol); cache_key = f"candles:{sym}:{timeframe}:{limit}"
        async def _fetch() -> CandleSeries:
            params = {"symbol": sym, "interval": timeframe, "limit": limit}
            data = await self.http.get("/api/v3/klines", params=params)
            candles = [Candle(open_time=int(c[0]), open=float(c[1]), high=float(c[2]), low=float(c[3]), close=float(c[4]), volume=float(c[5]), close_time=int(c[6]), quote_volume=float(c[7]), trades=int(c[8]), closed=True) for c in data]
            return CandleSeries(symbol=sym, exchange=self.name, timeframe=timeframe, candles=candles)
        return await self._candle_cache.get_or_set(cache_key, _fetch)

    async def get_order_book(self, symbol: str, depth: int = 100) -> OrderBook:
        sym = self._normalize_symbol(symbol); cache_key = f"ob:{sym}:{depth}"
        async def _fetch() -> OrderBook:
            params = {"symbol": sym, "limit": depth}
            data = await self.http.get("/api/v3/depth", params=params)
            bids = [OrderBookLevel(price=float(b[0]), size=float(b[1])) for b in data.get("bids", [])]
            asks = [OrderBookLevel(price=float(a[0]), size=float(a[1])) for a in data.get("asks", [])]
            return OrderBook(symbol=sym, exchange=self.name, timestamp=utc_now_ms(), bids=bids, asks=asks)
        return await self._ob_cache.get_or_set(cache_key, _fetch)

    async def get_ticker(self, symbol: str) -> Ticker:
        sym = self._normalize_symbol(symbol); params = {"symbol": sym}
        data = await self.http.get("/api/v3/ticker/24hr", params=params)
        return Ticker(symbol=sym, exchange=self.name, last_price=float(data["lastPrice"]), bid=float(data["bidPrice"]), ask=float(data["askPrice"]), volume_24h=float(data["volume"]), quote_volume_24h=float(data["quoteVolume"]), high_24h=float(data["highPrice"]), low_24h=float(data["lowPrice"]), price_change_pct_24h=float(data["priceChangePercent"]), timestamp=utc_now_ms())

    async def get_recent_trades(self, symbol: str, limit: int = 500) -> List[Trade]:
        sym = self._normalize_symbol(symbol); params = {"symbol": sym, "limit": limit}
        data = await self.http.get("/api/v3/trades", params=params)
        return [Trade(symbol=sym, exchange=self.name, price=float(t["price"]), size=float(t["qty"]), side="buy" if t["isBuyerMaker"] else "sell", timestamp=int(t["time"])) for t in data]

    async def close(self) -> None: await self.http.close()