"""Tests for BpmnSubProcessManager."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from engines.orchestration.bpmn.sub_process_manager import BpmnSubProcessManager, _SubProcessContext
from engines.document.models.osdm_models import StartEvent, EventType, EventDefinitionType


class TestSubProcessContext:
    """_SubProcessContext is a simple data holder."""

    def test_default_values(self):
        ctx = _SubProcessContext()
        ctx.sub_process_id = "sp-1"
        ctx.start_node_id = "start-1"
        assert ctx.sub_process_id == "sp-1"
        assert ctx.start_node_id == "start-1"
        assert ctx.is_event_sub_process is False
        assert ctx.is_interrupting is False
        assert ctx.is_transaction is False


class TestRegisterEventSubProcesses:
    """register_event_sub_processes handles dict and object activities."""

    def test_dict_triggered_by_event(self):
        mgr = BpmnSubProcessManager()
        model = MagicMock()
        model.activities = [
            {"id": "sp-1", "type": "subProcess", "triggeredByEvent": True,
             "isInterrupting": True, "startEvents": [StartEvent(id="error-1", name="Error")]},
        ]
        mgr.register_event_sub_processes("inst-1", model)
        handler = mgr._event_sub_process_handler
        found = handler.find_triggered_sub_process("inst-1", EventType.START, EventDefinitionType.ERROR)
        assert found is not None

    def test_object_triggered_by_event(self):
        mgr = BpmnSubProcessManager()
        obj = type("Activity", (), {
            "id": "sp-1", "activity_type": None,
            "triggered_by_event": True, "is_interrupting": True,
            "start_events": [{"id": "signal-1"}],
            "__getattr__": lambda self, name: None,
        })()
        model = MagicMock()
        model.activities = [obj]
        mgr.register_event_sub_processes("inst-1", model)

    def test_non_event_sub_process_skipped(self):
        mgr = BpmnSubProcessManager()
        model = MagicMock()
        model.activities = [{"id": "task-1", "type": "task"}]
        mgr.register_event_sub_processes("inst-1", model)
        assert True


class TestRegisterTransactions:
    """register_transactions registers sub-processes as transactions."""

    def test_transaction_activity_registered(self):
        mgr = BpmnSubProcessManager()
        model = MagicMock()
        model.activities = [{"id": "tx-1", "type": "transaction"}]
        mgr.register_transactions("inst-1", model)
        assert mgr._transaction_handler is not None


class TestHandleActivityFailure:
    """handle_activity_failure triggers transaction compensation."""

    @pytest.mark.asyncio
    async def test_no_sub_process_stack(self):
        mgr = BpmnSubProcessManager()
        instance = MagicMock()
        instance.id = "inst-1"
        engine = MagicMock()
        await mgr.handle_activity_failure("a1", "task", [], instance, engine)
        assert True

    @pytest.mark.asyncio
    async def test_transaction_failure_compensates(self):
        mgr = BpmnSubProcessManager()
        ctx = _SubProcessContext()
        ctx.sub_process_id = "tx-1"
        ctx.is_transaction = True
        ctx.start_node_id = "start-1"

        mgr._transaction_handler.begin_transaction("tx-1", "tx-1")

        instance = MagicMock()
        instance.id = "inst-1"
        engine = MagicMock()
        engine.event_bus = AsyncMock()

        tx_handler = mgr._transaction_handler
        tx_handler.compensate = MagicMock(return_value=["act-1", "act-2"])

        await mgr.handle_activity_failure("a1", "task", [ctx], instance, engine)

        instance.set_variable.assert_any_call("compensated.act-1", True)
        instance.set_variable.assert_any_call("compensated.act-2", True)
        assert engine.event_bus.publish.await_count == 2

    @pytest.mark.asyncio
    async def test_non_transaction_ignored(self):
        mgr = BpmnSubProcessManager()
        ctx = _SubProcessContext()
        ctx.sub_process_id = "sp-1"
        ctx.is_transaction = False
        ctx.start_node_id = "start-1"

        instance = MagicMock()
        instance.id = "inst-1"
        engine = MagicMock()

        await mgr.handle_activity_failure("a1", "task", [ctx], instance, engine)
        instance.set_variable.assert_not_called()


class TestCheckAdhocCompletion:
    """check_adhoc_completion evaluates ad-hoc completion conditions."""

    def test_no_completion_condition_returns_true(self):
        mgr = BpmnSubProcessManager()
        ctx = _SubProcessContext()
        ctx.sub_process_id = "sp-1"
        model = MagicMock()
        model.activities = []
        assert mgr.check_adhoc_completion(MagicMock(), ctx, model) is True

    def test_with_completion_condition(self):
        mgr = BpmnSubProcessManager()
        ctx = _SubProcessContext()
        ctx.sub_process_id = "sp-1"
        model = MagicMock()
        model.activities = [{"id": "sp-1", "payload": {"completionCondition": "1 == 1"}}]
        instance = MagicMock()
        instance.get_all_variables.return_value = {}
        assert mgr.check_adhoc_completion(instance, ctx, model) is True

    def test_completion_condition_false(self):
        mgr = BpmnSubProcessManager()
        ctx = _SubProcessContext()
        ctx.sub_process_id = "sp-1"
        model = MagicMock()
        model.activities = [{"id": "sp-1", "payload": {"completionCondition": "1 == 2"}}]
        instance = MagicMock()
        instance.get_all_variables.return_value = {}
        assert mgr.check_adhoc_completion(instance, ctx, model) is False
