"""Proxy pattern implementations for the orchestration engine.

Provides surrogate objects that control access to real subjects:
- LazyInitProxy defers storage backend creation until first use
- CachingProxy adds an LRU cache layer over storage backends
- EngineProtectionProxy guards engine execution with authorization checks
"""

from __future__ import annotations

import logging
from collections import OrderedDict
from typing import Any
from collections.abc import Callable

from ..._types import RawData
from .engine_bridge import ProcessEngine, ProcessInstance, ProcessDefinition

logger = logging.getLogger(__name__)


# ── Storage Proxy: Lazy Initialization ─────────────────────────────


class LazyInitProxy:
    """Virtual proxy that defers storage backend creation until first operation.

    The factory callable is invoked once on the first access to any
    StorageBackend method. Useful when backends require configuration
    that may not be available at construction time.
    """

    def __init__(self, factory: Callable[[], Any]) -> None:  # duck-typed
        self._factory = factory
        self._backend: Any | None = None  # duck-typed

    async def _get(self) -> Any:  # duck-typed
        if self._backend is None:
            self._backend = self._factory()
            logger.debug("LazyInitProxy: initialized %s", type(self._backend).__name__)
        return self._backend

    async def save(self, collection: str, key: str, value: RawData) -> None:
        backend = await self._get()
        await backend.save(collection, key, value)

    async def load(self, collection: str, key: str) -> RawData | None:
        backend = await self._get()
        return await backend.load(collection, key)

    async def delete(self, collection: str, key: str) -> None:
        backend = await self._get()
        await backend.delete(collection, key)

    async def list(self, collection: str) -> list[RawData]:
        backend = await self._get()
        return await backend.list(collection)

    async def clear(self, collection: str) -> None:
        backend = await self._get()
        await backend.clear(collection)

    async def __aenter__(self) -> LazyInitProxy:
        return self

    async def __aexit__(self, *args: Any) -> None:
        pass


# ── Storage Proxy: Caching ─────────────────────────────────────────


class CachingProxy:
    """Cache proxy that adds an LRU cache layer over a storage backend.

    Frequently-read items are served from an in-memory OrderedDict cache.
    Writes invalidate the cache for the affected key.
    """

    def __init__(self, wrapped: Any, maxsize: int = 256) -> None:  # duck-typed
        self._wrapped = wrapped  # duck-typed
        self._cache: OrderedDict[str, RawData] = OrderedDict()
        self._maxsize = maxsize

    def _cache_key(self, collection: str, key: str) -> str:
        return f"{collection}:{key}"

    def _cache_get(self, ck: str) -> RawData | None:
        if ck in self._cache:
            self._cache.move_to_end(ck)
            return self._cache[ck]
        return None

    def _cache_set(self, ck: str, value: RawData) -> None:
        self._cache[ck] = value
        self._cache.move_to_end(ck)
        if len(self._cache) > self._maxsize:
            self._cache.popitem(last=False)

    def _cache_invalidate(self, ck: str) -> None:
        self._cache.pop(ck, None)

    def _cache_invalidate_collection(self, collection: str) -> None:
        prefix = f"{collection}:"
        stale = [ck for ck in self._cache if ck.startswith(prefix)]
        for ck in stale:
            self._cache.pop(ck, None)

    async def save(self, collection: str, key: str, value: RawData) -> None:
        await self._wrapped.save(collection, key, value)
        ck = self._cache_key(collection, key)
        self._cache_set(ck, value)

    async def load(self, collection: str, key: str) -> RawData | None:
        ck = self._cache_key(collection, key)
        cached = self._cache_get(ck)
        if cached is not None:
            return cached
        result = await self._wrapped.load(collection, key)
        if result is not None:
            self._cache_set(ck, result)
        return result

    async def delete(self, collection: str, key: str) -> None:
        await self._wrapped.delete(collection, key)
        ck = self._cache_key(collection, key)
        self._cache_invalidate(ck)

    async def list(self, collection: str) -> list[RawData]:
        return await self._wrapped.list(collection)

    async def clear(self, collection: str) -> None:
        await self._wrapped.clear(collection)
        self._cache_invalidate_collection(collection)


# ── Engine Proxy: Access Control ───────────────────────────────────


class EngineProtectionProxy:
    """Protection proxy that checks authorization before delegating engine execution.

    Wraps a ProcessEngine and verifies that the caller (identified by a
    role or principal on the instance) is allowed to perform the requested
    operation.
    """

    def __init__(
        self,
        target: ProcessEngine,
        allowed_roles: set[str] | None = None,
    ) -> None:
        self._target = target
        self._allowed_roles = allowed_roles or {"admin", "operator"}

    async def execute(self, instance: ProcessInstance, definition: ProcessDefinition) -> Any:
        role = self._resolve_role(instance)
        if role not in self._allowed_roles:
            logger.warning("Access denied for role %s on engine %s", role, self.engine_type)
            raise PermissionError(
                f"Role '{role}' is not allowed to execute on engine '{self.engine_type}'"
            )
        return await self._target.execute(instance, definition)

    async def validate(self, definition: ProcessDefinition) -> list[str]:
        return await self._target.validate(definition)

    async def cancel(self, instance_id: str) -> None:
        await self._target.cancel(instance_id)

    async def get_status(self, instance: ProcessInstance) -> str | None:
        return await self._target.get_status(instance)

    @property
    def engine_type(self) -> str:
        return self._target.engine_type

    def set_allowed_roles(self, roles: set[str]) -> None:
        self._allowed_roles = roles

    @staticmethod
    def _resolve_role(instance: ProcessInstance) -> str:
        role = instance.variables.get("role") if hasattr(instance, "variables") else None
        if role and isinstance(role, str):
            return role
        return getattr(instance, "role", "default")
