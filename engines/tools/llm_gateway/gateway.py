from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ModelResult:
    text: str
    model: str
    cost: float = 0.0
    tokens_input: int = 0
    tokens_output: int = 0
    latency_ms: float = 0.0
    cached: bool = False


class LLMGateway:
    def __init__(self, cache_ttl_s: int = 3600):
        self._backends: dict[str, Any] = {}
        self._default_backend: str = ""
        self._cache: dict[str, ModelResult] = {}
        self._cache_ttl = cache_ttl_s

    def register_backend(self, name: str, backend: Any, set_default: bool = False) -> None:
        self._backends[name] = backend
        if set_default or not self._default_backend:
            self._default_backend = name

    async def route(
        self,
        model: str,
        prompt: str,
        backend: str = "",
        use_cache: bool = True,
        **kwargs: Any,
    ) -> ModelResult:
        backend_name = backend or self._default_backend
        if not backend_name or backend_name not in self._backends:
            raise RuntimeError(f"No LLM gateway backend available (tried: '{backend_name}')")

        cache_key = self._cache_key(model, prompt, kwargs)
        if use_cache and cache_key in self._cache:
            cached = self._cache[cache_key]
            if time.time() - cached.latency_ms < self._cache_ttl:
                return ModelResult(text=cached.text, model=model, cached=True)

        start = time.time()
        result = await self._backends[backend_name].route(model, prompt, **kwargs)
        elapsed = (time.time() - start) * 1000

        mr = ModelResult(
            text=result.get("text", ""),
            model=model,
            cost=result.get("cost", 0.0),
            tokens_input=result.get("tokens_input", 0),
            tokens_output=result.get("tokens_output", 0),
            latency_ms=elapsed,
        )
        if use_cache:
            self._cache[cache_key] = mr
        return mr

    async def get_cost(self, model: str, backend: str = "") -> float:
        backend_name = backend or self._default_backend
        if backend_name and backend_name in self._backends:
            return await self._backends[backend_name].get_cost(model)
        return 0.0

    def clear_cache(self) -> int:
        count = len(self._cache)
        self._cache.clear()
        return count

    def _cache_key(self, model: str, prompt: str, kwargs: dict) -> str:
        raw = f"{model}:{prompt}:{sorted(kwargs.items())}"
        return hashlib.sha256(raw.encode()).hexdigest()
