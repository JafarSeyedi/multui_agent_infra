from __future__ import annotations

from typing import Any

from engines.tools.base_executor import BaseToolExecutor
from engines.tools.base_executor import ToolResult


class GoogleSearchExecutor(BaseToolExecutor):
    """Performs web search via the Google Custom Search JSON API."""

    def __init__(self, api_key: str = "", cx: str = "") -> None:
        self._default_api_key = api_key
        self._default_cx = cx

    @property
    def name(self) -> str:
        return "google_search"

    @property
    def description(self) -> str:
        return "Search the web using Google Custom Search API"

    async def execute(self, **kwargs: Any) -> ToolResult:
        query = kwargs.get("query", "")
        if not query:
            return ToolResult(success=False, error="query is required")
        num = kwargs.get("num_results", 10)
        api_key = kwargs.get("api_key", self._default_api_key)
        cx = kwargs.get("cx", self._default_cx)
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
                "num": min(num, 10),
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
