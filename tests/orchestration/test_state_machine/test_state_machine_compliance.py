"""State machine compliance tests per UML state diagram semantics."""

from __future__ import annotations



class TestStateMachineEngine:
    def test_engine_creation(self):
        from engines.orchestration.state_machine.engine import StateMachineEngine
        assert StateMachineEngine is not None

    def test_state_executor_creation(self):
        from engines.orchestration.state_machine.state_executor import StateMachineExecutor
        assert StateMachineExecutor is not None


class TestPseudoStateKind:
    def test_all_pseudo_state_kinds(self):
        from engines.document.models.osdm_models import PseudoStateKind
        expected = {"initial", "choice", "junction", "fork", "join",
                    "shallowHistory", "deepHistory", "terminate",
                    "entryPoint", "exitPoint"}
        actual = {e.value for e in PseudoStateKind}
        assert actual == expected


class TestStateTransition:
    def test_transition_hierarchy(self):
        from engines.document.models.osdm_models import Transition, StateTransition
        assert issubclass(StateTransition, Transition)
