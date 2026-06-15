from __future__ import annotations

from engines.tools.models.core.core_models import ToolKind
from engines.tools.models.core.core_models import ToolParameter
from engines.tools.models.core.core_models import ParameterSource
from engines.tools.models.core.core_models import ParameterType
from engines.tools.models.core.core_models import ToolOutput
from engines.tools.models.ai_model.ai_model_models import AiModelTool


def parse_ai_model_tool(data: dict) -> AiModelTool:
    common = _common_fields(data)
    return AiModelTool(
        **common,
        endpoint_url=data.get("endpoint_url", ""),
        model_name=data.get("model_name", ""),
        prompt_template=data.get("prompt_template", ""),
        api_key_env=data.get("api_key_env", ""),
        temperature=data.get("temperature", 0.7),
        max_tokens=data.get("max_tokens", 1024),
        extra_params=data.get("extra_params", {}),
    )


def _common_fields(data: dict) -> dict:
    return {
        "id": data.get("id", ""),
        "name": data.get("name", ""),
        "description": data.get("description"),
        "version": data.get("version", "1.0.0"),
        "kind": ToolKind(data.get("kind", "aiModel")),
        "parameters": [_parse_param(p) for p in data.get("parameters", [])],
        "outputs": [_parse_output(o) for o in data.get("outputs", [])],
        "tags": data.get("tags", []),
        "annotations": data.get("annotations", {}),
        "retry_policy": data.get("retry_policy"),
        "timeout_ms": data.get("timeout_ms", 30000),
    }


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
