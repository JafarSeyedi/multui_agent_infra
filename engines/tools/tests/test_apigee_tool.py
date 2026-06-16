import pytest
from engines.tools.executors.apigee import ApigeeExecutor
from engines.tools.models.tools_def_models import ArgName
from engines.tools.models.tools_def_models import ParameterName
from engines.tools.models.tools_def_models import ToolParameter


@pytest.mark.asyncio
async def test_apigee_executor_missing_api_hub_url():
    executor = ApigeeExecutor(params=[
        ToolParameter(name=ParameterName.URL, default=""),
    ])
    result = await executor.execute([
        ToolParameter(name=ArgName.INPUT, default="test"),
    ])
    assert not result.success


@pytest.mark.asyncio
async def test_apigee_executor_validates_unknown_action():
    executor = ApigeeExecutor(params=[
        ToolParameter(name=ParameterName.URL, default=""),
        ToolParameter(name=ParameterName.ACTION, default="bogus"),
    ])
    result = await executor.execute([
        ToolParameter(name=ArgName.INPUT, default="test"),
    ])
    assert result.success
    assert result.data == {"apis": []}
