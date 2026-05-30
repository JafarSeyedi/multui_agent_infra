"""HTTP/service invocation adapter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import urllib.request
import urllib.error
import json


@dataclass(frozen=True)
class InvokeResult:
    status: int
    payload: dict[str, Any] | str


class ServiceInvoker:
    """Invoke HTTP endpoints via urllib to avoid hard runtime dependency."""

    def call_json(self, url: str, payload: dict[str, Any]) -> InvokeResult:
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=data,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                body = response.read().decode("utf-8")
                status = int(response.status)
                try:
                    parsed = json.loads(body)
                except json.JSONDecodeError:
                    parsed = body
                return InvokeResult(status=status, payload=parsed)
        except urllib.error.URLError as exc:
            return InvokeResult(status=503, payload={"error": str(exc)})

    def call(self, connector: Any, *args: Any, **kwargs: Any) -> Any:
        return connector(*args, **kwargs)
