from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List
from models.market_data import CandleSeries, OrderBook, Ticker, Trade

class ExchangeClient(ABC):
    name: str = "exchange"
    @abstractmethod
    async def get_candles(self, symbol: str, timeframe: str, limit: int = 300) -> CandleSeries: raise NotImplementedError
    @abstractmethod
    async def get_order_book(self, symbol: str, depth: int = 100) -> OrderBook: raise NotImplementedError
    @abstractmethod
    async def get_ticker(self, symbol: str) -> Ticker: raise NotImplementedError
    @abstractmethod
    async def get_recent_trades(self, symbol: str, limit: int = 500) -> List[Trade]: raise NotImplementedError
    async def close(self) -> None: pass