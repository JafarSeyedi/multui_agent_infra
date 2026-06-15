import pytest
from engines.tools.models.ai_model.executor import AiModelToolExecutor


@pytest.mark.asyncio
async def test_executor_passes_through_without_gateway():
    executor = AiModelToolExecutor()
    result = await executor.execute(model="gpt-4", prompt="hello")
    assert result.success
    assert result.data is not None
