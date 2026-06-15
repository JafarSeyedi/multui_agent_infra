import pytest
from engines.tools.models.data_agent.executor import DataAgentExecutor


@pytest.mark.asyncio
async def test_data_agent_rejects_empty_query():
    executor = DataAgentExecutor()
    result = await executor.execute(query="")
    assert not result.success
