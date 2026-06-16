import pytest
from engines.tools.executors.code_execution import CodeExecutionExecutor
from engines.tools.models.tools_def_models import ArgName
from engines.tools.models.tools_def_models import ToolParameter


@pytest.mark.asyncio
async def test_code_execution_rejects_empty_source():
    executor = CodeExecutionExecutor()
    result = await executor.execute([
        ToolParameter(name=ArgName.CODE, default=""),
    ])
    assert not result.success
    assert "required" in result.error.lower()


@pytest.mark.asyncio
async def test_code_execution_runs_python():
    executor = CodeExecutionExecutor()
    result = await executor.execute([
        ToolParameter(name=ArgName.CODE, default="print('hello')"),
    ])
    assert result.success
    assert "hello" in result.data.get("stdout", "")
