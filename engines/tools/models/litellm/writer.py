from __future__ import annotations

from typing import Any

from .litellm_models import LiteLLMTool


def write_litellm_tool(tool: LiteLLMTool) -> dict[str, Any]:
    return {
        "id": tool.id,
        "name": tool.name,
        "description": tool.description,
        "kind": tool.kind.value,
        "model": tool.model,
        "messages": tool.messages,
        "temperature": tool.temperature,
        "max_tokens": tool.max_tokens,
        "extra_kwargs": tool.extra_kwargs,
        "parameters": [
            {"name": p.name, "type": p.type.value, "required": p.required}
            for p in tool.parameters
        ],
        "outputs": [
            {"name": o.name, "type": o.type.value}
            for o in tool.outputs
        ],
        "tags": tool.tags,
        "annotations": tool.annotations,
    }
