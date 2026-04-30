# engines/document/writers/osdm_writers/cncf_serverless_workflow_writer.py
"""
CNCF Serverless Workflow Writer – converts an OSDM StateMachineModel into
a CNCF Serverless Workflow JSON file.

The writer maps:
  - StateMachineModel → Workflow definition
  - State (with entry/do actions) → Operation state or Event state
  - StateTransition → transitions between states
  - TimeoutConfig → timeouts
  - ErrorHandlingConfig → error handling
  - CloudResourceBinding → function references
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, cast

from .base_osdm_writer import BaseOSDMWriter, OSDMWriteOptions
from ...models.osdm_models import (
    BaseOSDMDocument, StateMachineDocument,
    StateMachineModel,
    State,
    StateTransition,
    CloudResourceBinding,
    ErrorHandlingConfig,
    RetryConfig,
    TimeoutConfig,
    Script,
)
from ...models.base import BaseDocument


class CNCFServerlessWorkflowWriter(BaseOSDMWriter):
    """Serialises an OSDM StateMachineModel to CNCF Serverless Workflow JSON."""

    name = "cncf_serverless_workflow"
    supported_extensions = (".sw.json",)

    def __init__(self, options: Optional[OSDMWriteOptions] = None):
        super().__init__(options)

    async def _write_design(self, base_document: BaseOSDMDocument) -> bytes:
        document = cast(StateMachineDocument, base_document)
        if not document or not document.state_machines:
            workflow = {"id": "empty", "version": "1.0", "specVersion": "0.8", "states": []}
        else:
            sm = document.state_machines[0]
            workflow = self._build_workflow(sm)
        json_str = json.dumps(workflow, indent=2, ensure_ascii=False)
        return json_str.encode(self.options.encoding or "utf-8")

    def get_supported_media_types(self) -> list[str]:
        return ["application/json"]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    # ── Build Workflow ────────────────────────────────────────────
    def _build_workflow(self, sm: StateMachineModel) -> dict:
        workflow = {
            "id": sm.id,
            "name": sm.name or sm.id,
            "version": "1.0",
            "specVersion": "0.8",
            "start": self._resolve_initial_state(sm),
            "states": [],
        }
        all_states: List[State] = []
        self._collect_states(sm.top_region, all_states)

        for state in all_states:
            sw_state = self._state_to_sw(state)
            workflow["states"].append(sw_state)

        # Add transitions as state‑local `transition` or `onErrors` etc. (handled inside _state_to_sw)
        return workflow

    def _resolve_initial_state(self, sm: StateMachineModel) -> str:
        if sm.top_region.initial_state:
            return sm.top_region.initial_state.id
        if sm.top_region.states:
            return sm.top_region.states[0].id
        return "start"

    def _collect_states(self, region, all_states: List[State]):
        for state in region.states:
            all_states.append(state)
            for sub_region in state.regions:
                self._collect_states(sub_region, all_states)

    def _state_to_sw(self, state: State) -> dict:
        sw_state = {
            "name": state.id,
            "type": self._map_state_type(state),
        }
        # Cloud resource → function call
        if state.cloud_resource and state.cloud_resource.resource_arn:
            sw_state["type"] = "operation"
            sw_state["actions"] = [{
                "functionRef": {
                    "refName": state.cloud_resource.resource_arn.split(":")[-1] or "invoke",
                    "arguments": state.cloud_resource.parameters if state.cloud_resource.parameters else {}
                }
            }]
        # Script → inline action
        elif (state.entry_actions or state.do_actions) and any(isinstance(a, Script) for a in (state.entry_actions + state.do_actions)):
            script = next(a for a in (state.entry_actions + state.do_actions) if isinstance(a, Script))
            sw_state["type"] = "operation"
            sw_state["actions"] = [{
                "functionRef": {
                    "refName": "inlineScript",
                    "arguments": {"code": script.script_body}
                }
            }]
        # Timeout
        if state.timeout:
            sw_state["timeouts"] = {
                "stateExecTimeout": f"PT{state.timeout.timeout_seconds}S"
            }
        # Error handling
        if state.error_handling:
            sw_state["onErrors"] = []
            for err_eq in state.error_handling.error_equals:
                sw_state["onErrors"].append({
                    "error": err_eq,
                    "end": True  # or transition to another state
                })
        # Transitions
        if state.outgoing_transitions:
            if len(state.outgoing_transitions) == 1 and not state.outgoing_transitions[0].condition:
                sw_state["transition"] = {"nextState": state.outgoing_transitions[0].target.id}
            elif len(state.outgoing_transitions) > 1:
                sw_state["type"] = "switch"
                conditions = []
                default_transition = None
                for trans in state.outgoing_transitions:
                    if trans.condition:
                        conditions.append({
                            "path": "$.someVariable",   # we would need to parse condition
                            "value": trans.condition.body,
                            "operator": "equals",
                            "transition": {"nextState": trans.target.id}
                        })
                    else:
                        default_transition = trans
                if conditions:
                    sw_state["dataConditions"] = conditions
                    if default_transition:
                        sw_state["defaultCondition"] = {"transition": {"nextState": default_transition.target.id}}
        # End state if no outgoing transitions
        if not sw_state.get("transition") and not sw_state.get("dataConditions"):
            sw_state["end"] = True
        return sw_state

    def _map_state_type(self, state: State) -> str:
        if state.workflow_state_type is not None:
            return state.workflow_state_type.value
        # Fallback heuristic
        if state.outgoing_transitions and len(state.outgoing_transitions) > 1:
            return WorkflowStateType.SWITCH.value
        if state.timeout and not state.entry_actions:
            return WorkflowStateType.DELAY.value
        return WorkflowStateType.OPERATION.value    
