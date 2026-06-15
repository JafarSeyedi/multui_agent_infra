from __future__ import annotations

from dataclasses import dataclass

from engines.tools.models.core.core_models import Tool
from engines.tools.models.core.core_models import ToolKind


@dataclass
class DbQueryTool(Tool):
    kind: ToolKind = ToolKind.DB_QUERY
    connection_string: str = ""
    query_template: str = ""


@dataclass
class DbStatementTool(Tool):
    kind: ToolKind = ToolKind.DB_STATEMENT
    connection_string: str = ""
    statement_template: str = ""
