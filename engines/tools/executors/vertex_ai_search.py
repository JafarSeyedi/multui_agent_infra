from __future__ import annotations

from engines.tools.base_executor import BaseToolExecutor
from engines.tools.base_executor import ToolResult
from engines.tools.models.tools_def_models import ArgName, ParameterName, ToolKind
from engines.tools.models.tools_def_models import ToolParameter


@BaseToolExecutor.register(ToolKind.VERTEX_AI_SEARCH)
class VertexAiSearchExecutor(BaseToolExecutor):
    """Searches enterprise data stores using Vertex AI Search (Discovery Engine)."""

    def _apply_params(self) -> None:
        self._data_store_id = self.param(self._params, ParameterName.DATA_STORE, "")
        self._serving_config = self.param(self._params, ParameterName.SERVING_CONFIG, "default_search")
        self._location = self.param(self._params, ParameterName.LOCATION, "global")

    @property
    def name(self) -> str:
        return "vertex_ai_search"

    @property
    def description(self) -> str:
        return "Search enterprise data using Vertex AI Discovery Engine"

    async def execute(self, args: list[ToolParameter]) -> ToolResult:
        query = self.arg(args, ArgName.INPUT, "")
        if not query:
            return ToolResult(success=False, error="query is required")
        if not self._data_store_id:
            return ToolResult(success=False, error="data_store_id is required")
        try:
            from google.cloud import discoveryengine_v1 as discoveryengine  # type: ignore[import-untyped]
            client = discoveryengine.SearchServiceClient()
            serving_config_path = (
                f"projects/{{project}}/locations/{self._location}"
                f"/dataStores/{self._data_store_id}"
                f"/servingConfigs/{self._serving_config}"
            )
            request = discoveryengine.SearchRequest(
                query=query,
                serving_config=serving_config_path,
                page_size=10,
            )
            response = client.search(request)
            results = []
            for r in response.results:
                doc = r.document
                results.append({
                    "id": doc.id,
                    "title": doc.name,
                    "content": doc.derived_struct_data if hasattr(doc, "derived_struct_data") else None,
                })
            return ToolResult(success=True, data={"results": results})
        except ImportError:
            return ToolResult(
                success=False,
                error="google-cloud-discoveryengine is not installed",
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
