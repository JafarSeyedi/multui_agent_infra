from __future__ import annotations

from engines.tools.base_executor import BaseToolExecutor
from engines.tools.base_executor import ToolResult
from engines.tools.models.tools_def_models import ArgName, ParameterName, ToolKind
from engines.tools.models.tools_def_models import ToolParameter


@BaseToolExecutor.register(ToolKind.AI_MODEL)
class AIModelExecutor(BaseToolExecutor):
    """Executes AI model inference (LLM, embedding, etc.)."""

    def __init__(self, params: list[ToolParameter] | None = None, gateway=None) -> None:
        super().__init__(params)
        self._gateway = gateway

    def _apply_params(self) -> None:
        self._model_name = self.param(self._params, ParameterName.MODEL, "default")

    @property
    def name(self) -> str:
        return f"ai_model:{self._model_name}"

    @property
    def description(self) -> str:
        return f"AI model inference using {self._model_name}"

    async def execute(self, args: list[ToolParameter]) -> ToolResult:
        if self._gateway is not None:
            try:
                result = await self._gateway.route(
                    model=self.arg(args, ParameterName.MODEL, self._model_name),
                    prompt=self.arg(args, ArgName.INPUT, ""),
                )
                return ToolResult(success=True, data={"text": result.text, "model": result.model, "cost": result.cost})
            except Exception as e:
                return ToolResult(success=False, error=f"Gateway error: {e}")
        prompt = self.arg(args, ArgName.INPUT, "")
        return ToolResult(True, data={"model": self._model_name, "response": f"Echo: {prompt}"})


AiModelToolExecutor = AIModelExecutor
