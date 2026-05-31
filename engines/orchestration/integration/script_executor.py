"""Script executor for BPMN script tasks.

Supports safe, auditable script execution with typed inputs/outputs.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ...core.instance import ProcessInstance


logger = logging.getLogger(__name__)


class ScriptLanguage(str, Enum):
    FEEL = "FEEL"
    PYTHON = "Python"
    JAVASCRIPT = "JavaScript"
    GROOVY = "Groovy"


@dataclass
class ScriptResult:
    success: bool = True
    result: Any = None
    duration_ms: float = 0.0
    output_variables: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class ScriptExecutionError(RuntimeError):
    pass


class ScriptExecutor:
    ALLOWED_BUILTINS = {
        "len": len, "str": str, "int": int, "float": float, "bool": bool,
        "list": list, "dict": dict, "abs": abs, "min": min, "max": max,
        "round": round, "sorted": sorted, "reversed": reversed,
        "enumerate": enumerate, "zip": zip, "map": map, "filter": filter,
        "any": any, "all": all, "sum": sum,
    }

    def __init__(self) -> None:
        self._scripts: dict[str, str] = {}
        self._execution_log: list[dict[str, Any]] = []

    def register(self, script_id: str, script: str, language: str = "FEEL") -> None:
        self._scripts[script_id] = script

    async def execute(
        self,
        script: str,
        context: dict[str, Any],
        result_variable: str | None = None,
        instance: ProcessInstance | None = None,
        language: str = "FEEL",
        timeout_seconds: int = 30,
    ) -> ScriptResult:
        start_time = time.time()

        try:
            result = self._evaluate(script, context, language)
            duration = (time.time() - start_time) * 1000

            output_vars: dict[str, Any] = {}
            if result_variable and result is not None:
                output_vars[result_variable] = result
                if instance:
                    instance.set_variable(result_variable, result)

            script_result = ScriptResult(
                success=True,
                result=result,
                duration_ms=duration,
                output_variables=output_vars,
            )

            self._log_execution(script, language, duration, None)
            return script_result

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self._log_execution(script, language, duration, str(e))
            return ScriptResult(
                success=False,
                duration_ms=duration,
                error=str(e),
            )

    def _evaluate(self, script: str, context: dict[str, Any], language: str) -> Any:
        if language == "FEEL":
            from ...dmn.feel_engine import FEELEngine
            return FEELEngine().evaluate(script, context)
        else:
            safe_globals = {"__builtins__": self.ALLOWED_BUILTINS}
            local_vars = dict(context)
            return eval(script, safe_globals, local_vars)

    def _log_execution(self, script: str, language: str, duration: float, error: str | None) -> None:
        self._execution_log.append({
            "language": language,
            "duration_ms": duration,
            "error": error,
        })

    def get_execution_log(self) -> list[dict[str, Any]]:
        return list(self._execution_log)

    def clear_execution_log(self) -> int:
        count = len(self._execution_log)
        self._execution_log.clear()
        return count
