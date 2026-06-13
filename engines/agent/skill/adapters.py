from __future__ import annotations

import json
import logging
from abc import ABC
from abc import abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class BaseSkillExecutor(ABC):
    """Template Method pattern — shared execution skeleton for skill executors."""

    def __init__(self, llm_client: Any) -> None:
        self._llm_client = llm_client

    async def execute(self, skill_identifier: str, inputs: dict[str, Any], **kwargs: Any) -> Any:
        prompt = await self._build_prompt(skill_identifier, inputs)
        return await self._call_llm(prompt, **kwargs)

    @abstractmethod
    async def _build_prompt(self, skill_identifier: str, inputs: dict[str, Any]) -> str:
        ...

    async def _call_llm(self, prompt: str, **kwargs: Any) -> Any:
        try:
            return self._llm_client.generate_structured_output(prompt=prompt, output_schema={}, **kwargs)
        except Exception:
            logger.warning("Structured output failed, falling back to text")
            text = self._llm_client.generate_text(prompt, **kwargs)
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return text


class MCPAdapter:
    """Adapter pattern — wraps MCPClient into the SkillExecutor interface."""

    def __init__(self, mcp_client: Any) -> None:
        self._client = mcp_client

    async def execute(self, tool_name: str, arguments: dict[str, Any] | None = None) -> Any:
        if hasattr(self._client, "call_tool"):
            return await self._client.call_tool(tool_name, arguments or {})
        raise RuntimeError("MCP client does not support call_tool")
