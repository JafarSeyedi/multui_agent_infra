from __future__ import annotations

from engines.tools.base_executor import BaseToolExecutor, ToolResult
from engines.tools.models.tools_def_models import ArgName, ParameterName, ToolKind
from engines.tools.models.tools_def_models import ToolParameter


@BaseToolExecutor.register(ToolKind.FILE_WRITE)
@BaseToolExecutor.register(ToolKind.FILE_READ)
class FileExecutor(BaseToolExecutor):
    def _apply_params(self) -> None:
        self._file_path = self.param(self._params, ParameterName.FILE_PATH, "")
        self._action = self.param(self._params, ParameterName.ACTION, "read")
        self._backend_instance = None

    def _storage(self):
        if self._backend_instance is not None:
            return self._backend_instance
        from engines.storage.factories import create_storage
        self._backend_instance = create_storage("object", backend="filesystem", base_path="/")
        return self._backend_instance

    @property
    def name(self) -> str:
        return "file"

    @property
    def description(self) -> str:
        return "Read or write files on the local filesystem"

    async def execute(self, args: list[ToolParameter]) -> ToolResult:
        import os
        path_input = self.arg(args, ArgName.INPUT, "")
        content = self.arg(args, ArgName.CONTENT, "")
        action = self.arg(args, ArgName.ACTION, self._action)

        target = path_input or self._file_path
        target = target.lstrip("/")

        try:
            store = self._storage()
            if action == "write":
                raw = content.encode() if isinstance(content, str) else b""
                await store.put(target, raw)
                return ToolResult(success=True, data={"path": target, "written": len(raw)})
            else:
                exists = await store.exists(target)
                if not exists:
                    return ToolResult(success=True, data={"path": target, "content": ""})
                data = await store.get(target)
                decoded = data.decode() if isinstance(data, bytes) else str(data or "")
                return ToolResult(success=True, data={"path": target, "content": decoded})
        except Exception as e:
            return ToolResult(success=False, error=str(e))
