from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from engines.orchestration.core.correlation import CorrelationKeySet
from engines.orchestration.core.event_bus import Event, EventBus, EventType
from engines.orchestration.core.engine import OrchestrationEngine, ProcessDefinition
from engines.orchestration.persistence.definition_repository import DefinitionRepository
from engines.orchestration.core.instance import InstanceState, ProcessInstance
from engines.orchestration.core.scheduler import Scheduler
from engines.orchestration.persistence.event_repository import EventRepository
from engines.orchestration.persistence.history_repository import HistoryRepository
from engines.orchestration.persistence.instance_repository import InstanceRepository
from engines.orchestration.persistence.token_repository import TokenRepository
from engines.orchestration.persistence.variable_repository import VariableRepository
from engines.orchestration.runtime.variable_manager import VariableManager


@pytest.mark.asyncio
async def test_variable_manager_persists_and_restores_scope() -> None:
    repository = VariableRepository()
    manager = VariableManager(repository=repository)

    await manager.set_persisted("inst-1", "scope-a", "answer", 42, value_type="integer")
    manager.clear()

    restored = await manager.restore_persisted("inst-1", "scope-a")

    assert restored == {"answer": 42}
    assert manager.get("answer") == 42


@pytest.mark.asyncio
async def test_event_bus_replays_filtered_events() -> None:
    repository = EventRepository()
    bus = EventBus(event_repository=repository)

    first = Event(type=EventType.MESSAGE_SENT, data={"instance_id": "i-1"}, correlation_id="corr-1")
    second = Event(type=EventType.TASK_COMPLETED, data={"instance_id": "i-1"}, correlation_id="corr-2")

    await bus.publish_sync(first)
    await bus.publish_sync(second)

    replayed = await bus.replay_events(event_type=EventType.MESSAGE_SENT, correlation_id="corr-1")

    assert len(replayed) == 1
    assert replayed[0].type == EventType.MESSAGE_SENT
    assert replayed[0].correlation_id == "corr-1"


@pytest.mark.asyncio
async def test_scheduler_reload_restores_pending_jobs_from_history() -> None:
    history_repository = HistoryRepository()
    scheduler = Scheduler(history_repository=history_repository)
    task_id = scheduler.schedule_once(
        "demo",
        lambda _task: None,
        datetime.utcnow() + timedelta(minutes=5),
        metadata={"instance_id": "inst-2"},
    )

    task = scheduler.get_task(task_id)
    assert task is not None
    await scheduler._persist_task_state(task, "job.pending")

    restored_scheduler = Scheduler(history_repository=history_repository)
    restored = await restored_scheduler.reload_tasks_from_history("inst-2")

    assert len(restored) == 1
    assert restored[0].task_id == task_id
    assert restored[0].name == "demo"


@pytest.mark.asyncio
async def test_engine_recovery_hydrates_definitions_instances_tokens_and_variables() -> None:
    instance_repository = InstanceRepository()
    token_repository = TokenRepository()
    variable_repository = VariableRepository()
    event_repository = EventRepository()

    definition = ProcessDefinition(
        id="def-1",
        key="order-process",
        name="Order Process",
        version=1,
        deployment_id="dep-1",
        resource_name="order.bpmn",
        diagram_resource_name=None,
        has_start_form_key=False,
        has_graphical_notation=True,
        is_suspended=False,
        tenant_id=None,
        version_tag=None,
        history_time_to_live=None,
        is_startable_in_tasklist=True,
        definition_type="bpmn",
        definition_xml="<bpmn id='order-process' />",
        deployed_at=datetime.utcnow(),
    )

    definition_repository = DefinitionRepository()

    engine = OrchestrationEngine(
        definition_repository=definition_repository,
        event_repository=event_repository,
        instance_repository=instance_repository,
        variable_repository=variable_repository,
        token_repository=token_repository,
    )
    engine.definition_repository.save(definition.id, engine._definition_to_dict(definition))

    instance = ProcessInstance(
        id="inst-3",
        definition_id=definition.id,
        definition_key=definition.key,
        definition_version=definition.version,
    )
    engine.instance_manager.add_instance(instance)
    await engine.instance_manager.persist_instance(instance.id)

    token = engine.token_manager.create_token(instance.id, current_element_id="start")
    await engine.token_manager.persist_token(token.token_id)
    await engine.variable_manager.set_persisted(instance.id, instance.id, "customer_id", "c-1")
    await event_repository.append_persisted(
        Event(type=EventType.PROCESS_INSTANCE_STARTED, data={"instance_id": instance.id}).to_record_payload()
    )

    recovered = OrchestrationEngine(
        definition_repository=definition_repository,
        event_repository=event_repository,
        instance_repository=instance_repository,
        variable_repository=variable_repository,
        token_repository=token_repository,
    )
    await recovered._recover_runtime_state()

    assert definition.key in recovered.definitions
    assert instance.id in recovered.instances
    assert recovered.variable_manager.get("customer_id") == "c-1"
    recovered_tokens = recovered.token_manager.get_instance_tokens(instance.id)
    assert len(recovered_tokens) == 1
    assert recovered_tokens[0].current_element_id == "start"


