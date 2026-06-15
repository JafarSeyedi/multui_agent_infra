from __future__ import annotations

from typing import Any

from engines.tools.base_executor import BaseToolExecutor
from engines.tools.base_executor import ToolResult


class AIModelExecutor(BaseToolExecutor):
    """Executes AI model inference (LLM, embedding, etc.)."""

    def __init__(self, model_name: str = "default", gateway=None) -> None:
        super().__init__()
        self._model_name = model_name
        self._gateway = gateway

    @property
    def name(self) -> str:
        return f"ai_model:{self._model_name}"

    @property
    def description(self) -> str:
        return f"AI model inference using {self._model_name}"

    async def execute(self, **kwargs: Any) -> ToolResult:
        if self._gateway is not None:
            try:
                result = await self._gateway.route(
                    model=kwargs.get("model", self._model_name),
                    prompt=kwargs.get("prompt", ""),
                    **{k: v for k, v in kwargs.items() if k not in ("model", "prompt")},
                )
                return ToolResult(success=True, data={"text": result.text, "model": result.model, "cost": result.cost})
            except Exception as e:
                return ToolResult(success=False, error=f"Gateway error: {e}")
        prompt = kwargs.get("prompt", "")
        return ToolResult(True, data={"model": self._model_name, "response": f"Echo: {prompt}"})


AiModelToolExecutor = AIModelExecutor
