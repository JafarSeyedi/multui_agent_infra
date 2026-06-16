import pytest

from engines.tools.executors.bigquery import BigQueryExecutor
from engines.tools.models.tools_def_models import ArgName
from engines.tools.models.tools_def_models import ParameterName
from engines.tools.models.tools_def_models import Tool
from engines.tools.models.tools_def_models import ToolKind
from engines.tools.models.tools_def_models import ToolParameter


def test_bigquery_tool_defaults():
    tool = Tool(
        id="bq-1",
        name="BigQuery Test",
        kind=ToolKind.BIGQUERY,
        params=[
            ToolParameter(name=ArgName.INPUT, default="SELECT 1"),
            ToolParameter(name=ParameterName.PROJECT, default="my-project"),
        ],
    )
    assert tool.kind == ToolKind.BIGQUERY
    params = {p.name: p.default for p in tool.params}
    assert params["input"] == "SELECT 1"


@pytest.mark.asyncio
async def test_bigquery_executor_rejects_empty_query():
    executor = BigQueryExecutor()
    result = await executor.execute([
        ToolParameter(name=ArgName.INPUT, default=""),
    ])
    assert not result.success
    assert "empty" in result.error.lower()
