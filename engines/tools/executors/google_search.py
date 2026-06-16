from __future__ import annotations

from engines.tools.base_executor import BaseToolExecutor
from engines.tools.base_executor import ToolResult
from engines.tools.models.tools_def_models import ArgName, ParameterName, ToolKind
from engines.tools.models.tools_def_models import ToolParameter


@BaseToolExecutor.register(ToolKind.GOOGLE_SEARCH)
class GoogleSearchExecutor(BaseToolExecutor):
    """Performs web search via the Google Custom Search JSON API."""

    def _apply_params(self) -> None:
        self._default_api_key = self.param(self._params, ParameterName.API_KEY, "")
        self._default_cx = self.param(self._params, ParameterName.CX, "")
        self._default_num = self.param(self._params, ParameterName.MAX_RESULTS, 10)

    @property
    def name(self) -> str:
        return "google_search"

    @property
    def description(self) -> str:
        return "Search the web using Google Custom Search API"

    async def execute(self, args: list[ToolParameter]) -> ToolResult:
        query = self.arg(args, ArgName.INPUT, "")
        if not query:
            return ToolResult(success=False, error="query is required")
        api_key = self._default_api_key
        cx = self._default_cx
        if not api_key or not cx:
            return ToolResult(
                success=False,
                error="Google Custom Search requires both api_key and cx",
            )
        try:
            import httpx
            params = {
                "key": api_key,
                "cx": cx,
                "q": query,
                "num": min(self._default_num, 10),
            }
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://www.googleapis.com/customsearch/v1",
                    params=params,
                )
                resp.raise_for_status()
                data = resp.json()
            items = data.get("items", [])
            results = []
            for item in items:
                results.append({
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                })
            return ToolResult(success=True, data={"results": results})
        except ImportError:
            return ToolResult(success=False, error="httpx is not installed")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
