"""BPMN engine execution semantics tests per BPMN 2.0 Annex A."""

from __future__ import annotations

from datetime import datetime

import pytest

from engines.orchestration.bpmn.engine import BPMNEngine
from engines.orchestration.document.models.osdm_models import FlowNode
from engines.orchestration.bpmn.bpmn_execution_semantics import (
    BpmnGatewaySemantics,
    BpmnEventSubProcessHandler,
    BpmnTransactionHandler,
    BpmnBoundaryEventHandler,
)
from engines.orchestration.core.engine import OrchestrationEngine, ProcessDefinition
from engines.orchestration.core.instance import InstanceState
from engines.orchestration.persistence.event_repository import EventRepository
from engines.orchestration.persistence.history_repository import HistoryRepository
from engines.orchestration.persistence.instance_repository import InstanceRepository
from engines.orchestration.persistence.token_repository import TokenRepository
from engines.orchestration.persistence.variable_repository import VariableRepository


def _definition(*, key: str, definition_xml: str, def_type: str = "bpmn") -> ProcessDefinition:
    return ProcessDefinition(
        id=f"{key}-id", key=key, name=key, version=1,
        deployment_id=f"{key}-deployment", resource_name=f"{key}.{def_type}",
        diagram_resource_name=None, has_start_form_key=False,
        has_graphical_notation=True, is_suspended=False, tenant_id=None,
        version_tag=None, history_time_to_live=None, is_startable_in_tasklist=True,
        definition_type=def_type, definition_xml=definition_xml,
        deployed_at=datetime.utcnow(),
    )


def _make_engine():
    engine = OrchestrationEngine(
        event_repository=EventRepository(),
        history_repository=HistoryRepository(),
        instance_repository=InstanceRepository(),
        variable_repository=VariableRepository(),
        token_repository=TokenRepository(),
    )
    bpmn_engine = BPMNEngine(engine)
    engine.register_engine_handler("bpmn", bpmn_engine)
    return engine, bpmn_engine


class TestBpmnEngineLifecycle:
    @pytest.mark.asyncio
    async def test_engine_start_stop(self):
        engine, _ = _make_engine()
        await engine.start()
        assert engine.state == "running"
        await engine.stop()
        assert engine.state == "stopped"

    @pytest.mark.asyncio
    async def test_deploy_and_start_instance(self):
        engine, _ = _make_engine()
        deployment = await engine.deploy("test", {"test.bpmn": "<bpmn></bpmn>"})
        assert deployment.id in engine.deployments
        definition = _definition(key="proc1", definition_xml=str({
            "id": "proc1", "start_event_id": "start1",
            "activities": [{"id": "start1", "type": "startEvent", "payload": {}}],
        }))
        engine.definitions["proc1"] = definition
        instance = await engine.start_process_instance("proc1", variables={"x": 1})
        assert instance.state == InstanceState.ACTIVE
        assert instance.variables["x"] == 1


class TestExclusiveGateway:
    @pytest.mark.asyncio
    async def test_exclusive_gateway_first_true_wins(self):
        from engines.orchestration.bpmn.gateway_handler import GatewayHandler
        handler = GatewayHandler()
        gateway = {
            "id": "gw1", "type": "exclusiveGateway",
            "branches": [
                {"target": "task_a", "condition": "amount > 100", "priority": 0},
                {"target": "task_b", "condition": "amount <= 100", "priority": 1},
            ],
        }
        result = handler.choose(gateway=gateway, context={"amount": 200})
        assert result.next_targets == ["task_a"]

    @pytest.mark.asyncio
    async def test_exclusive_gateway_falls_to_default(self):
        from engines.orchestration.bpmn.gateway_handler import GatewayHandler
        handler = GatewayHandler()
        gateway = {
            "id": "gw1", "type": "exclusiveGateway", "default": "task_default",
            "branches": [
                {"target": "task_a", "condition": "x > 999", "priority": 0},
            ],
        }
        result = handler.choose(gateway=gateway, context={"x": 1})
        assert result.default_used or "task_default" in result.next_targets


class TestParallelGateway:
    @pytest.mark.asyncio
    async def test_parallel_gateway_all_paths_taken(self):
        from engines.orchestration.bpmn.gateway_handler import GatewayHandler
        handler = GatewayHandler()
        gateway = {
            "id": "gw1", "type": "parallelGateway",
            "branches": [
                {"target": "task_a"}, {"target": "task_b"}, {"target": "task_c"},
            ],
        }
        result = handler.choose(gateway=gateway, context={})
        assert set(result.next_targets) == {"task_a", "task_b", "task_c"}


