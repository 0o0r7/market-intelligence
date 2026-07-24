from __future__ import annotations
import asyncio
import time
from typing import Any, Awaitable, Callable, Dict, Tuple, TypeVar
T = TypeVar("T")

class AsyncTTLCache:
    def __init__(self, ttl_seconds: int = 15, maxsize: int = 1024):
        self.ttl = ttl_seconds; self.maxsize = maxsize
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._global_lock = asyncio.Lock()

    async def get_or_set(self, key: str, factory: Callable[[], Awaitable[T]]) -> T:
        now = time.monotonic()
        if key in self._cache:
            ts, val = self._cache[key]
            if now - ts < self.ttl: return val
        async with self._global_lock:
            if key not in self._locks: self._locks[key] = asyncio.Lock()
            lock = self._locks[key]
        async with lock:
            if key in self._cache:
                ts, val = self._cache[key]
                if time.monotonic() - ts < self.ttl: return val
            val = await factory()
            self._cache[key] = (time.monotonic(), val)
            if len(self._cache) > self.maxsize:
                oldest_key = min(self._cache, key=lambda k: self._cache[k][0])
                del self._cache[oldest_key]
            return val