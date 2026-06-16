from __future__ import annotations

from engines.tools.base_executor import BaseToolExecutor, ToolResult
from engines.tools.models.tools_def_models import ArgName, ParameterName, ToolKind
from engines.tools.models.tools_def_models import ToolParameter


@BaseToolExecutor.register(ToolKind.SERVICE_DISCOVERY)
class ServiceDiscoveryExecutor(BaseToolExecutor):
    def _apply_params(self) -> None:
        self._discovery = None

    def _get_discovery(self):
        if self._discovery is not None:
            return self._discovery
        from engines.communication import ServiceDiscovery
        self._discovery = ServiceDiscovery()
        return self._discovery

    @property
    def name(self) -> str:
        return "service_discovery"

    @property
    def description(self) -> str:
        return "Resolve service endpoints via discovery backends"

    async def execute(self, args: list[ToolParameter]) -> ToolResult:
        operation_id = self.arg(args, ArgName.OPERATION, "")
        endpoint = self.arg(args, ParameterName.URL, "")

        try:
            discovery = self._get_discovery()
            result = discovery.resolve(operation_id, binding_endpoint=endpoint or None)
            return ToolResult(success=True, data={
                "target": result.target,
                "targets": result.targets,
                "source": result.source,
            })
        except ImportError as e:
            return ToolResult(success=False, error=f"Missing dependency: {e}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
