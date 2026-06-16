import pytest
from engines.tools.executors.mcp import MCPToolExecutor
from engines.tools.models.tools_def_models import ParameterName
from engines.tools.models.tools_def_models import ParameterType
from engines.tools.models.tools_def_models import ToolParameter


@pytest.mark.asyncio
async def test_mcp_executor_parses_server_command():
    executor = MCPToolExecutor(params=[
        ToolParameter(name=ParameterName.COMMAND, default='["echo", "hello"]', type=ParameterType.JSON),
    ])
    assert "mcp:" in executor.name


@pytest.mark.asyncio
async def test_mcp_executor_rejects_missing_server_command():
    with pytest.raises(ValueError, match="server_command|requires"):
        MCPToolExecutor()
