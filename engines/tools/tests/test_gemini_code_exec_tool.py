import pytest
from engines.tools.executors.gemini_code_exec import GeminiCodeExecutionExecutor
from engines.tools.models.tools_def_models import ArgName
from engines.tools.models.tools_def_models import ParameterName
from engines.tools.models.tools_def_models import ToolParameter


@pytest.mark.asyncio
async def test_gemini_code_exec_rejects_empty_code():
    executor = GeminiCodeExecutionExecutor()
    result = await executor.execute([
        ToolParameter(name=ArgName.CODE, default=""),
    ])
    assert not result.success
    assert "required" in result.error.lower()
