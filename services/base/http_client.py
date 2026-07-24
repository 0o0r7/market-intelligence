from __future__ import annotations
import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict, Mapping, Optional
import aiohttp
import orjson
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential_jitter
from config.logging import get_logger
from config.settings import get_settings
from utils.retry import RetryPolicy

log = get_logger(__name__)

class HttpClientError(Exception):
    def __init__(self, status: int, message: str, payload: Optional[bytes] = None) -> None:
        super().__init__(f"HTTP {status}: {message}")
        self.status = status; self.message = message; self.payload = payload

class RateLimitError(HttpClientError):
    def __init__(self, retry_after: Optional[float] = None) -> None:
        super().__init__(429, "Rate limited"); self.retry_after = retry_after

class AsyncHttpClient:
    def __init__(self, *, base_url: str, headers: Optional[Mapping[str, str]] = None, timeout: Optional[float] = None, retry_policy: Optional[RetryPolicy] = None, name: str = "http") -> None:
        settings = get_settings()
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout or settings.http_timeout_seconds
        self.retry_policy = retry_policy or RetryPolicy(max_attempts=settings.http_max_retries, base_delay=settings.http_retry_backoff_base)
        self.default_headers: Dict[str, str] = {"Accept": "application/json", "User-Agent": "crypto-data-aggregator/1.0 (+azure-functions)"}
        if headers: self.default_headers.update(dict(headers))
        self.name = name
        self._session: Optional[aiohttp.ClientSession] = None
        self._lock = asyncio.Lock()

    async def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            async with self._lock:
                if self._session is None or self._session.closed:
                    timeout = aiohttp.ClientTimeout(total=self.timeout)
                    connector = aiohttp.TCPConnector(limit=100, limit_per_host=20, ttl_dns_cache=300, enable_cleanup_closed=True)
                    self._session = aiohttp.ClientSession(timeout=timeout, connector=connector, headers=self.default_headers)
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed: await self._session.close()

    async def request(self, method: str, path: str, *, params: Optional[Mapping[str, Any]] = None, json_body: Optional[Any] = None, headers: Optional[Mapping[str, str]] = None, base_url: Optional[str] = None) -> Any:
        url = f"{(base_url or self.base_url)}{path}"
        clean_params: Optional[Dict[str, Any]] = None
        if params: clean_params = {k: v for k, v in params.items() if v is not None}

        async def _do_request() -> Any:
            session = await self._ensure_session()
            async with session.request(method=method.upper(), url=url, params=clean_params, json=json_body, headers=headers) as resp:
                body = await resp.read()
                if resp.status == 429: raise RateLimitError(retry_after=float(resp.headers.get("Retry-After")) if resp.headers.get("Retry-After") else None)
                if resp.status >= 500: raise HttpClientError(resp.status, resp.reason or "server error", body)
                if resp.status >= 400: raise HttpClientError(resp.status, resp.reason or "client error", body)
                if not body: return None
                try: return orjson.loads(body)
                except orjson.JSONDecodeError as exc:
                    log.error("http.json_decode_failed", client=self.name, url=url, status=resp.status, error=str(exc))
                    raise HttpClientError(resp.status, "invalid json", body) from exc

        try:
            async for attempt in AsyncRetrying(stop=stop_after_attempt(self.retry_policy.max_attempts), wait=wait_exponential_jitter(initial=self.retry_policy.base_delay, max=self.retry_policy.max_delay), retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError, HttpClientError, RateLimitError)), reraise=True):
                with attempt: return await _do_request()
        except RateLimitError: raise
        except HttpClientError: raise
        except Exception as exc:
            log.error("http.request_failed", client=self.name, url=url, error=str(exc))
            raise

    async def get(self, path: str, **kwargs) -> Any: return await self.request("GET", path, **kwargs)
    async def post(self, path: str, **kwargs) -> Any: return await self.request("POST", path, **kwargs)

    @asynccontextmanager
    async def session(self) -> AsyncIterator[aiohttp.ClientSession]:
        yield await self._ensure_session()