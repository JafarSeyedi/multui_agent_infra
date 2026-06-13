from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


class LazyKnowledgeProxy:
    """Proxy pattern — defers knowledge engine initialization.

    Useful when the engine requires expensive setup (model loading,
    embedding index build, etc.).
    """

    def __init__(self, factory: Callable[..., Any], **factory_kwargs: Any) -> None:
        self._factory = factory
        self._factory_kwargs = factory_kwargs
        self._engine: Any | None = None

    async def _ensure(self) -> Any:
        if self._engine is None:
            self._engine = self._factory(**self._factory_kwargs)
            if hasattr(self._engine, "connect"):
                await self._engine.connect()
        return self._engine

    async def query(self, *args: Any, **kwargs: Any) -> Any:
        engine = await self._ensure()
        if hasattr(engine, "query"):
            return await engine.query(*args, **kwargs)
        raise AttributeError(f"Engine {type(engine).__name__!r} has no query method")

    async def search(self, *args: Any, **kwargs: Any) -> Any:
        engine = await self._ensure()
        if hasattr(engine, "search"):
            return await engine.search(*args, **kwargs)
        raise AttributeError(f"Engine {type(engine).__name__!r} has no search method")

    async def ingest(self, *args: Any, **kwargs: Any) -> Any:
        engine = await self._ensure()
        if hasattr(engine, "ingest"):
            return await engine.ingest(*args, **kwargs)
        raise AttributeError(f"Engine {type(engine).__name__!r} has no ingest method")

    @property
    def is_initialized(self) -> bool:
        return self._engine is not None


class KnowledgeMediator:
    """Mediator pattern — coordinates RAG, graph, and ML mining engines.

    Centralizes query routing: determines which engine(s) to invoke
    based on query type, merges results, and handles fallbacks.
    """

    def __init__(self) -> None:
        self._engines: dict[str, Any] = {}

    def register(self, name: str, engine: Any) -> None:
        self._engines[name] = engine

    def unregister(self, name: str) -> None:
        self._engines.pop(name, None)

    def get(self, name: str) -> Any:
        return self._engines.get(name)

    async def query_all(self, query: str, **kwargs: Any) -> dict[str, Any]:
        results: dict[str, Any] = {}
        for name, engine in self._engines.items():
            try:
                if hasattr(engine, "query"):
                    results[name] = await engine.query(query, **kwargs)
                elif hasattr(engine, "search"):
                    results[name] = await engine.search(query, **kwargs)
            except Exception as exc:
                logger.warning("Knowledge engine '%s' failed: %s", name, exc)
                results[name] = {"error": str(exc)}
        return results

    async def query_best(self, query: str, **kwargs: Any) -> Any:
        for name, engine in self._engines.items():
            try:
                if hasattr(engine, "search"):
                    result = await engine.search(query, **kwargs)
                    if result:
                        return result
            except Exception:
                continue
        return None
