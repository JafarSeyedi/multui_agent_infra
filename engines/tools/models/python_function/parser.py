from __future__ import annotations

from engines.tools.models.core.core_models import ToolKind
from engines.tools.models.core.core_models import ToolParameter
from engines.tools.models.core.core_models import ParameterSource
from engines.tools.models.core.core_models import ParameterType
from engines.tools.models.core.core_models import ToolOutput
from engines.tools.models.python_function.python_function_models import PythonFunctionTool


def parse_python_function_tool(data: dict) -> PythonFunctionTool:
    return PythonFunctionTool(
        id=data.get("id", ""),
        name=data.get("name", ""),
        description=data.get("description"),
        version=data.get("version", "1.0.0"),
        kind=ToolKind.PYTHON_FUNCTION,
        parameters=[_parse_param(p) for p in data.get("parameters", [])],
        outputs=[_parse_output(o) for o in data.get("outputs", [])],
        tags=data.get("tags", []),
        annotations=data.get("annotations", {}),
        retry_policy=data.get("retry_policy"),
        timeout_ms=data.get("timeout_ms", 30000),
        module_path=data.get("module_path", ""),
        function_name=data.get("function_name", ""),
        import_type=data.get("import_type", "direct"),
    )


def _parse_param(p: dict) -> ToolParameter:
    return ToolParameter(
        name=p.get("name", ""),
        type=ParameterType(p.get("type", "string")),
        required=p.get("required", False),
        default=p.get("default"),
        description=p.get("description"),
        source=ParameterSource(p.get("source", "callerArg")),
        source_path=p.get("source_path"),
        mapping_target=p.get("mapping_target"),
    )


def _parse_output(o: dict) -> ToolOutput:
    return ToolOutput(
        name=o.get("name", ""),
        type=ParameterType(o.get("type", "json")),
        description=o.get("description"),
        mapping_from=o.get("mapping_from"),
    )
