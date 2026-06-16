# engines/masking/backends/in_memory/in_memory_masking.py
from __future__ import annotations

import re
from typing import Any

from ...plugin import IMaskingEngine, IAnonymizer


class InMemoryMaskingEngine(IMaskingEngine):
    name = "in_memory"

    async def mask(self, data: dict[str, Any], rules: list[str]) -> dict[str, Any]:
        result = dict(data)
        for field_path in rules:
            parts = field_path.split(".")
            target = result
            for part in parts[:-1]:
                if isinstance(target, dict):
                    target = target.get(part, {})
                else:
                    break
            else:
                if isinstance(target, dict) and parts[-1] in target:
                    target[parts[-1]] = "***"
        return result


class InMemoryAnonymizer(IAnonymizer):
    name = "in_memory"

    def __init__(self, patterns: dict[str, str] | None = None) -> None:
        self._patterns = patterns or {
            r"\b\d{3}-\d{2}-\d{4}\b": "XXX-XX-XXXX",
            r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b": "[email]",
        }

    async def anonymize(self, text: str) -> str:
        result = text
        for pattern, replacement in self._patterns.items():
            result = re.sub(pattern, replacement, result)
        return result
