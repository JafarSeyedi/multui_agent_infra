# engines/document/ingestion/utils/retry_policy.py
from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any


class RetryPolicy:
    """
    Generic async retry wrapper.
    Supports:
        - exponential backoff
        - jitter
        - retry-on-exception types
    """

    def __init__(
        self,
        *,
        retries: int = 3,
        backoff: float = 0.5,
        max_backoff: float = 8.0,
        retry_exceptions: tuple[type[BaseException], ...] = (Exception,),
        jitter: float = 0.1,
    ):
        self.retries = retries
        self.backoff = backoff
        self.max_backoff = max_backoff
        self.retry_exceptions = retry_exceptions
        self.jitter = jitter

    # ------------------------------------------------------------------
    async def run(self, fn: Callable, *args, **kwargs) -> Any:
        delay = self.backoff

        for attempt in range(self.retries + 1):
            try:
                return await fn(*args, **kwargs)
            except self.retry_exceptions:
                if attempt >= self.retries:
                    raise

                jitter = (self.jitter * delay)
                await asyncio.sleep(min(delay + jitter, self.max_backoff))
                delay = min(delay * 2, self.max_backoff)
