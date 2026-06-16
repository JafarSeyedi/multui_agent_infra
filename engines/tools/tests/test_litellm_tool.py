from __future__ import annotations

import pytest

from engines.tools.base_executor import ToolResult
from engines.tools.executors.litellm import LiteLLMExecutor
from engines.tools.models.tools_def_models import ArgName
from engines.tools.models.tools_def_models import ParameterName
from engines.tools.models.tools_def_models import ParameterType
from engines.tools.models.tools_def_models import Tool
from engines.tools.models.tools_def_models import ToolKind
from engines.tools.models.tools_def_models import ToolParameter


class TestLiteLLMModels:

    def test_tool_defaults(self):
        tool = Tool(id="ll1", name="llm", kind=ToolKind.AI_MODEL)
        assert tool.params == []

    def test_tool_fields(self) -> None:
        tool = Tool(
            id="ll1",
            name="my_llm",
            description="My LLM",
            kind=ToolKind.AI_MODEL,
            params=[
                ToolParameter(name=ParameterName.MODEL, default="claude-3-opus-20240229"),
                ToolParameter(name=ArgName.MESSAGES, type=ParameterType.JSON, default='[{"role": "user", "content": "hi"}]'),
                ToolParameter(name=ParameterName.TEMPERATURE, type=ParameterType.FLOAT, default="0.5"),
                ToolParameter(name=ParameterName.MAX_TOKENS, type=ParameterType.INTEGER, default="100"),
            ],
        )
        params = {p.name: p.default for p in tool.params}
        assert params["model"] == "claude-3-opus-20240229"
        assert params["temperature"] == "0.5"
        assert params["max_tokens"] == "100"

    def test_tool_with_extra_params(self) -> None:
        tool = Tool(
            id="ll2",
            name="llm",
            kind=ToolKind.AI_MODEL,
            params=[
                ToolParameter(name=ParameterName.EXTRA, type=ParameterType.JSON, default='{"stop": ["END"], "top_p": 0.9}'),
            ],
        )
        import json
        extra = json.loads(tool.params[0].default or "{}")
        assert extra["stop"] == ["END"]

    def test_tool_minimal(self):
        tool = Tool(id="m", name="m", kind=ToolKind.AI_MODEL)
        assert tool.params == []

    def test_tool_kind(self):
        tool = Tool(id="x", name="x", kind=ToolKind.AI_MODEL)
        assert tool.kind == ToolKind.AI_MODEL


class TestLiteLLMExecutor:

    @pytest.fixture
    def executor(self):
        return LiteLLMExecutor()

    async def test_execute_missing_prompt_and_messages(self, executor):
        result = await executor.execute([])
        assert result.success is False
        assert "messages" in (result.error or "") or "prompt" in (result.error or "")

    async def test_execute_with_prompt(self, executor):
        result = await executor.execute([
            ToolParameter(name=ArgName.INPUT, default="Hello"),
        ])
        assert isinstance(result, ToolResult)

    async def test_execute_with_messages(self, executor):
        import json
        result = await executor.execute([
            ToolParameter(name=ArgName.MESSAGES, default=json.dumps([{"role": "user", "content": "Hello"}])),
        ])
        assert isinstance(result, ToolResult)

    async def test_execute_with_model_override(self, executor):
        result = await executor.execute([
            ToolParameter(name=ParameterName.MODEL, default="gpt-4o"),
            ToolParameter(name=ArgName.INPUT, default="Hello"),
        ])
        assert isinstance(result, ToolResult)

    async def test_execute_with_temperature(self, executor):
        result = await executor.execute([
            ToolParameter(name=ArgName.INPUT, default="Hi"),
            ToolParameter(name=ParameterName.TEMPERATURE, default="0.0"),
        ])
        assert isinstance(result, ToolResult)

    async def test_execute_with_extra_params(self, executor):
        result = await executor.execute([
            ToolParameter(name=ArgName.INPUT, default="Hi"),
            ToolParameter(name="top_p", default="0.5"),
            ToolParameter(name="stop", default='["END"]'),
        ])
        assert isinstance(result, ToolResult)
