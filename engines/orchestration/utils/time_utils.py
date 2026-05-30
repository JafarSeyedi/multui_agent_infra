"""Time/duration helper functions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import re


@dataclass(frozen=True)
class DurationError(ValueError):
    """Raised when a duration string is invalid."""


def utc_now() -> datetime:
    """Current UTC timestamp."""
    return datetime.now(timezone.utc)


def to_epoch_ms(value: datetime) -> int:
    """Convert datetime to Unix epoch milliseconds."""
    return int(value.timestamp() * 1000)


def parse_duration(value: str | int | float | timedelta) -> timedelta:
    """Parse a duration from common textual/int/float representations.

    Supported: `500ms`, `2s`, `3m`, `1h`, `7d`, integers/float seconds.
    """
    if isinstance(value, timedelta):
        return value
    if isinstance(value, (int, float)):
        return timedelta(seconds=float(value))

    duration = value.strip().lower()
    if not duration:
        raise DurationError("Empty duration")

    match = re.fullmatch(r"^([0-9]+(?:\.[0-9]+)?)(ms|s|m|h|d)$", duration)
    if not match:
        raise DurationError(f"Unsupported duration format: {value!r}")

    number = float(match.group(1))
    unit = match.group(2)
    if unit == "ms":
        return timedelta(milliseconds=number)
    if unit == "s":
        return timedelta(seconds=number)
    if unit == "m":
        return timedelta(minutes=number)
    if unit == "h":
        return timedelta(hours=number)
    return timedelta(days=number)
