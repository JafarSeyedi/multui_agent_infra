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
    definition_xml: str,
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

    bpmn_xml = """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" id="Definitions_1" targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:process id="simple-process" isExecutable="true">
    <bpmn:startEvent id="start1" name="Start"/>
    <bpmn:sequenceFlow id="flow1" sourceRef="start1" targetRef="task_1"/>
    <bpmn:serviceTask id="task_1" name="Task 1">
      <bpmn:extensionElements>
        <bpmn:outputParameters>
          <bpmn:outputParameter name="result">ok</bpmn:outputParameter>
        </bpmn:outputParameters>
      </bpmn:extensionElements>
    </bpmn:serviceTask>
    <bpmn:endEvent id="end1" name="End"/>
    <bpmn:sequenceFlow id="flow2" sourceRef="task_1" targetRef="end1"/>
  </bpmn:process>
</bpmn:definitions>"""
    definition = _definition(
        key="simple-process",
        definition_xml=bpmn_xml,
    )
    engine.definitions[definition.key] = definition
    engine.definition_versions[definition.key] = [definition]

    instance = await engine.start_process_instance(definition.key)

    assert instance.state == InstanceState.COMPLETED

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

    bpmn_xml = """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" id="Definitions_1" targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:process id="message-wait-process" isExecutable="true">
    <bpmn:startEvent id="start1" name="Start"/>
    <bpmn:sequenceFlow id="flow1" sourceRef="start1" targetRef="wait_1"/>
    <bpmn:intermediateCatchEvent id="wait_1" name="Wait for Approval">
      <bpmn:messageEventDefinition messageRef="OrderApproved"/>
    </bpmn:intermediateCatchEvent>
    <bpmn:endEvent id="end1" name="End"/>
    <bpmn:sequenceFlow id="flow2" sourceRef="wait_1" targetRef="end1"/>
  </bpmn:process>
</bpmn:definitions>"""
    definition = _definition(
        key="message-wait-process",
        definition_xml=bpmn_xml,
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
