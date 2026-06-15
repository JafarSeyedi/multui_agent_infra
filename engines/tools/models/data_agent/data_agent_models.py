from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from engines.tools.models.core.core_models import Tool


@dataclass
class DataAgentTool(Tool):
    kind: str = "data_agent"
    query: str = ""
    data_source: str = ""
    agent_id: str = ""
