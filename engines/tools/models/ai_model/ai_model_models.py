from __future__ import annotations

from dataclasses import dataclass, field

from engines.tools.models.core.core_models import Tool
from engines.tools.models.core.core_models import ToolKind


@dataclass
class AiModelTool(Tool):
    kind: ToolKind = ToolKind.AI_MODEL
    endpoint_url: str = ""
    model_name: str = ""
    prompt_template: str = ""
    api_key_env: str = ""
    temperature: float = 0.7
    max_tokens: int = 1024
    extra_params: dict[str, str] = field(default_factory=dict)
