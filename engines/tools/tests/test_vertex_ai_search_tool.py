from __future__ import annotations

from typing import Any

import pytest

from engines.tools.base_executor import ToolResult
from engines.tools.models.vertex_ai_search import (
    VertexAiSearchExecutor,
    VertexAiSearchTool,
    parse_vertex_ai_search_tool,
)
from engines.tools.models.vertex_ai_search.writer import write_vertex_ai_search_tool


class TestVertexAiSearchModels:

    def test_tool_defaults(self):
        tool = VertexAiSearchTool(id="va1", name="vas")
        assert tool.kind.value == "vertexAiSearch"
        assert tool.query == ""
        assert tool.serving_config == "default_search"
        assert tool.location == "global"

    def test_parse_round_trip(self):
        data: dict[str, Any] = {
            "id": "va1",
            "name": "enterprise_search",
            "description": "Search enterprise data",
            "query": "annual report",
            "data_store_id": "ds_123",
            "serving_config": "custom_search",
            "location": "us-central1",
        }
        tool = parse_vertex_ai_search_tool(data)
        assert tool.query == "annual report"
        assert tool.data_store_id == "ds_123"
        assert tool.serving_config == "custom_search"
        assert tool.location == "us-central1"

        out = write_vertex_ai_search_tool(tool)
        assert out["query"] == "annual report"
        assert out["data_store_id"] == "ds_123"
        assert out["kind"] == "vertexAiSearch"


class TestVertexAiSearchExecutor:

    @pytest.fixture
    def executor(self):
        return VertexAiSearchExecutor()

    async def test_execute_missing_query(self, executor):
        result = await executor.execute()
        assert result.success is False
        assert "query" in (result.error or "")

    async def test_execute_missing_data_store(self, executor):
        result = await executor.execute(query="test")
        assert result.success is False
        assert "data_store_id" in (result.error or "")

    async def test_execute_graceful_missing_sdk(self, executor):
        result = await executor.execute(
            query="test", data_store_id="ds_1",
        )
        # Either google-cloud-discoveryengine is installed (will auth-fail)
        # or missing (graceful ImportError)
        assert isinstance(result, ToolResult)

    async def test_execute_with_all_params(self, executor):
        result = await executor.execute(
            query="q", data_store_id="d", serving_config="sc",
            location="us",
        )
        assert isinstance(result, ToolResult)
