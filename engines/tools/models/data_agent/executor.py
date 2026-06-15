from __future__ import annotations

from typing import Any

from ...base_executor import BaseToolExecutor, ToolResult


class DataAgentExecutor(BaseToolExecutor):
    @property
    def name(self) -> str:
        return "data_agent"

    @property
    def description(self) -> str:
        return "Query Google Cloud Data Agents with natural language"

    async def execute(self, **kwargs: Any) -> ToolResult:
        query = kwargs.get("query", "")
        if not query:
            return ToolResult(success=False, error="Query is required")
        try:
            from google.cloud import discoveryengine_v1 as discoveryengine
            client = discoveryengine.SearchServiceClient()
            request = discoveryengine.SearchRequest(
                query=query,
                serving_config=f"projects/*/locations/global/dataStores/{kwargs.get('data_source', 'default')}/servingConfigs/default_search",
            )
            response = client.search(request)
            results = [{"id": r.id, "title": r.document.name, "snippet": r.model.snippet} for r in response.results]
            return ToolResult(success=True, data={"results": results})
        except ImportError:
            return ToolResult(success=False, error="google-cloud-discoveryengine not installed")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
