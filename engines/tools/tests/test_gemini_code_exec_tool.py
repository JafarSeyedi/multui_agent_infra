import pytest
from engines.tools.models.gemini_code_exec.executor import GeminiCodeExecutionExecutor


@pytest.mark.asyncio
async def test_gemini_code_exec_rejects_empty_code():
    executor = GeminiCodeExecutionExecutor()
    result = await executor.execute(code="")
    assert not result.success
    assert "required" in result.error.lower()