@pytest.mark.asyncio
async def test_engine_state_transition_persists_snapshot_and_history_reload() -> None:
    history_repository = HistoryRepository()
    engine = OrchestrationEngine(history_repository=history_repository)
    definition = ProcessDefinition(
        id="def-2",
        key="invoice-process",
        name="Invoice Process",
        version=1,
        deployment_id="dep-2",
        resource_name="invoice.bpmn",
        diagram_resource_name=None,
        has_start_form_key=False,
        has_graphical_notation=True,
        is_suspended=False,
        tenant_id=None,
        version_tag=None,
        history_time_to_live=None,
        is_startable_in_tasklist=True,
        definition_type="bpmn",
        definition_xml="<bpmn id='invoice-process' />",
        deployed_at=datetime.utcnow(),
    )
    engine.definitions[definition.key] = definition

    instance = await engine.start_process_instance(definition.key, variables={"amount": 10})
    await engine.update_instance_state(instance.id, InstanceState.SUSPENDED, reason="manual pause")

    snapshot = engine.state_manager.get(instance.id)
    assert snapshot is not None
    assert snapshot.state == InstanceState.SUSPENDED.value

    scheduler = Scheduler(history_repository=history_repository)
    task_id = scheduler.schedule_once(
        "resume-check",
        lambda _task: None,
        datetime.utcnow() + timedelta(minutes=1),
        metadata={"instance_id": instance.id},
    )
    task = scheduler.get_task(task_id)
    assert task is not None
    await scheduler._persist_task_state(task, "job.pending")

    restored = await engine.scheduler.reload_tasks_from_history(instance.id)
    assert len(restored) == 1
    assert restored[0].task_id == task_id


@pytest.mark.asyncio
async def test_correlation_engine_recovers_message_and_event_subscriptions() -> None:
    history_repository = HistoryRepository()
    engine = OrchestrationEngine(history_repository=history_repository)

    keys = CorrelationKeySet()
    keys.add_key("order_id", "123")

    message_sub_id = await engine.correlation_engine.subscribe_message_persisted(
        "OrderApproved",
        keys,
        "inst-4",
        "activity-a",
    )
    event_sub_id = await engine.correlation_engine.subscribe_event_persisted(
        "InvoiceSignal",
        "inst-4",
        "activity-b",
    )
    await engine.correlation_engine.correlate_message("UnmatchedMessage", keys, {"value": 1}, ttl_seconds=60)

    recovered = OrchestrationEngine(history_repository=history_repository)
    await recovered.correlation_engine.reload_from_history()

    assert message_sub_id in recovered.correlation_engine.message_subscriptions
    assert event_sub_id in recovered.correlation_engine.event_subscriptions
    assert len(recovered.correlation_engine.buffered_messages) == 1
    assert recovered.correlation_engine.buffered_messages[0].message_name == "UnmatchedMessage"


@pytest.mark.asyncio
async def test_delete_instance_cleans_up_persisted_correlation_subscriptions() -> None:
    history_repository = HistoryRepository()
    engine = OrchestrationEngine(history_repository=history_repository)
    definition = ProcessDefinition(
        id="def-3",
        key="shipment-process",
        name="Shipment Process",
        version=1,
        deployment_id="dep-3",
        resource_name="shipment.bpmn",
        diagram_resource_name=None,
        has_start_form_key=False,
        has_graphical_notation=True,
        is_suspended=False,
        tenant_id=None,
        version_tag=None,
        history_time_to_live=None,
        is_startable_in_tasklist=True,
        definition_type="bpmn",
        definition_xml="<bpmn id='shipment-process' />",
        deployed_at=datetime.utcnow(),
    )
    engine.definitions[definition.key] = definition

    instance = await engine.start_process_instance(definition.key)
    keys = CorrelationKeySet()
    keys.add_key("shipment_id", "s-1")
    await engine.correlation_engine.subscribe_message_persisted("ShipmentReady", keys, instance.id, "wait-message")
    await engine.correlation_engine.subscribe_event_persisted("ShipmentSignal", instance.id, "wait-signal")

    await engine.delete_instance(instance.id, "cleanup")

    recovered = OrchestrationEngine(history_repository=history_repository)
    await recovered.correlation_engine.reload_from_history()

    assert recovered.correlation_engine.instance_message_subs.get(instance.id, set()) == set()
    assert recovered.correlation_engine.instance_event_subs.get(instance.id, set()) == set()
