from __future__ import annotations

from .computer_use_models import ComputerUseTool


def write_computer_use_tool(tool: ComputerUseTool) -> dict:
    return {k: getattr(tool, k) for k in tool.__dataclass_fields__}
