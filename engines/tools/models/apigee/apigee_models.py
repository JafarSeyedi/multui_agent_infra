from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from engines.tools.models.core.core_models import Tool


@dataclass
class ApigeeTool(Tool):
    kind: str = "apigee"
    api_hub_url: str = ""
    action: str = "search"
    query: str = ""
    api_id: str = ""
