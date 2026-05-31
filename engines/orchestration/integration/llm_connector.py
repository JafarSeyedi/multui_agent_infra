"""LLM/AI connector for orchestration runtime.

Provides AI agent integration within BPMN workflows per Camunda 8.7+,
Kestra, Orch8, Stormchaser patterns.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any


logger = logging.getLogger(__name__)


class LlmProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    DEEPSEEK = "deepseek"
    OLLAMA = "ollama"
    CUSTOM = "custom"


from enum import Enum


@dataclass
class LlmMessage:
    role: str = "user"
    content: str = ""


@dataclass
class LlmRequest:
    provider: str = LlmProvider.OPENAI
    model: str = "gpt-4"
    messages: list[LlmMessage] = field(default_factory=list)
    system_prompt: str | None = None
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 1.0
    stop_sequences: list[str] = field(default_factory=list)
    tools: list[dict[str, Any]] = field(default_factory=list)
    tool_choice: str | None = None
    variables: dict[str, Any] = field(default_factory=dict)
    endpoint_url: str | None = None
    api_key: str | None = None
    timeout_seconds: int = 120


@dataclass
class LlmResponse:
    content: str = ""
    model: str = ""
    provider: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    duration_ms: float = 0.0
    success: bool = True
    error: str | None = None
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    raw_response: Any = None


class LlmConnector:
    async def invoke(self, request: LlmRequest) -> LlmResponse:
        start = time.time()
        try:
            messages = []
            if request.system_prompt:
                messages.append({"role": "system", "content": request.system_prompt})
            for msg in request.messages:
                content = self._interpolate(msg.content, request.variables)
                messages.append({"role": msg.role, "content": content})

            if request.provider == LlmProvider.OPENAI:
                return await self._call_openai(request, messages, start)
            elif request.provider == LlmProvider.ANTHROPIC:
                return await self._call_anthropic(request, messages, start)
            elif request.provider == LlmProvider.OLLAMA:
                return await self._call_ollama(request, messages, start)
            else:
                return await self._call_generic(request, messages, start)
        except Exception as e:
            duration = (time.time() - start) * 1000
            logger.error("LLM invocation failed: %s", e)
            return LlmResponse(
                success=False, error=str(e), duration_ms=duration,
                provider=request.provider, model=request.model,
            )

    async def _call_openai(self, request: LlmRequest, messages: list[dict], start: float) -> LlmResponse:
        try:
            import urllib.request
            url = request.endpoint_url or "https://api.openai.com/v1/chat/completions"
            payload = {
                "model": request.model, "messages": messages,
                "temperature": request.temperature, "max_tokens": request.max_tokens,
            }
            if request.tools:
                payload["tools"] = request.tools
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url, data=data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {request.api_key or ''}",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=request.timeout_seconds) as resp:
                raw = resp.read().decode("utf-8")
                result = json.loads(raw)
                choice = result.get("choices", [{}])[0]
                msg = choice.get("message", {})
                duration = (time.time() - start) * 1000
                usage = result.get("usage", {})
                return LlmResponse(
                    content=msg.get("content", ""),
                    model=result.get("model", request.model),
                    provider=LlmProvider.OPENAI,
                    prompt_tokens=usage.get("prompt_tokens", 0),
                    completion_tokens=usage.get("completion_tokens", 0),
                    total_tokens=usage.get("total_tokens", 0),
                    duration_ms=duration, success=True,
                    tool_calls=msg.get("tool_calls", []),
                    raw_response=result,
                )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return LlmResponse(success=False, error=str(e), duration_ms=duration)

    async def _call_anthropic(self, request: LlmRequest, messages: list[dict], start: float) -> LlmResponse:
        try:
            import urllib.request
            url = request.endpoint_url or "https://api.anthropic.com/v1/messages"
            system = ""
            if request.system_prompt:
                system = request.system_prompt
            payload = {
                "model": request.model, "messages": messages,
                "max_tokens": request.max_tokens,
            }
            if system:
                payload["system"] = system
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url, data=data,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": request.api_key or "",
                    "anthropic-version": "2023-06-01",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=request.timeout_seconds) as resp:
                raw = resp.read().decode("utf-8")
                result = json.loads(raw)
                content_blocks = result.get("content", [])
                content = "".join(b.get("text", "") for b in content_blocks if b.get("type") == "text")
                duration = (time.time() - start) * 1000
                usage = result.get("usage", {})
                return LlmResponse(
                    content=content, model=result.get("model", request.model),
                    provider=LlmProvider.ANTHROPIC,
                    prompt_tokens=usage.get("input_tokens", 0),
                    completion_tokens=usage.get("output_tokens", 0),
                    duration_ms=duration, success=True, raw_response=result,
                )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return LlmResponse(success=False, error=str(e), duration_ms=duration)

    async def _call_ollama(self, request: LlmRequest, messages: list[dict], start: float) -> LlmResponse:
        try:
            import urllib.request
            url = request.endpoint_url or "http://localhost:11434/api/chat"
            payload = {
                "model": request.model, "messages": messages,
                "stream": False,
                "options": {"temperature": request.temperature},
            }
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=request.timeout_seconds) as resp:
                raw = resp.read().decode("utf-8")
                result = json.loads(raw)
                msg = result.get("message", {})
                duration = (time.time() - start) * 1000
                return LlmResponse(
                    content=msg.get("content", ""),
                    model=result.get("model", request.model),
                    provider=LlmProvider.OLLAMA,
                    duration_ms=duration, success=True, raw_response=result,
                )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return LlmResponse(success=False, error=str(e), duration_ms=duration)

    async def _call_generic(self, request: LlmRequest, messages: list[dict], start: float) -> LlmResponse:
        return LlmResponse(
            success=False,
            error=f"Provider '{request.provider}' not implemented",
            duration_ms=(time.time() - start) * 1000,
        )

    def _interpolate(self, template: str, variables: dict[str, Any]) -> str:
        result = template
        for key, value in variables.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result
