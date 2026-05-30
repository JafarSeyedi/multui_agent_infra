from __future__ import annotations

from datetime import datetime

import pytest

from engines.orchestration.bpmn.engine import BPMNEngine
from engines.orchestration.core.engine import OrchestrationEngine, ProcessDefinition
from engines.orchestration.core.instance import InstanceState
from engines.orchestration.persistence.event_repository import EventRepository
from engines.orchestration.persistence.history_repository import HistoryRepository
from engines.orchestration.persistence.instance_repository import InstanceRepository
from engines.orchestration.persistence.token_repository import TokenRepository
from engines.orchestration.persistence.variable_repository import VariableRepository


def _definition(
    *,
    key: str,
    definition_xml: dict,
) -> ProcessDefinition:
    return ProcessDefinition(
        id=f"{key}-id",
        key=key,
        name=key,
        version=1,
        deployment_id=f"{key}-deployment",
        resource_name=f"{key}.bpmn",
        diagram_resource_name=None,
        has_start_form_key=False,
        has_graphical_notation=True,
        is_suspended=False,
        tenant_id=None,
        version_tag=None,
        history_time_to_live=None,
        is_startable_in_tasklist=True,
        definition_type="bpmn",
        definition_xml=definition_xml,
        deployed_at=datetime.utcnow(),
    )


@pytest.mark.asyncio
async def test_bpmn_completed_path_persists_token_variable_and_events() -> None:
    engine = OrchestrationEngine(
        event_repository=EventRepository(),
        history_repository=HistoryRepository(),
        instance_repository=InstanceRepository(),
        variable_repository=VariableRepository(),
        token_repository=TokenRepository(),
    )
    engine.register_engine_handler("bpmn", BPMNEngine(engine))

    definition = _definition(
        key="simple-process",
        definition_xml={
            "id": "simple-process",
            "start_event_id": "task_1",
            "activities": [
                {"id": "task_1", "type": "serviceTask", "payload": {"result": "ok"}},
            ],
            "flows": [],
        },
    )
    engine.definitions[definition.key] = definition
    engine.definition_versions[definition.key] = [definition]

    instance = await engine.start_process_instance(definition.key)

    assert instance.state == InstanceState.COMPLETED
    assert engine.variable_manager.get("task_1.output") == {"result": "ok"}

    tokens = engine.token_manager.get_instance_tokens(instance.id)
    assert len(tokens) == 1
    assert tokens[0].is_completed()

    history = engine.event_bus.get_event_history(limit=20)
    event_types = [event.type.value for event in history]
    assert "activity.started" in event_types
    assert "activity.completed" in event_types


@pytest.mark.asyncio
async def test_bpmn_message_wait_path_persists_waiting_token_and_subscription() -> None:
    engine = OrchestrationEngine(
        event_repository=EventRepository(),
        history_repository=HistoryRepository(),
        instance_repository=InstanceRepository(),
        variable_repository=VariableRepository(),
        token_repository=TokenRepository(),
    )
    engine.register_engine_handler("bpmn", BPMNEngine(engine))

    definition = _definition(
        key="message-wait-process",
        definition_xml={
            "id": "message-wait-process",
            "start_event_id": "wait_1",
            "activities": [
                {
                    "id": "wait_1",
                    "type": "intermediateCatch",
                    "payload": {
                        "message_name": "OrderApproved",
                        "correlation_keys": {"order_id": "order_id"},
                    },
                }
            ],
            "flows": [],
        },
    )
    engine.definitions[definition.key] = definition
    engine.definition_versions[definition.key] = [definition]

    instance = await engine.start_process_instance(definition.key, variables={"order_id": "order-1"})

    snapshot = engine.state_manager.get(instance.id)
    assert snapshot is not None
    assert snapshot.state == "waiting"

    tokens = engine.token_manager.get_instance_tokens(instance.id)
    assert len(tokens) == 1
    assert tokens[0].is_waiting()

    subscriptions = engine.correlation_engine.instance_message_subs.get(instance.id, set())
    assert len(subscriptions) == 1
