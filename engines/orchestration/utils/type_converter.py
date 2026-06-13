"""Type conversion helpers used across orchestration modules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from collections.abc import Callable


@dataclass(frozen=True)
class ConversionError(ValueError):
    """Raised when a value cannot be converted to a requested type."""


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y", "on"}:
        return True
    if text in {"false", "0", "no", "n", "off"}:
        return False
    raise ConversionError(f"Cannot convert {value!r} to bool")


def _to_int(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ConversionError(f"Cannot convert {value!r} to int") from exc


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ConversionError(f"Cannot convert {value!r} to float") from exc


def _to_json_value(value: Any) -> Any:
    return value

_TYPE_MAP: dict[str, Callable[[Any], Any]] = {
    "bool": _to_bool,
    "boolean": _to_bool,
    "int": _to_int,
    "integer": _to_int,
    "float": _to_float,
    "number": _to_float,
    "any": _to_json_value,
    "json": _to_json_value,
    "string": lambda value: str(value),
}


def coerce_type(value: Any, target: str) -> Any:
    """Convert a value to a requested logical type."""
    converter = _TYPE_MAP.get(target.lower())
    if converter is None:
        raise ConversionError(f"Unsupported target type: {target}")
    return converter(value)
