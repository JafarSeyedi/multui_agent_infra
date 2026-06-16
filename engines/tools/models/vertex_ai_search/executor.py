from __future__ import annotations

from typing import Any

from engines.tools.base_executor import BaseToolExecutor
from engines.tools.base_executor import ToolResult


class VertexAiSearchExecutor(BaseToolExecutor):
    """Searches enterprise data stores using Vertex AI Search (Discovery Engine)."""

    @property
    def name(self) -> str:
        return "vertex_ai_search"

    @property
    def description(self) -> str:
        return "Search enterprise data using Vertex AI Discovery Engine"

    async def execute(self, **kwargs: Any) -> ToolResult:
        query = kwargs.get("query", "")
        if not query:
            return ToolResult(success=False, error="query is required")
        data_store_id = kwargs.get("data_store_id", "")
        if not data_store_id:
            return ToolResult(success=False, error="data_store_id is required")
        serving_config = kwargs.get("serving_config", "default_search")
        location = kwargs.get("location", "global")
        try:
            from google.cloud import discoveryengine_v1 as discoveryengine
            client = discoveryengine.SearchServiceClient()
            serving_config_path = (
                f"projects/{{project}}/locations/{location}"
                f"/dataStores/{data_store_id}"
                f"/servingConfigs/{serving_config}"
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
