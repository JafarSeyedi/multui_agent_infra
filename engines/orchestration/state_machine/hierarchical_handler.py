"""Hierarchical state handler for state machine.

Supports hierarchical nesting, pseudostates, and parent-child propagation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from ...core.instance import ProcessInstance
from ...core.engine import OrchestrationEngine


@dataclass
class StateNode:
    state_id: str
    name: str | None = None
    parent: str | None = None
    children: list[str] = field(default_factory=list)
    is_composite: bool = False
    is_orthogonal: bool = False
    initial_state: str | None = None
    entry_actions: list[str] = field(default_factory=list)
    exit_actions: list[str] = field(default_factory=list)


class HierarchicalHandler:
    def __init__(self, orchestration_engine: OrchestrationEngine | None = None) -> None:
        self._engine = orchestration_engine
        self._states: dict[str, StateNode] = {}

    def register(self, state: StateNode) -> None:
        self._states[state.state_id] = state

    def get_state(self, state_id: str) -> StateNode | None:
        return self._states.get(state_id)

    def get_parent(self, state_id: str) -> StateNode | None:
        state = self._states.get(state_id)
        if state and state.parent:
            return self._states.get(state.parent)
        return None

    def get_children(self, state_id: str) -> list[StateNode]:
        state = self._states.get(state_id)
        if state is None:
            return []
        return [self._states[s_id] for s_id in state.children if s_id in self._states]

    def get_ancestors(self, state_id: str) -> list[StateNode]:
        ancestors: list[StateNode] = []
        current = self.get_parent(state_id)
        while current:
            ancestors.append(current)
            current = self.get_parent(current.state_id)
        return ancestors

    def get_common_ancestor(self, state_a: str, state_b: str) -> StateNode | None:
        ancestors_a = set()
        current = self._states.get(state_a)
        while current:
            ancestors_a.add(current.state_id)
            current = self.get_parent(current.state_id)

        current = self._states.get(state_b)
        while current:
            if current.state_id in ancestors_a:
                return current
            current = self.get_parent(current.state_id)
        return None

    def is_ancestor_of(self, ancestor_id: str, state_id: str) -> bool:
        current = self.get_parent(state_id)
        while current:
            if current.state_id == ancestor_id:
                return True
            current = self.get_parent(current.state_id)
        return False

    def propagate_entry_up(self, state_id: str, instance: ProcessInstance) -> None:
        ancestors = self.get_ancestors(state_id)
        if ancestors:
            for ancestor in reversed(ancestors):
                for action in ancestor.entry_actions:
                    instance.set_variable(f"state.{ancestor.state_id}.entry", action)

    def propagate_exit_down(self, state_id: str, instance: ProcessInstance) -> None:
        state = self._states.get(state_id)
        if state:
            for action in state.exit_actions:
                instance.set_variable(f"state.{state_id}.exit", action)
            for child_id in state.children:
                child = self._states.get(child_id)
                if child:
                    instance.set_variable(f"state.{child_id}.parent_exit", True)
