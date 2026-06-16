import pytest
from engines.tools.executors.data_agent import DataAgentExecutor
from engines.tools.models.tools_def_models import ArgName
from engines.tools.models.tools_def_models import ParameterName
from engines.tools.models.tools_def_models import ToolParameter


@pytest.mark.asyncio
async def test_data_agent_rejects_empty_query():
    executor = DataAgentExecutor()
    result = await executor.execute([
        ToolParameter(name=ArgName.INPUT, default=""),
    ])
    assert not result.success
