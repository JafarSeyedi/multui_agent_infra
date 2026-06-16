import pytest
from engines.tools.executors.ai_model import AiModelToolExecutor
from engines.tools.models.tools_def_models import ArgName
from engines.tools.models.tools_def_models import ParameterName
from engines.tools.models.tools_def_models import ToolParameter


@pytest.mark.asyncio
async def test_executor_passes_through_without_gateway():
    executor = AiModelToolExecutor()
    result = await executor.execute([
        ToolParameter(name=ParameterName.MODEL, default="gpt-4"),
        ToolParameter(name=ArgName.INPUT, default="hello"),
    ])
    assert result.success
    assert result.data is not None
