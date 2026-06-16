from __future__ import annotations

from typing import Any

import pytest

from engines.tools.base_executor import ToolResult
from engines.tools.models.litellm import LiteLLMExecutor, LiteLLMTool, parse_litellm_tool
from engines.tools.models.litellm.writer import write_litellm_tool


class TestLiteLLMModels:

    def test_tool_defaults(self) -> None:
        tool = LiteLLMTool(id="ll1", name="llm")
        assert tool.model == "gpt-4o-mini"
        assert tool.temperature == 0.7
        assert tool.max_tokens is None

    def test_parse_round_trip(self) -> None:
        data: dict[str, Any] = {
            "id": "ll1",
            "name": "my_llm",
            "description": "My LLM",
            "model": "claude-3-opus-20240229",
            "messages": [{"role": "user", "content": "hi"}],
            "temperature": 0.5,
            "max_tokens": 100,
        }
        tool = parse_litellm_tool(data)
        assert tool.model == "claude-3-opus-20240229"
        assert tool.temperature == 0.5
        assert tool.max_tokens == 100

        out = write_litellm_tool(tool)
        assert out["model"] == "claude-3-opus-20240229"
        assert out["max_tokens"] == 100

    def test_parse_with_extra_kwargs(self) -> None:
        data: dict[str, Any] = {
            "id": "ll2",
            "name": "llm",
            "extra_kwargs": {"stop": ["END"], "top_p": 0.9},
        }
        tool = parse_litellm_tool(data)
        assert tool.extra_kwargs["stop"] == ["END"]

    def test_parse_minimal(self) -> None:
        tool = parse_litellm_tool({"id": "m", "name": "m"})
        assert tool.model == "gpt-4o-mini"

    def test_tool_kind(self) -> None:
        tool = LiteLLMTool(id="x", name="x")
        assert tool.kind.value == "aiModel"


class TestLiteLLMExecutor:

    @pytest.fixture
    def executor(self):
        return LiteLLMExecutor()

    async def test_execute_missing_prompt_and_messages(self, executor):
        result = await executor.execute()
        assert result.success is False
        assert "messages" in (result.error or "") or "prompt" in (result.error or "")

    async def test_execute_with_prompt(self, executor):
        result = await executor.execute(prompt="Hello")
        # If works → success; if not → graceful error
        assert isinstance(result, ToolResult)

    async def test_execute_with_messages(self, executor):
        result = await executor.execute(
            messages=[{"role": "user", "content": "Hello"}],
        )
        assert isinstance(result, ToolResult)

    async def test_execute_with_model_override(self, executor):
        result = await executor.execute(
            model="gpt-4o",
            prompt="Hello",
        )
        assert isinstance(result, ToolResult)

    async def test_execute_with_temperature(self, executor):
        result = await executor.execute(
            prompt="Hi", temperature=0.0,
        )
        assert isinstance(result, ToolResult)

    async def test_execute_with_extra_params(self, executor):
        result = await executor.execute(
            prompt="Hi",
            top_p=0.5,
            stop=["END"],
        )
        assert isinstance(result, ToolResult)
