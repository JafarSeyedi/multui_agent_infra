from __future__ import annotations

from engines.tools.base_executor import BaseToolExecutor, ToolResult
from engines.tools.models.tools_def_models import ArgName, ParameterName, ToolKind
from engines.tools.models.tools_def_models import ToolParameter


@BaseToolExecutor.register(ToolKind.DATA_AGENT)
class DataAgentExecutor(BaseToolExecutor):
    def _apply_params(self) -> None:
        self._data_source = self.param(self._params, ParameterName.DATA_STORE, "default")

    @property
    def name(self) -> str:
        return "data_agent"

    @property
    def description(self) -> str:
        return "Query Google Cloud Data Agents with natural language"

    async def execute(self, args: list[ToolParameter]) -> ToolResult:
        query = self.arg(args, ArgName.INPUT, "")
        if not query:
            return ToolResult(success=False, error="Query is required")
        try:
            from google.cloud import discoveryengine_v1 as discoveryengine  # type: ignore[import-untyped]
            client = discoveryengine.SearchServiceClient()
            request = discoveryengine.SearchRequest(
                query=query,
                serving_config=f"projects/*/locations/global/dataStores/{self._data_source}/servingConfigs/default_search",
            )
            response = client.search(request)
            results = [{"id": r.id, "title": r.document.name, "snippet": r.model.snippet} for r in response.results]
            return ToolResult(success=True, data={"results": results})
        except ImportError:
            return ToolResult(success=False, error="google-cloud-discoveryengine not installed")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
