import pytest
from engines.observability.backends.agentops import AgentOpsBackend


@pytest.mark.asyncio
async def test_agentops_connect_and_shutdown():
    backend = AgentOpsBackend(api_key="test-key")
    await backend.shutdown()
