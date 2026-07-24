from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any

class BaseEngine(ABC):
    name: str = "base_engine"
    @abstractmethod
    async def analyze(self, *args: Any, **kwargs: Any) -> Any: raise NotImplementedError