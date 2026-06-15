from __future__ import annotations

from dataclasses import dataclass

from engines.tools.models.core.core_models import Tool
from engines.tools.models.core.core_models import ToolKind


@dataclass
class FileReadTool(Tool):
    kind: ToolKind = ToolKind.FILE_READ
    file_path_template: str = ""
    encoding: str = "utf-8"


@dataclass
class FileWriteTool(Tool):
    kind: ToolKind = ToolKind.FILE_WRITE
    file_path_template: str = ""
    content_template: str = ""
    encoding: str = "utf-8"
