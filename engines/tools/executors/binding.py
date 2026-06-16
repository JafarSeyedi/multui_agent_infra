from __future__ import annotations

from engines.tools.base_executor import BaseToolExecutor, ToolResult
from engines.tools.models.tools_def_models import ArgName, ParameterName, ToolKind
from engines.tools.models.tools_def_models import ToolParameter


@BaseToolExecutor.register(ToolKind.BINDING)
class BindingExecutor(BaseToolExecutor):
    def _apply_params(self) -> None:
        self._format = self.param(self._params, ParameterName.FORMAT, "auto")

    @property
    def name(self) -> str:
        return "binding"

    @property
    def description(self) -> str:
        return "Parse and serialize SSDM service bindings"

    async def execute(self, args: list[ToolParameter]) -> ToolResult:
        import json as _json

        action = self.arg(args, ArgName.ACTION, "parse")
        data_str = self.arg(args, ArgName.DATA, "{}")
        output_format = self.arg(args, ParameterName.FORMAT, "yaml")

        try:
            from engines.communication import BindingParser, BindingWriter
            from engines.communication.bindings.binding_parser import parse_bindings

            if action == "parse":
                data = _json.loads(data_str) if isinstance(data_str, str) else data_str
                bindings = parse_bindings(data)
                serialized = [b.__dict__ for b in bindings]
                return ToolResult(success=True, data={"bindings": serialized})
            elif action == "parse_file":
                from pathlib import Path
                path = Path(data_str)
                bindings = BindingParser.parse_service_bindings_file(path)
                serialized = [b.__dict__ for b in bindings]
                return ToolResult(success=True, data={"bindings": serialized})
            elif action == "write":
                data = _json.loads(data_str) if isinstance(data_str, str) else data_str
                bindings = parse_bindings(data)
                writer = BindingWriter()
                raw = writer.write(bindings, output_format=output_format)
                return ToolResult(success=True, data={"output": raw.decode("utf-8"), "format": output_format})
            return ToolResult(success=False, error=f"Unknown action: {action}")
        except ImportError as e:
            return ToolResult(success=False, error=f"Missing dependency: {e}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
