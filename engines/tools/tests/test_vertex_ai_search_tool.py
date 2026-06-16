from __future__ import annotations

import pytest

from engines.tools.base_executor import ToolResult
from engines.tools.executors.vertex_ai_search import VertexAiSearchExecutor
from engines.tools.models.tools_def_models import ArgName
from engines.tools.models.tools_def_models import ParameterName
from engines.tools.models.tools_def_models import Tool
from engines.tools.models.tools_def_models import ToolKind
from engines.tools.models.tools_def_models import ToolParameter


class TestVertexAiSearchModels:

    def test_tool_defaults(self):
        tool = Tool(id="va1", name="vas", kind=ToolKind.VERTEX_AI_SEARCH)
        assert tool.kind == ToolKind.VERTEX_AI_SEARCH
        assert tool.params == []

    def test_tool_fields(self) -> None:
        tool = Tool(
            id="va1",
            name="enterprise_search",
            description="Search enterprise data",
            kind=ToolKind.VERTEX_AI_SEARCH,
            params=[
                ToolParameter(name=ArgName.INPUT, default="annual report"),
                ToolParameter(name=ParameterName.DATA_STORE, default="ds_123"),
                ToolParameter(name=ParameterName.SERVING_CONFIG, default="custom_search"),
                ToolParameter(name=ParameterName.LOCATION, default="us-central1"),
            ],
        )
        params = {p.name: p.default for p in tool.params}
        assert params["input"] == "annual report"
        assert params["data_store"] == "ds_123"
        assert params["serving_config"] == "custom_search"
        assert params["location"] == "us-central1"


class TestVertexAiSearchExecutor:

    @pytest.fixture
    def executor(self):
        return VertexAiSearchExecutor()

    async def test_execute_missing_query(self, executor):
        result = await executor.execute([])
        assert result.success is False
        assert "query" in (result.error or "")

    async def test_execute_missing_data_store(self, executor):
        result = await executor.execute([
            ToolParameter(name=ArgName.INPUT, default="test"),
        ])
        assert result.success is False
        assert "data_store_id" in (result.error or "")

    async def test_execute_graceful_missing_sdk(self, executor):
        result = await executor.execute([
            ToolParameter(name=ArgName.INPUT, default="test"),
            ToolParameter(name=ParameterName.DATA_STORE, default="ds_1"),
        ])
        assert isinstance(result, ToolResult)

    async def test_execute_with_all_params(self, executor):
        result = await executor.execute([
            ToolParameter(name=ArgName.INPUT, default="q"),
            ToolParameter(name=ParameterName.DATA_STORE, default="d"),
            ToolParameter(name=ParameterName.SERVING_CONFIG, default="sc"),
            ToolParameter(name=ParameterName.LOCATION, default="us"),
        ])
        assert isinstance(result, ToolResult)
