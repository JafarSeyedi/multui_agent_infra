"""Ad-hoc subprocess handler for BPMN ad-hoc tasks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Iterator


@dataclass(frozen=True)
class AdHocProcess:
    activities: list[dict[str, Any]]


class AdhocHandler:
    def iterate(self, process: AdHocProcess) -> Iterator[dict[str, Any]]:
        for activity in process.activities:
            yield activity

    def execute(self, process: AdHocProcess) -> list[str]:
        return [str(item.get("id")) for item in self.iterate(process)]
