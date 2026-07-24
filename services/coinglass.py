from __future__ import annotations
from typing import Any, Dict, List
from config.logging import get_logger
from config.settings import get_settings
from services.base.http_client import AsyncHttpClient
from utils.cache import AsyncTTLCache
from utils.security import resolve_secret
log = get_logger(__name__)

class CoinGlassClient:
    name: str = "coinglass"
    def __init__(self) -> None:
        settings = get_settings()
        api_key = resolve_secret("COINGLASS_API_KEY", required=True)
        self.http = AsyncHttpClient(base_url=settings.coinglass_base_url, headers={"CG-API-KEY": api_key}, name=self.name)
        self._fund_cache = AsyncTTLCache(ttl_seconds=settings.funding_cache_ttl_seconds)
        self._oi_cache = AsyncTTLCache(ttl_seconds=settings.oi_cache_ttl_seconds)
        self._lsr_cache = AsyncTTLCache(ttl_seconds=settings.lsr_cache_ttl_seconds)
        self._liq_cache = AsyncTTLCache(ttl_seconds=settings.liquidation_cache_ttl_seconds)

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        s = symbol.upper().replace("-", "")
        return s[:-4] if s.endswith("USDT") else s

    async def _request(self, path: str, params: Dict[str, Any]) -> Any:
        data = await self.http.get(path, params=params)
        if data.get("code") != "0":
            log.error("coinglass.api_error", path=path, msg=data.get("msg"))
            raise ValueError(f"CoinGlass API Error: {data.get('msg')}")
        return data.get("data", [])

    async def get_funding_rates(self, symbol: str) -> List[Dict[str, Any]]:
        sym = self._normalize_symbol(symbol); cache_key = f"fund:{sym}"
        async def _fetch() -> List[Dict[str, Any]]: return await self._request("/api/futures/fundingRate/current", {"symbol": sym})
        return await self._fund_cache.get_or_set(cache_key, _fetch)

    async def get_open_interest_history(self, symbol: str, interval: str = "1h", limit: int = 48) -> List[Dict[str, Any]]:
        sym = self._normalize_symbol(symbol); cache_key = f"oi_hist:{sym}:{interval}:{limit}"
        async def _fetch() -> List[Dict[str, Any]]: return await self._request("/api/futures/openInterest/ohlc-history", {"symbol": sym, "interval": interval, "limit": limit})
        return await self._oi_cache.get_or_set(cache_key, _fetch)

    async def get_long_short_ratio(self, symbol: str, interval: str = "1h", limit: int = 24) -> List[Dict[str, Any]]:
        sym = self._normalize_symbol(symbol); cache_key = f"lsr:{sym}:{interval}:{limit}"
        async def _fetch() -> List[Dict[str, Any]]: return await self._request("/api/futures/longShort/chart", {"symbol": sym, "interval": interval, "limit": limit})
        return await self._lsr_cache.get_or_set(cache_key, _fetch)

    async def get_liquidations(self, symbol: str, interval: str = "1h", lookback: int = 24) -> List[Dict[str, Any]]:
        sym = self._normalize_symbol(symbol); cache_key = f"liq:{sym}:{interval}:{lookback}"
        async def _fetch() -> List[Dict[str, Any]]: return await self._request("/api/futures/liquidation/chart", {"symbol": sym, "interval": interval, "limit": lookback})
        return await self._liq_cache.get_or_set(cache_key, _fetch)

    async def get_liquidation_clusters(self, symbol: str, range_pct: float = 0.05) -> List[Dict[str, Any]]:
        sym = self._normalize_symbol(symbol); cache_key = f"liq_cluster:{sym}:{range_pct}"
        async def _fetch() -> List[Dict[str, Any]]: return await self._request("/api/futures/liquidation/aggregated-chart", {"symbol": sym, "range": range_pct})
        return await self._liq_cache.get_or_set(cache_key, _fetch)

    async def close(self) -> None: await self.http.close()