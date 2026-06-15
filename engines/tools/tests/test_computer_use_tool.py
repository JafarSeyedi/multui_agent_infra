import pytest
from engines.tools.models.computer_use.executor import ComputerUseExecutor


@pytest.mark.asyncio
async def test_computer_use_rejects_unknown_action():
    executor = ComputerUseExecutor()
    result = await executor.execute(action="unknown_action")
    assert not result.success
