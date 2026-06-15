from __future__ import annotations

import os
from typing import Any


class MLflowGatewayBackend:
    def __init__(self, gateway_uri: str = "", api_key: str = ""):
        self.gateway_uri = gateway_uri or os.environ.get("MLFLOW_GATEWAY_URI", "http://localhost:5000")
        self._api_key = api_key or os.environ.get("MLFLOW_GATEWAY_API_KEY", "")

    async def route(self, model: str, prompt: str, **kwargs: Any) -> dict[str, Any]:
        import aiohttp
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        payload = {
            "model": model,
            "prompt": prompt,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1024),
        }
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(f"{self.gateway_uri}/gateway/{model}/invocations", json=payload) as resp:
                if resp.status != 200:
                    return {"text": "", "error": f"Gateway error: {resp.status}", "cost": 0.0}
                data = await resp.json()
                return {
                    "text": data.get("candidates", [{}])[0].get("text", ""),
                    "cost": data.get("metadata", {}).get("cost", 0.0),
                    "tokens_input": data.get("metadata", {}).get("input_tokens", 0),
                    "tokens_output": data.get("metadata", {}).get("output_tokens", 0),
                }

    async def get_cost(self, model: str) -> float:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.gateway_uri}/gateway/{model}/cost") as resp:
                if resp.status != 200:
                    return 0.0
                data = await resp.json()
                return data.get("cost_per_request", 0.0)
