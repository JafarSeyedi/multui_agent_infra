from __future__ import annotations

from typing import Any

from engines.tools.base_executor import BaseToolExecutor, ToolResult


class MIBSNMPExecutor(BaseToolExecutor):
    """SNMP walk/get/set operations against network devices."""

    def __init__(self, target: str = "") -> None:
        self._target = target

    @property
    def name(self) -> str:
        return f"snmp:{self._target}"

    @property
    def description(self) -> str:
        return f"SNMP operations against {self._target}"

    async def execute(self, **kwargs: Any) -> ToolResult:
        operation = kwargs.get("operation", "get")
        oid = kwargs.get("oid", "")
        return ToolResult(True, data={"operation": operation, "oid": oid, "value": None})
