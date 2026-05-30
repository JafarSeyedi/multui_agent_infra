"""Execution loop for state machine definitions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..core.instance import ProcessInstance
from .transition_handler import TransitionHandler


@dataclass(frozen=True)
class StateMachineExecutor:
    transition_handler: TransitionHandler | None = None

    def __post_init__(self) -> None:
        if self.transition_handler is None:
            object.__setattr__(self, "transition_handler", TransitionHandler())

    def execute(self, instance: ProcessInstance, definition: dict[str, Any]) -> None:
        states = definition.get("states", [])
        transitions = definition.get("transitions", [])
        if not states:
            return

        current_state = definition.get("initial_state", states[0].get("id"))
        steps = 0
        while steps < 200:
            steps += 1
            instance.current_activity_id = str(current_state)
            next_transition = self.transition_handler.resolve(current_state, transitions, instance.get_all_variables())
            if not next_transition:
                break
            current_state = next_transition.get("target")
            if not current_state:
                break
        instance.complete()
