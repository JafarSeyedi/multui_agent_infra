from __future__ import annotations

from engines.tools.base_executor import BaseToolExecutor, ToolResult
from engines.tools.models.tools_def_models import ArgName, ParameterName, ToolKind
from engines.tools.models.tools_def_models import ToolParameter


@BaseToolExecutor.register(ToolKind.CACHE)
class CacheExecutor(BaseToolExecutor):
    def _apply_params(self) -> None:
        self._backend = self.param(self._params, ParameterName.BACKEND, "memory")
        self._connection = self.param(self._params, ParameterName.CONNECTION, "")
        self._backend_instance = None

    async def _storage(self):
        if self._backend_instance is not None:
            return self._backend_instance
        from engines.storage.factories import create_storage
        try:
            if self._connection:
                self._backend_instance = create_storage("cache", backend=self._backend, connection_string=self._connection)
            else:
                self._backend_instance = create_storage("cache", backend=self._backend)
            if not getattr(self._backend_instance, "_connected", False):
                await self._backend_instance.connect()
        except Exception:
            self._backend_instance = None
        return self._backend_instance

    @property
    def name(self) -> str:
        return f"cache:{self._backend}"

    @property
    def description(self) -> str:
        return f"Cache operations via {self._backend} backend"

    async def execute(self, args: list[ToolParameter]) -> ToolResult:
        action = self.arg(args, ArgName.ACTION, "get")
        key = self.arg(args, ArgName.KEY, "")
        value = self.arg(args, ArgName.VALUE, None)
        ttl_str = self.arg(args, ParameterName.TIMEOUT_MS, None)

        try:
            store = await self._storage()
            if store is None:
                return ToolResult(success=True, data={"note": "no backend configured"})

            if action == "get":
                data = await store.get(key)
                return ToolResult(success=True, data={"key": key, "value": data})
            elif action == "set":
                ttl = int(ttl_str) if ttl_str else None
                await store.set(key, value, ttl=ttl)
                return ToolResult(success=True, data={"key": key, "set": True})
            elif action == "delete":
                await store.delete(key)
                return ToolResult(success=True, data={"key": key, "deleted": True})
            elif action == "exists":
                found = await store.exists(key)
                return ToolResult(success=True, data={"key": key, "exists": found})
            elif action == "list_keys":
                keys = await store.list_keys(prefix=key or None)
                return ToolResult(success=True, data={"keys": keys})
            return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
