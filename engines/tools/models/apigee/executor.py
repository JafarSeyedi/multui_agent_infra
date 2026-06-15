from __future__ import annotations

from typing import Any

from ...base_executor import BaseToolExecutor, ToolResult


class ApigeeExecutor(BaseToolExecutor):
    @property
    def name(self) -> str:
        return "apigee"

    @property
    def description(self) -> str:
        return "Query Apigee API Hub for API discovery"

    async def execute(self, **kwargs: Any) -> ToolResult:
        import aiohttp
        base_url = kwargs.get("api_hub_url", "")
        if not base_url:
            base_url = "https://apihub.googleapis.com/v1"
        action = kwargs.get("action", "search")
        try:
            async with aiohttp.ClientSession() as session:
                if action == "search":
                    query = kwargs.get("query", "")
                    async with session.get(f"{base_url}/apis", params={"q": query}) as resp:
                        resp.raise_for_status()
                        data = await resp.json()
                        return ToolResult(success=True, data=data)
                elif action == "get":
                    api_id = kwargs.get("api_id", "")
                    async with session.get(f"{base_url}/apis/{api_id}") as resp:
                        resp.raise_for_status()
                        data = await resp.json()
                        return ToolResult(success=True, data=data)
                return ToolResult(success=True, data={"apis": []})
        except Exception as e:
            return ToolResult(success=False, error=str(e))
