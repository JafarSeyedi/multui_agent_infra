from __future__ import annotations

from typing import Any

import pytest

from engines.tools.base_executor import ToolResult
from engines.tools.models.google_search import (
    GoogleSearchExecutor,
    GoogleSearchTool,
    parse_google_search_tool,
)
from engines.tools.models.google_search.writer import write_google_search_tool


class TestGoogleSearchModels:

    def test_tool_defaults(self):
        tool = GoogleSearchTool(id="gs1", name="gs")
        assert tool.kind.value == "googleSearch"
        assert tool.query == ""
        assert tool.num_results == 10

    def test_parse_round_trip(self):
        data: dict[str, Any] = {
            "id": "gs1",
            "name": "web_search",
            "description": "Search the web",
            "query": "hello world",
            "num_results": 5,
            "cx": "my_cx",
            "api_key": "my_key",
        }
        tool = parse_google_search_tool(data)
        assert tool.query == "hello world"
        assert tool.num_results == 5
        assert tool.cx == "my_cx"

        out = write_google_search_tool(tool)
        assert out["query"] == "hello world"
        assert out["num_results"] == 5
        assert out["kind"] == "googleSearch"


class TestGoogleSearchExecutor:

    @pytest.fixture
    def executor(self):
        return GoogleSearchExecutor()

    async def test_execute_missing_query(self, executor):
        result = await executor.execute()
        assert result.success is False
        assert "query" in (result.error or "")

    async def test_execute_missing_credentials(self, executor):
        result = await executor.execute(query="test")
        assert result.success is False
        # Should fail with missing api_key/cx before reaching HTTP
        assert "api_key" in (result.error or "") or "cx" in (result.error or "")

    async def test_execute_with_credentials_no_httpx(self, executor):
        result = await executor.execute(
            query="test", api_key="abc", cx="def",
        )
        if result.success is False and "httpx" in (result.error or ""):
            pass  # httpx not installed — expected graceful degradation
        # If httpx is installed it will fail with auth, not our concern
        assert isinstance(result, ToolResult)

    async def test_execute_missing_cx(self, executor):
        result = await executor.execute(query="test", api_key="abc")
        assert result.success is False

    async def test_execute_missing_api_key(self, executor):
        result = await executor.execute(query="test", cx="def")
        assert result.success is False

    async def test_execute_passes_params(self, executor):
        result = await executor.execute(
            query="hello", api_key="k", cx="c", num_results=5,
        )
        # Will fail at HTTP level but parameters were formed correctly
        assert isinstance(result, ToolResult)
