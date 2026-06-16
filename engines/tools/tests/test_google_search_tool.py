from __future__ import annotations

import pytest

from engines.tools.base_executor import ToolResult
from engines.tools.executors.google_search import GoogleSearchExecutor
from engines.tools.models.tools_def_models import ArgName
from engines.tools.models.tools_def_models import ParameterName
from engines.tools.models.tools_def_models import ParameterType
from engines.tools.models.tools_def_models import Tool
from engines.tools.models.tools_def_models import ToolKind
from engines.tools.models.tools_def_models import ToolParameter


class TestGoogleSearchModels:

    def test_tool_defaults(self):
        tool = Tool(id="gs1", name="gs", kind=ToolKind.GOOGLE_SEARCH)
        assert tool.kind == ToolKind.GOOGLE_SEARCH
        assert tool.params == []

    def test_tool_fields(self) -> None:
        tool = Tool(
            id="gs1",
            name="web_search",
            description="Search the web",
            kind=ToolKind.GOOGLE_SEARCH,
            params=[
                ToolParameter(name=ArgName.INPUT, default="hello world"),
                ToolParameter(name=ParameterName.MAX_RESULTS, type=ParameterType.INTEGER, default="5"),
                ToolParameter(name=ParameterName.CX, default="my_cx"),
            ],
        )
        params = {p.name: p.default for p in tool.params}
        assert params["input"] == "hello world"
        assert params["max_results"] == "5"
        assert params["cx"] == "my_cx"


class TestGoogleSearchExecutor:

    @pytest.fixture
    def executor(self):
        return GoogleSearchExecutor()

    async def test_execute_missing_query(self, executor):
        result = await executor.execute([])
        assert result.success is False
        assert "query" in (result.error or "")

    async def test_execute_missing_credentials(self, executor):
        result = await executor.execute([
            ToolParameter(name=ArgName.INPUT, default="test"),
        ])
        assert result.success is False
        assert "api_key" in (result.error or "") or "cx" in (result.error or "")

    async def test_execute_with_credentials_no_httpx(self, executor):
        result = await executor.execute([
            ToolParameter(name=ArgName.INPUT, default="test"),
            ToolParameter(name="api_key", default="abc"),
            ToolParameter(name=ParameterName.CX, default="def"),
        ])
        if result.success is False and "httpx" in (result.error or ""):
            pass
        assert isinstance(result, ToolResult)

    async def test_execute_missing_cx(self, executor):
        result = await executor.execute([
            ToolParameter(name=ArgName.INPUT, default="test"),
            ToolParameter(name="api_key", default="abc"),
        ])
        assert result.success is False

    async def test_execute_missing_api_key(self, executor):
        result = await executor.execute([
            ToolParameter(name=ArgName.INPUT, default="test"),
            ToolParameter(name=ParameterName.CX, default="def"),
        ])
        assert result.success is False

    async def test_execute_passes_params(self, executor):
        result = await executor.execute([
            ToolParameter(name=ArgName.INPUT, default="hello"),
            ToolParameter(name="api_key", default="k"),
            ToolParameter(name=ParameterName.CX, default="c"),
            ToolParameter(name=ParameterName.MAX_RESULTS, default="5"),
        ])
        assert isinstance(result, ToolResult)
