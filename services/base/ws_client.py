from __future__ import annotations
import asyncio
import json
from typing import Any, AsyncIterator, Callable, Optional
import websockets
from websockets.asyncio.client import connect
from config.logging import get_logger
log = get_logger(__name__)

class WebSocketClient:
    def __init__(self, url: str, *, on_message: Optional[Callable[[dict], Any]] = None, ping_interval: float = 20.0, reconnect_backoff_base: float = 1.0, max_reconnect_attempts: int = 10) -> None:
        self.url = url; self.on_message = on_message; self.ping_interval = ping_interval
        self.reconnect_backoff_base = reconnect_backoff_base; self.max_reconnect_attempts = max_reconnect_attempts
        self._stop = asyncio.Event()

    async def stream(self) -> AsyncIterator[dict]:
        attempt = 0
        while not self._stop.is_set():
            try:
                async with connect(self.url, ping_interval=self.ping_interval, ping_timeout=self.ping_interval * 2, close_timeout=5) as ws:
                    attempt = 0
                    async for raw in ws:
                        if self._stop.is_set(): break
                        try: msg = json.loads(raw)
                        except json.JSONDecodeError: log.warning("ws.invalid_json", url=self.url); continue
                        if self.on_message:
                            try: self.on_message(msg)
                            except Exception: log.exception("ws.on_message_error", url=self.url)
                        yield msg
            except Exception as exc:
                if self._stop.is_set(): break
                attempt += 1
                if attempt > self.max_reconnect_attempts: log.error("ws.max_reconnects_exceeded", url=self.url, error=str(exc)); raise
                delay = min(self.reconnect_backoff_base * (2 ** attempt), 30.0)
                log.warning("ws.reconnecting", url=self.url, attempt=attempt, delay=delay)
                await asyncio.sleep(delay)

    def stop(self) -> None: self._stop.set()