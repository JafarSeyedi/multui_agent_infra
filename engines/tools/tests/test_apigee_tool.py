import pytest
from engines.tools.models.apigee.executor import ApigeeExecutor


@pytest.mark.asyncio
async def test_apigee_executor_missing_api_hub_url():
    executor = ApigeeExecutor()
    result = await executor.execute(query="test", api_hub_url="")
    assert not result.success


@pytest.mark.asyncio
async def test_apigee_executor_validates_unknown_action():
    executor = ApigeeExecutor()
    result = await executor.execute(query="test", action="bogus")
    assert result.success
    assert result.data == {"apis": []}
