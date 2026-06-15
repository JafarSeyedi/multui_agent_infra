from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from engines.tools.models.core.core_models import Tool, ToolKind


@dataclass
class LiteLLMTool(Tool):
    kind: ToolKind = ToolKind.AI_MODEL
    model: str = "gpt-4o-mini"
    messages: list[dict[str, str]] = field(default_factory=list)
    temperature: float = 0.7
    max_tokens: int | None = None
    extra_kwargs: dict[str, Any] = field(default_factory=dict)
