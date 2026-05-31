"""HTTP connector for integration layer.

Provides HTTP/REST invocation for BPMN service tasks per Camunda connector pattern.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any


logger = logging.getLogger(__name__)


@dataclass
class HttpConnectorConfig:
    base_url: str = ""
    method: str = "GET"
    headers: dict[str, str] = field(default_factory=dict)
    timeout_seconds: int = 30
    retry_max: int = 0
    retry_delay_ms: int = 1000
    auth_type: str = "none"
    auth_config: dict[str, Any] = field(default_factory=dict)
    result_expression: str | None = None
    error_expression: str | None = None


@dataclass
class HttpConnectorResult:
    status_code: int = 200
    headers: dict[str, str] = field(default_factory=dict)
    body: Any = None
    raw_body: str = ""
    duration_ms: float = 0.0
    success: bool = True
    error: str | None = None


class HttpConnector:
    def __init__(self, config: HttpConnectorConfig | None = None) -> None:
        self._config = config or HttpConnectorConfig()

    async def invoke(
        self,
        url: str | None = None,
        method: str | None = None,
        headers: dict[str, str] | None = None,
        body: Any = None,
        variables: dict[str, Any] | None = None,
    ) -> HttpConnectorResult:
        target_url = url or self._config.base_url
        target_method = method or self._config.method
        target_headers = dict(self._config.headers)
        if headers:
            target_headers.update(headers)

        if variables:
            target_url = self._interpolate(target_url, variables)
            if isinstance(body, str):
                body = self._interpolate(body, variables)

        last_error = ""
        for attempt in range(self._config.retry_max + 1):
            try:
                result = await self._do_request(target_url, target_method, target_headers, body)
                if self._config.error_expression and result.body:
                    if self._check_error(result.body, self._config.error_expression):
                        last_error = "Error expression matched in response"
                        continue
                return result
            except Exception as e:
                last_error = str(e)
                if attempt < self._config.retry_max:
                    import asyncio
                    await asyncio.sleep(self._config.retry_delay_ms / 1000 * (attempt + 1))

        return HttpConnectorResult(
            status_code=0, success=False,
            error=f"HTTP request failed after {self._config.retry_max + 1} attempts: {last_error}",
        )

    async def _do_request(
        self, url: str, method: str, headers: dict[str, str], body: Any,
    ) -> HttpConnectorResult:
        start = time.time()
        try:
            import urllib.request
            import urllib.error

            data = None
            if body is not None:
                if isinstance(body, (dict, list)):
                    data = json.dumps(body).encode("utf-8")
                    headers.setdefault("Content-Type", "application/json")
                elif isinstance(body, str):
                    data = body.encode("utf-8")

            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            with urllib.request.urlopen(req, timeout=self._config.timeout_seconds) as resp:
                raw = resp.read().decode("utf-8")
                duration = (time.time() - start) * 1000
                parsed = None
                try:
                    parsed = json.loads(raw)
                except (json.JSONDecodeError, ValueError):
                    parsed = raw
                return HttpConnectorResult(
                    status_code=resp.status, headers=dict(resp.headers),
                    body=parsed, raw_body=raw, duration_ms=duration,
                    success=200 <= resp.status < 300,
                )
        except urllib.error.HTTPError as e:
            duration = (time.time() - start) * 1000
            return HttpConnectorResult(
                status_code=e.code, success=False,
                error=f"HTTP {e.code}: {e.reason}", duration_ms=duration,
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return HttpConnectorResult(
                status_code=0, success=False, error=str(e), duration_ms=duration,
            )

    def _interpolate(self, template: str, variables: dict[str, Any]) -> str:
        result = template
        for key, value in variables.items():
            result = result.replace(f"{{{key}}}", str(value))
            result = result.replace(f"${{{key}}}", str(value))
        return result

    def _check_error(self, body: Any, expression: str) -> bool:
        try:
            from ...expression.evaluator import EvaluationContext
            from ...expression.python_evaluator import PythonEvaluator
            ctx = body if isinstance(body, dict) else {"body": body}
            return bool(PythonEvaluator().evaluate(expression, EvaluationContext(variables=ctx)))
        except Exception:
            return False
