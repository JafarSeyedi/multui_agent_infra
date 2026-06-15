from __future__ import annotations

from typing import Any

from engines.tools.base_executor import BaseToolExecutor
from engines.tools.base_executor import ToolResult


class LiteLLMExecutor(BaseToolExecutor):
    """LLM inference via LiteLLM — unified interface for 100+ providers."""

    def __init__(self, default_model: str = "gpt-4o-mini") -> None:
        self._default_model = default_model

    @property
    def name(self) -> str:
        return "litellm"

    @property
    def description(self) -> str:
        return "Call LLMs via LiteLLM (OpenAI, Anthropic, Gemini, etc.)"

    async def execute(self, **kwargs: Any) -> ToolResult:
        import litellm
        model = kwargs.get("model", self._default_model)
        messages = kwargs.get("messages", [])
        if not messages:
            prompt = kwargs.get("prompt", "")
            if not prompt:
                return ToolResult(success=False, error="messages or prompt required")
            messages = [{"role": "user", "content": prompt}]
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens")
        extra = {
            k: v for k, v in kwargs.items()
            if k not in ("model", "messages", "temperature", "max_tokens")
        }
        try:
            response = await litellm.acompletion(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **extra,
            )
            choice = response.choices[0]
            return ToolResult(success=True, data={
                "text": choice.message.content,
                "model": response.model,
                "usage": dict(response.usage) if response.usage else {},
            })
        except Exception as e:
            return ToolResult(success=False, error=str(e))
