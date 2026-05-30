"""Loop and multi-instance handler for BPMN activities."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LoopConfiguration:
    repeat_count: int


class LoopHandler:
    def execute(self, config: LoopConfiguration, callback) -> list[object]:
        results: list[object] = []
        for _ in range(max(0, config.repeat_count)):
            results.append(callback())
        return results
