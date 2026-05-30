"""Compensation registration and rollback orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class CompensationStep:
    """One reversible action in a transaction-like workflow."""

    name: str
    action: Callable[[], Any]
    compensates: Callable[[], Any] | None = None


class CompensationManager:
    """Execute compensation steps in reverse registration order."""

    def __init__(self) -> None:
        self._steps: list[CompensationStep] = []

    def register(self, step: CompensationStep) -> None:
        self._steps.append(step)

    def clear(self) -> None:
        self._steps.clear()

    def rollback(self) -> list[str]:
        errors: list[str] = []
        for step in reversed(self._steps):
            try:
                if step.compensates is not None:
                    step.compensates()
            except Exception as exc:  # pragma: no cover - defensive
                errors.append(f"{step.name}: {exc}")
        self._steps.clear()
        return errors
