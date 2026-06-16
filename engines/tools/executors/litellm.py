from __future__ import annotations

from engines.tools.base_executor import BaseToolExecutor
from engines.tools.base_executor import ToolResult
from engines.tools.models.tools_def_models import ArgName, ParameterName, ToolKind
from engines.tools.models.tools_def_models import ToolParameter


@BaseToolExecutor.register(ToolKind.AI_MODEL)
class LiteLLMExecutor(BaseToolExecutor):
    """LLM inference via LiteLLM — unified interface for 100+ providers."""

    def _apply_params(self) -> None:
        self._default_model = self.param(self._params, ParameterName.MODEL, "gpt-4o-mini")
        self._temperature = self.param(self._params, ParameterName.TEMPERATURE, 0.7)
        self._max_tokens = self.param(self._params, ParameterName.MAX_TOKENS, None)

    @property
    def name(self) -> str:
        return "litellm"

    @property
    def description(self) -> str:
        return "Call LLMs via LiteLLM (OpenAI, Anthropic, Gemini, etc.)"

    async def execute(self, args: list[ToolParameter]) -> ToolResult:
        import litellm
        messages = self.arg(args, ArgName.MESSAGES, [])
        if not messages:
            prompt = self.arg(args, ArgName.INPUT, "")
            if not prompt:
                return ToolResult(success=False, error="messages or prompt required")
            messages = [{"role": "user", "content": prompt}]
        try:
            response = await litellm.acompletion(
                model=self._default_model,
                messages=messages,
                temperature=self._temperature,
                max_tokens=self._max_tokens,
            )
            choice = response.choices[0]
            return ToolResult(success=True, data={
                "text": choice.message.content,
                "model": response.model,
                "usage": dict(response.usage) if response.usage else {},
            })
        except Exception as e:
            return ToolResult(success=False, error=str(e))
