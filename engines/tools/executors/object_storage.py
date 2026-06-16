from __future__ import annotations

from engines.tools.base_executor import BaseToolExecutor, ToolResult
from engines.tools.models.tools_def_models import ArgName, ParameterName, ToolKind
from engines.tools.models.tools_def_models import ToolParameter


@BaseToolExecutor.register(ToolKind.OBJECT_STORAGE)
class ObjectStorageExecutor(BaseToolExecutor):
    def _apply_params(self) -> None:
        self._backend = self.param(self._params, ParameterName.BACKEND, "filesystem")
        self._connection = self.param(self._params, ParameterName.CONNECTION, "")
        self._backend_instance = None

    async def _storage(self):
        if self._backend_instance is not None:
            return self._backend_instance
        from engines.storage.factories import create_storage
        try:
            if self._connection:
                self._backend_instance = create_storage("object", backend=self._backend, base_path=self._connection)
            else:
                self._backend_instance = create_storage("object", backend=self._backend)
            if not getattr(self._backend_instance, "_connected", False):
                await self._backend_instance.connect()
        except Exception:
            self._backend_instance = None
        return self._backend_instance

    @property
    def name(self) -> str:
        return f"object_store:{self._backend}"

    @property
    def description(self) -> str:
        return f"Object storage via {self._backend} backend"

    async def execute(self, args: list[ToolParameter]) -> ToolResult:
        action = self.arg(args, ArgName.ACTION, "get")
        key = self.arg(args, ArgName.KEY, "")
        value = self.arg(args, ArgName.VALUE, None)
        content_type = self.arg(args, ParameterName.CONTENT_TYPE, None)

        try:
            store = await self._storage()
            if store is None:
                return ToolResult(success=True, data={"note": "no backend configured"})
            if action == "get":
                exists = await store.exists(key)
                if not exists:
                    return ToolResult(success=True, data={"key": key, "exists": False, "data": None})
                data = await store.get(key)
                return ToolResult(success=True, data={"key": key, "exists": True, "data": data})
            elif action == "put":
                raw = value.encode() if isinstance(value, str) else (value or b"")
                await store.put(key, raw, content_type=content_type)
                return ToolResult(success=True, data={"key": key, "put": True})
            elif action == "delete":
                await store.delete(key)
                return ToolResult(success=True, data={"key": key, "deleted": True})
            elif action == "exists":
                found = await store.exists(key)
                return ToolResult(success=True, data={"key": key, "exists": found})
            elif action == "generate_url":
                url = await store.generate_url(key)
                return ToolResult(success=True, data={"key": key, "url": url})
            return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
