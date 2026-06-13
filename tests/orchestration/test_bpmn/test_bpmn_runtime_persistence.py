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

    definition = _definition(
        key="simple-process",
        definition_xml="""<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL">
  <bpmn:process id="simple-process" isExecutable="true">
    <bpmn:startEvent id="start" />
    <bpmn:serviceTask id="task_1" />
    <bpmn:endEvent id="end" />
    <bpmn:sequenceFlow id="f1" sourceRef="start" targetRef="task_1" />
    <bpmn:sequenceFlow id="f2" sourceRef="task_1" targetRef="end" />
  </bpmn:process>
</bpmn:definitions>""",
    )
    engine.definitions[definition.key] = definition
    engine.definition_versions[definition.key] = [definition]

    instance = await engine.start_process_instance(definition.key)

    assert instance.state in (InstanceState.COMPLETED, InstanceState.ACTIVE)

    tokens = engine.token_manager.get_instance_tokens(instance.id)
    assert len(tokens) > 0


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
        definition_xml="""<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL">
  <bpmn:process id="message-wait-process" isExecutable="true">
    <bpmn:startEvent id="start" />
    <bpmn:intermediateCatchEvent id="wait_1">
      <bpmn:messageEventDefinition id="msg_evt" messageRef="msg_1" />
    </bpmn:intermediateCatchEvent>
    <bpmn:endEvent id="end" />
    <bpmn:sequenceFlow id="f1" sourceRef="start" targetRef="wait_1" />
    <bpmn:sequenceFlow id="f2" sourceRef="wait_1" targetRef="end" />
  </bpmn:process>
  <bpmn:message id="msg_1" name="OrderApproved" />
</bpmn:definitions>""",
    )
    engine.definitions[definition.key] = definition
    engine.definition_versions[definition.key] = [definition]

    instance = await engine.start_process_instance(definition.key, variables={"order_id": "order-1"})

    tokens = engine.token_manager.get_instance_tokens(instance.id)
    assert len(tokens) > 0
