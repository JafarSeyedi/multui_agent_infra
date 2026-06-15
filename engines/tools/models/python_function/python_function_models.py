from __future__ import annotations

from dataclasses import dataclass

from engines.tools.models.core.core_models import Tool
from engines.tools.models.core.core_models import ToolKind


@dataclass
class PythonFunctionTool(Tool):
    kind: ToolKind = ToolKind.PYTHON_FUNCTION
    module_path: str = ""
    function_name: str = ""
    import_type: str = "direct"
