from __future__ import annotations
import asyncio
import functools
import random
from dataclasses import dataclass
from typing import Awaitable, Callable, Tuple, Type, TypeVar
T = TypeVar("T")

@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 4; base_delay: float = 0.8; max_delay: float = 8.0; jitter: float = 0.25; retry_on: Tuple[Type[BaseException], ...] = (Exception,)
    def delay_for(self, attempt: int) -> float:
        raw = self.base_delay * (2 ** (attempt - 1))
        capped = min(raw, self.max_delay)
        jitter = random.uniform(0, self.jitter) * capped
        return capped * (1 - self.jitter / 2) + jitter

DEFAULT_POLICY = RetryPolicy()

async def retry_async(func: Callable[..., Awaitable[T]], *args, policy: RetryPolicy = DEFAULT_POLICY, **kwargs) -> T:
    last_exc: Exception | None = None
    for attempt in range(1, policy.max_attempts + 1):
        try: return await func(*args, **kwargs)
        except policy.retry_on as exc:
            last_exc = exc
            if attempt >= policy.max_attempts: break
            await asyncio.sleep(policy.delay_for(attempt))
    assert last_exc is not None
    raise last_exc

def with_retry(policy: RetryPolicy = DEFAULT_POLICY):
    def decorator(fn: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs) -> T: return await retry_async(fn, *args, policy=policy, **kwargs)
        return wrapper
    return decorator