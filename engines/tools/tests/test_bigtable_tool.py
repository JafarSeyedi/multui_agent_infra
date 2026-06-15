import pytest
from engines.tools.models.bigtable.executor import BigtableExecutor


@pytest.mark.asyncio
async def test_bigtable_executor_rejects_missing_instance():
    executor = BigtableExecutor()
    result = await executor.execute(table_id="my-table", row_key="key1")
    assert not result.success
    assert "instance_id" in result.error.lower()
