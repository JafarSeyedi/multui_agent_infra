from __future__ import annotations

from engines.tools.base_executor import BaseToolExecutor
from engines.tools.base_executor import ToolResult
from engines.tools.models.tools_def_models import ArgName
from engines.tools.models.tools_def_models import ParameterName
from engines.tools.models.tools_def_models import ToolKind
from engines.tools.models.tools_def_models import ToolParameter


@BaseToolExecutor.register(ToolKind.MIB_SNMP)
class MIBSNMPExecutor(BaseToolExecutor):

    def _apply_params(self) -> None:
        self._target = self.param(self._params, "target", "")
        self._action = self.param(self._params, ParameterName.ACTION, "get")
        self._oid = self.param(self._params, ParameterName.OID, "")

    @property
    def name(self) -> str:
        return f"snmp:{self._target}"

    @property
    def description(self) -> str:
        return f"SNMP operations against {self._target}"

    async def execute(self, args: list[ToolParameter]) -> ToolResult:
        return ToolResult(True, data={"operation": self._action, "oid": self._oid, "value": None})
