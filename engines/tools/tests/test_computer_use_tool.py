import pytest
from engines.tools.executors.computer_use import ComputerUseExecutor
from engines.tools.models.tools_def_models import ArgName
from engines.tools.models.tools_def_models import ParameterName
from engines.tools.models.tools_def_models import ToolParameter


@pytest.mark.asyncio
async def test_computer_use_rejects_unknown_action():
    executor = ComputerUseExecutor(params=[
        ToolParameter(name=ParameterName.ACTION, default="unknown_action"),
        ToolParameter(name=ParameterName.URL, default="about:blank"),
    ])
    result = await executor.execute([
        ToolParameter(name=ArgName.CONTENT, default=""),
    ])
    assert not result.success
