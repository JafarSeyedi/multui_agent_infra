"""JSON helper utilities with normalized error handling."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class JsonParseError(ValueError):
    """Raised when JSON loading/parsing fails."""


def loads_json(payload: str | bytes | bytearray) -> Any:
    """Parse JSON and raise a stable exception type on failure."""
    try:
        return json.loads(payload)
    except (TypeError, json.JSONDecodeError) as exc:
        raise JsonParseError(f"Invalid JSON payload: {exc}") from exc


def dumps_json(payload: Any, *, pretty: bool = False) -> str:
    """Serialize to JSON with stable separators."""
    kwargs: dict[str, Any] = {"ensure_ascii": False}
    if pretty:
        kwargs.update({"indent": 2, "sort_keys": True})
    return json.dumps(payload, **kwargs)
