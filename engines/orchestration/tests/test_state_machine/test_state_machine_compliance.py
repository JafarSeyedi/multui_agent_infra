"""State machine compliance tests per UML state diagram semantics."""

from __future__ import annotations

import pytest

from engines.orchestration.bpmn.models.bpmn_models import Transition
from engines.orchestration.models.shared_models import PseudoStateKind
from engines.orchestration.state_machine.models.state_machine_models import StateTransition


class TestStateMachineEngine:
    def test_engine_creation(self):
        from engines.orchestration.state_machine.engine import StateMachineEngine
        assert StateMachineEngine is not None

    def test_state_executor_creation(self):
        from engines.orchestration.state_machine.state_execution import StateMachineExecutor
        assert StateMachineExecutor is not None


class TestPseudoStateKind:
    def test_all_pseudo_state_kinds(self):
        expected = {"initial", "choice", "junction", "fork", "join",
                    "shallowHistory", "deepHistory", "terminate",
                    "entryPoint", "exitPoint"}
        actual = {e.value for e in PseudoStateKind}
        assert actual == expected


class TestStateTransition:
    def test_transition_hierarchy(self):
        assert issubclass(StateTransition, Transition)
