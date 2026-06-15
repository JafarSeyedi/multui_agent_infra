from __future__ import annotations

from typing import Any

from .litellm_models import LiteLLMTool


def parse_litellm_tool(data: dict[str, Any]) -> LiteLLMTool:
    return LiteLLMTool(
        id=data.get("id", ""),
        name=data.get("name", "litellm"),
        description=data.get("description", ""),
        model=data.get("model", "gpt-4o-mini"),
        messages=data.get("messages", []),
        temperature=data.get("temperature", 0.7),
        max_tokens=data.get("max_tokens"),
        extra_kwargs=data.get("extra_kwargs", {}),
        parameters=data.get("parameters", []),
        outputs=data.get("outputs", []),
        tags=data.get("tags", []),
        annotations=data.get("annotations", {}),
    )
