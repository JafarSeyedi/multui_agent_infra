import pytest
from engines.tools.models.mcp.executor import MCPToolExecutor


@pytest.mark.asyncio
async def test_mcp_executor_parses_server_command():
    executor = MCPToolExecutor(
        tool_name="test-tool",
        server_command=["echo", '{"result": "hello"}'],
    )
    assert executor.name == "test-tool"
    assert executor.description == "MCP tool: test-tool"


@pytest.mark.asyncio
async def test_mcp_executor_rejects_missing_server_command():
    with pytest.raises(ValueError, match="server_command"):
        MCPToolExecutor(tool_name="bad")
