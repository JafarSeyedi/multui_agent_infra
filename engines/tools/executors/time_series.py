from __future__ import annotations

from datetime import datetime

from engines.tools.base_executor import BaseToolExecutor, ToolResult
from engines.tools.models.tools_def_models import ArgName, ParameterName, ToolKind
from engines.tools.models.tools_def_models import ToolParameter


@BaseToolExecutor.register(ToolKind.TIME_SERIES)
class TimeSeriesExecutor(BaseToolExecutor):
    def _apply_params(self) -> None:
        self._backend = self.param(self._params, ParameterName.BACKEND, "influx")
        self._connection = self.param(self._params, ParameterName.CONNECTION, "")
        self._backend_instance = None

    async def _storage(self):
        if self._backend_instance is not None:
            return self._backend_instance
        from engines.storage.factories import create_storage
        try:
            if self._connection:
                self._backend_instance = create_storage("timeseries", backend=self._backend, url=self._connection)
            else:
                self._backend_instance = create_storage("timeseries", backend=self._backend)
            if not getattr(self._backend_instance, "_connected", False):
                await self._backend_instance.connect()
        except Exception:
            self._backend_instance = None
        return self._backend_instance

    @property
    def name(self) -> str:
        return f"timeseries:{self._backend}"

    @property
    def description(self) -> str:
        return f"Time-series storage via {self._backend} backend"

    async def execute(self, args: list[ToolParameter]) -> ToolResult:
        action = self.arg(args, ArgName.ACTION, "query")
        measurement = self.arg(args, ParameterName.MEASUREMENT, "")
        fields_str = self.arg(args, ParameterName.FIELDS, "{}")
        tags_str = self.arg(args, ParameterName.TAGS, "{}")
        start_str = self.arg(args, ParameterName.START, "")
        end_str = self.arg(args, ParameterName.END, "")

        try:
            store = await self._storage()
            if store is None:
                return ToolResult(success=True, data={"note": "no backend configured"})

            import json
            if action == "write":
                fields = json.loads(fields_str) if isinstance(fields_str, str) else fields_str
                tags = json.loads(tags_str) if isinstance(tags_str, str) else tags_str
                await store.write(measurement, datetime.utcnow(), fields, tags=tags or None)
                return ToolResult(success=True, data={"measurement": measurement, "written": True})
            elif action == "query":
                start = datetime.fromisoformat(start_str) if start_str else datetime(2000, 1, 1)
                end = datetime.fromisoformat(end_str) if end_str else datetime.utcnow()
                rows = await store.query(measurement, start, end)
                return ToolResult(success=True, data={"rows": rows})
            return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
