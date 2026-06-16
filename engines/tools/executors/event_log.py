from __future__ import annotations

from engines.tools.base_executor import BaseToolExecutor, ToolResult
from engines.tools.models.tools_def_models import ArgName, ParameterName, ToolKind
from engines.tools.models.tools_def_models import ToolParameter


@BaseToolExecutor.register(ToolKind.EVENT_LOG)
class EventLogExecutor(BaseToolExecutor):
    def _apply_params(self) -> None:
        self._backend = self.param(self._params, ParameterName.BACKEND, "sql")
        self._connection = self.param(self._params, ParameterName.CONNECTION, "")
        self._backend_instance = None

    async def _storage(self):
        if self._backend_instance is not None:
            return self._backend_instance
        from engines.storage.event_log.backends.sql_event_log import SqlLogStorage
        try:
            if self._backend == "rsyslog":
                from engines.storage.event_log.backends.rsyslog import RSyslogStorage
                self._backend_instance = RSyslogStorage(server=self._connection or "localhost")
            else:
                from engines.storage.relational.base import SQLStorage
                sql_store = SQLStorage(db_path=":memory:")
                await sql_store.connect()
                self._backend_instance = SqlLogStorage(sql_storage=sql_store)
                await self._backend_instance.connect()
        except Exception:
            self._backend_instance = None
        return self._backend_instance

    @property
    def name(self) -> str:
        return f"event_log:{self._backend}"

    @property
    def description(self) -> str:
        return f"Event log via {self._backend} backend"

    async def execute(self, args: list[ToolParameter]) -> ToolResult:
        action = self.arg(args, ArgName.ACTION, "log_event")
        agent_name = self.arg(args, ParameterName.AGENT_ID, "")
        event_type = self.arg(args, ParameterName.EVENT_TYPE, "general")
        payload_str = self.arg(args, ArgName.PAYLOAD, "{}")
        key = self.arg(args, ArgName.KEY, "")

        try:
            store = await self._storage()
            if store is None:
                return ToolResult(success=True, data={"note": "no backend configured"})

            import json
            payload = json.loads(payload_str) if isinstance(payload_str, str) else payload_str

            if action == "log_event":
                await store.log_event(event_type, payload)
                return ToolResult(success=True, data={"event_type": event_type, "logged": True})
            elif action == "list_events":
                keys = await store.list_events(event_type=event_type or None)
                return ToolResult(success=True, data={"keys": keys})
            elif action == "get_event":
                event = await store.get_event(key)
                return ToolResult(success=True, data={"event": event})
            elif action == "log_agent_execution":
                await store.log_agent_execution(agent_name, payload)
                return ToolResult(success=True, data={"agent": agent_name, "logged": True})
            elif action == "list_agent_logs":
                keys = await store.list_agent_logs(agent_name)
                return ToolResult(success=True, data={"keys": keys})
            elif action == "get_agent_log":
                log = await store.get_agent_log(key)
                return ToolResult(success=True, data={"log": log})
            return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
