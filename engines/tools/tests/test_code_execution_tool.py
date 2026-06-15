import pytest
from engines.tools.models.code_execution.executor import CodeExecutionExecutor


@pytest.mark.asyncio
async def test_code_execution_rejects_empty_source():
    executor = CodeExecutionExecutor()
    result = await executor.execute(source="")
    assert not result.success
    assert "required" in result.error.lower()


@pytest.mark.asyncio
async def test_code_execution_runs_python():
    executor = CodeExecutionExecutor()
    result = await executor.execute(language="python", source="print('hello')")
    assert result.success
    assert "hello" in result.data.get("stdout", "")
