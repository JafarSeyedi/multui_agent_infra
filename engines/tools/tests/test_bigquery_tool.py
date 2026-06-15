import pytest
from engines.tools.models.bigquery.executor import BigQueryExecutor
from engines.tools.models.bigquery.bigquery_models import BigQueryTool


def test_bigquery_tool_defaults():
    tool = BigQueryTool(id="bq-1", name="BigQuery Test", query="SELECT 1", project_id="my-project")
    assert tool.kind == "bigquery"
    assert tool.query == "SELECT 1"


@pytest.mark.asyncio
async def test_bigquery_executor_rejects_empty_query():
    executor = BigQueryExecutor()
    result = await executor.execute(query="")
    assert not result.success
    assert "empty" in result.error.lower()
