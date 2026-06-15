from __future__ import annotations

from typing import Any

from engines.tools.base_executor import BaseToolExecutor
from engines.tools.base_executor import ToolResult


class AIModelExecutor(BaseToolExecutor):
    """Executes AI model inference (LLM, embedding, etc.)."""

    def __init__(self, model_name: str = "default") -> None:
        self._model_name = model_name

    @property
    def name(self) -> str:
        return f"ai_model:{self._model_name}"

    @property
    def description(self) -> str:
        return f"AI model inference using {self._model_name}"

    async def execute(self, **kwargs: Any) -> ToolResult:
        prompt = kwargs.get("prompt", "")
        return ToolResult(True, data={"model": self._model_name, "response": f"Echo: {prompt}"})
