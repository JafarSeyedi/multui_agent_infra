from __future__ import annotations

from .computer_use_models import ComputerUseTool


def parse_computer_use_tool(data: dict) -> ComputerUseTool:
    return ComputerUseTool(**{k: v for k, v in data.items() if k in ComputerUseTool.__dataclass_fields__})
