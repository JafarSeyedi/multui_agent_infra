from __future__ import annotations

from engines.tools.base_executor import BaseToolExecutor, ToolResult
from engines.tools.models.tools_def_models import ArgName, ParameterName, ToolKind
from engines.tools.models.tools_def_models import ToolParameter


@BaseToolExecutor.register(ToolKind.STREAM)
class StreamExecutor(BaseToolExecutor):
    def _apply_params(self) -> None:
        self._backend = self.param(self._params, ParameterName.BACKEND, "memory")
        self._connection = self.param(self._params, ParameterName.CONNECTION, "")
        self._topic = self.param(self._params, ParameterName.TOPIC, "")
        self._backend_instance = None

    async def _storage(self):
        if self._backend_instance is not None:
            return self._backend_instance
        from engines.storage.factories import create_storage
        try:
            if self._connection:
                self._backend_instance = create_storage("stream", backend=self._backend, connection_string=self._connection)
            else:
                self._backend_instance = create_storage("stream", backend=self._backend)
            if not getattr(self._backend_instance, "_connected", False):
                await self._backend_instance.connect()
        except Exception:
            self._backend_instance = None
        return self._backend_instance

    @property
    def name(self) -> str:
        return f"stream:{self._backend}"

    @property
    def description(self) -> str:
        return f"Event stream via {self._backend} backend"

    async def execute(self, args: list[ToolParameter]) -> ToolResult:
        action = self.arg(args, ArgName.ACTION, "publish")
        topic = self.arg(args, ParameterName.TOPIC, self._topic)
        message_str = self.arg(args, ArgName.MESSAGES, "{}")
        group = self.arg(args, ParameterName.GROUP, "default")

        try:
            store = await self._storage()
            if store is None:
                return ToolResult(success=True, data={"topic": topic, "note": "no backend configured"})

            import json
            if action == "publish":
                message = json.loads(message_str) if isinstance(message_str, str) else message_str
                await store.publish(topic, message)
                return ToolResult(success=True, data={"topic": topic, "published": True})
            elif action == "consume":
                messages = await store.consume(topic, group)
                return ToolResult(success=True, data={"topic": topic, "messages": messages})
            return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