class TestEventSubProcess:
    def test_event_sub_process_registration(self):
        handler = BpmnEventSubProcessHandler()
        from engines.orchestration.document.models.osdm_models import StartEvent
        start_evt = StartEvent(id="msg_start", name="Message Start")
        ctx = handler.register_event_sub_process(
            "inst1", "subproc1", start_evt, is_interrupting=True
        )
        assert ctx.sub_process_id == "subproc1"
        assert ctx.is_interrupting is True
        assert ctx.triggered is False

    def test_interrupting_sub_process_interrupts_parent(self):
        handler = BpmnEventSubProcessHandler()
        from engines.orchestration.document.models.osdm_models import StartEvent
        start_evt = StartEvent(id="err_start", name="Error Start")
        ctx = handler.register_event_sub_process(
            "inst1", "subproc1", start_evt, is_interrupting=True
        )
        handler.mark_triggered(ctx, "error")
        assert handler.should_interrupt_parent(ctx) is True

    def test_non_interrupting_does_not_interrupt(self):
        handler = BpmnEventSubProcessHandler()
        from engines.orchestration.document.models.osdm_models import StartEvent
        start_evt = StartEvent(id="timer_start", name="Timer Start")
        ctx = handler.register_event_sub_process(
            "inst1", "subproc1", start_evt, is_interrupting=False
        )
        handler.mark_triggered(ctx, "timer")
        assert handler.should_interrupt_parent(ctx) is False


class TestTransactionSemantics:
    def test_transaction_lifecycle(self):
        handler = BpmnTransactionHandler()
        ctx = handler.begin_transaction("tx1", "subproc1")
        assert ctx.state == "active"
        handler.complete_activity("tx1", "task1")
        handler.complete_activity("tx1", "task2")
        assert len(ctx.completed_activities) == 2
        compensated = handler.compensate("tx1")
        assert compensated == ["task2", "task1"]
        assert ctx.state == "compensated"

    def test_transaction_cancel(self):
        handler = BpmnTransactionHandler()
        handler.begin_transaction("tx1", "subproc1")
        assert handler.cancel("tx1") is True
        ctx = handler.get_context("tx1")
        assert ctx.state == "cancelled"

    def test_transaction_failure_triggers_compensation(self):
        handler = BpmnTransactionHandler()
        handler.begin_transaction("tx1", "subproc1")
        handler.complete_activity("tx1", "task1")
        handler.fail_activity("tx1", "task2")
        ctx = handler.get_context("tx1")
        assert ctx.state == "failed"
        assert ctx.failed_activity == "task2"


class TestBoundaryEventSemantics:
    def test_interrupting_boundary_event(self):
        from engines.orchestration.document.models.osdm_models import BoundaryEvent, Event, EventType
        be = BoundaryEvent(id="be1", event_type=EventType.BOUNDARY, cancel_activity=True)
        assert BpmnBoundaryEventHandler.is_interrupting(be) is True

    def test_non_interrupting_boundary_event(self):
        from engines.orchestration.document.models.osdm_models import BoundaryEvent, EventType
        be = BoundaryEvent(id="be2", event_type=EventType.BOUNDARY, cancel_activity=False)
        assert BpmnBoundaryEventHandler.is_interrupting(be) is False


class TestInclusiveGateway:
    @pytest.mark.asyncio
    async def test_inclusive_gateway_multiple_true_conditions(self):
        from engines.orchestration.bpmn.gateway_handler import GatewayHandler
        handler = GatewayHandler()
        gateway = {
            "id": "gw1", "type": "inclusiveGateway",
            "branches": [
                {"target": "task_a", "condition": "x > 10", "priority": 0},
                {"target": "task_b", "condition": "y < 5", "priority": 1},
                {"target": "task_c", "condition": "z == 0", "priority": 2},
            ],
        }
        result = handler.choose(gateway=gateway, context={"x": 20, "y": 3, "z": 99})
        assert "task_a" in result.next_targets
        assert "task_b" in result.next_targets
        assert "task_c" not in result.next_targets


class TestEventBasedGateway:
    @pytest.mark.asyncio
    async def test_event_based_gateway_waits_for_events(self):
        from engines.orchestration.bpmn.gateway_handler import GatewayHandler
        handler = GatewayHandler()
        gateway = {
            "id": "gw1", "type": "eventBasedGateway",
            "branches": [
                {"target": "task_a", "event_type": "message"},
                {"target": "task_b", "event_type": "timer"},
            ],
        }
        result = handler.choose(gateway=gateway, context={})
        # Event-based gateway doesn't immediately select a path
        assert result.gateway_type == "eventBasedGateway"

    @pytest.mark.asyncio
    async def test_event_based_gateway_resolves_to_triggered_event(self):
        from engines.orchestration.bpmn.gateway_handler import GatewayHandler
        handler = GatewayHandler()
        gateway = {
            "id": "gw1", "type": "eventBasedGateway",
            "triggered_event": "message",
            "branches": [
                {"target": "task_a", "event_type": "message"},
                {"target": "task_b", "event_type": "timer"},
            ],
        }
        result = handler.choose(gateway=gateway, context={})
        assert result.next_targets == ["task_a"]
        assert result.event_triggered == "message"
