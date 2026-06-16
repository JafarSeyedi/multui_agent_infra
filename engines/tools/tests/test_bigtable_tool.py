import pytest
from engines.tools.executors.bigtable import BigtableExecutor
from engines.tools.models.tools_def_models import ArgName
from engines.tools.models.tools_def_models import ParameterName
from engines.tools.models.tools_def_models import ToolParameter


@pytest.mark.asyncio
async def test_bigtable_executor_rejects_missing_instance():
    executor = BigtableExecutor()
    result = await executor.execute([
        ToolParameter(name=ParameterName.TABLE, default="my-table"),
        ToolParameter(name=ParameterName.ROW_KEY, default="key1"),
    ])
    assert not result.success
    assert "instance_id" in result.error.lower()
