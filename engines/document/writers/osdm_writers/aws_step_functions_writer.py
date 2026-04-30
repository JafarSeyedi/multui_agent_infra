# engines/document/writers/osdm_writers/aws_step_functions_writer.py
"""
AWS Step Functions Writer – converts an OSDM StateMachineModel (extended with
cloud‑native fields) into an Amazon States Language (ASL) JSON file.

The writer expects the state machine to have CloudResourceBinding, ErrorHandlingConfig,
RetryConfig, and TimeoutConfig attached to individual States.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, cast

from .base_osdm_writer import BaseOSDMWriter, OSDMWriteOptions, VersionStrategy
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


class AWSStepFunctionsWriter(BaseOSDMWriter):
    """Serialises an OSDM StateMachineModel to AWS Step Functions ASL JSON."""

    name = "aws_step_functions"
    supported_extensions = (".asl.json",)

    def __init__(self, options: Optional[OSDMWriteOptions] = None):
        super().__init__(options)

    async def _write_design(self, base_document: BaseOSDMDocument) -> bytes:
        # The document may contain multiple state machines; we write the first one
        # or an array if multiple. For ASL, a single state machine is typical.
        document = cast(StateMachineDocument, base_document)
        if not document or not document.state_machines:
            asl = {"Comment": "No state machine defined."}
        else:
            # Take the first state machine (or we could write an array if needed)
            sm = document.state_machines[0]
            asl = self._build_asl(sm)
        json_str = json.dumps(asl, indent=2, ensure_ascii=False)
        return json_str.encode(self.options.encoding or "utf-8")

    def get_supported_media_types(self) -> list[str]:
        return ["application/json"]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    # ── Build ASL structure ────────────────────────────────────────
    def _build_asl(self, sm: StateMachineModel) -> dict:
        asl = {
            "Comment": sm.name or sm.id,
            "StartAt": self._resolve_initial_state(sm),
        }
        states = {}
        # Collect all states from the region recursively
        self._collect_states(sm.top_region, states)
        asl["States"] = states
        # If there is a timeout or error handling at the top level, we could add a top-level Catch/TimeoutSeconds
        # but that is not directly mapped in the model; we rely on state-level configurations.
        return asl

    def _resolve_initial_state(self, sm: StateMachineModel) -> str:
        if sm.top_region.initial_state:
            return sm.top_region.initial_state.id
        # Fallback: first pseudo-state or first state
        if sm.pseudo_states and sm.pseudo_states[0].kind == "initial":
            # Pseudo-state initial points to a target state? Not directly, we need a transition.
            # In ASL, StartAt must be a state name. We'll use the first actual state.
            pass
        if sm.top_region.states:
            return sm.top_region.states[0].id
        return "Unknown"

    def _collect_states(self, region, states_dict: Dict[str, dict]):
        # Recurse into regions and states
        for state in region.states:
            st = self._state_to_asl(state)
            states_dict[state.id] = st
            for sub_region in state.regions:
                self._collect_states(sub_region, states_dict)
        # Also handle the region's initial state not being a pseudo-state? Already covered.

    def _state_to_asl(self, state: State) -> dict:
        """Convert a single OSDM State to an ASL state object."""
        asl_state = {
            "Type": self._map_state_type(state),
        }
        # Resource binding (for Task states)
        if state.cloud_resource and state.cloud_resource.resource_arn:
            asl_state["Resource"] = state.cloud_resource.resource_arn
            if state.cloud_resource.parameters:
                asl_state["Parameters"] = state.cloud_resource.parameters
        # Timeout
        if state.timeout:
            asl_state["TimeoutSeconds"] = state.timeout.timeout_seconds
            if state.timeout.heartbeat_seconds:
                asl_state["HeartbeatSeconds"] = state.timeout.heartbeat_seconds
        # Error handling (Catch)
        if state.error_handling:
            catches = []
            for err_eq in state.error_handling.error_equals:
                catch_entry = {
                    "ErrorEquals": [err_eq] if not isinstance(err_eq, list) else err_eq,
                    "Next": state.error_handling.next_state.id if state.error_handling.next_state else "Fail",
                }
                if state.error_handling.result_path:
                    catch_entry["ResultPath"] = state.error_handling.result_path
                catches.append(catch_entry)
            if catches:
                asl_state["Catch"] = catches
        # Retry
        if state.retry:
            retriers = [{
                "ErrorEquals": state.retry.error_equals,
                "IntervalSeconds": state.retry.interval_seconds,
                "MaxAttempts": state.retry.max_attempts,
                "BackoffRate": state.retry.backoff_rate,
            }]
            asl_state["Retry"] = retriers
        # Transitions
        if state.outgoing_transitions:
            # ASL uses "Next" for a single outgoing transition, or "Choices" for multiple.
            # If there is exactly one outgoing transition and no condition, it's a simple "Next".
            if len(state.outgoing_transitions) == 1:
                trans = state.outgoing_transitions[0]
                if trans.condition is None and trans.target:
                    asl_state["Next"] = trans.target.id
                else:
                    # If there is a condition, we must use a Choice state? ASL Choice states are separate.
                    # We'll treat state with a single conditional transition as a Choice? Not ideal, but for now skip.
                    pass
            elif len(state.outgoing_transitions) > 1:
                # It must be a Choice state. We'll convert to Choice with rules.
                choices = []
                for trans in state.outgoing_transitions:
                    if trans.condition:
                        rule = {
                            "Variable": "$.somevariable",  # we would need to parse the condition
                            "StringEquals": trans.condition.body,  # simplified
                            "Next": trans.target.id,
                        }
                        choices.append(rule)
                if choices:
                    asl_state["Type"] = "Choice"
                    asl_state["Choices"] = choices
                    # Set default
                    # (find transition without condition and use as Default)
                    default_trans = next((t for t in state.outgoing_transitions if not t.condition), None)
                    if default_trans and default_trans.target:
                        asl_state["Default"] = default_trans.target.id
        # End state
        if not asl_state.get("Next") and not asl_state.get("Choices"):
            asl_state["End"] = True
        # Input/output processing (optional)
        if state.entry_actions:
            # Could be mapped to InputPath, ResultPath, etc. but we ignore for now.
            pass
        return asl_state

    def _map_state_type(self, state: State) -> str:
        """Determine ASL state type based on OSDM State properties."""
        # If cloud resource is set → Task
        if state.cloud_resource and state.cloud_resource.resource_arn:
            return "Task"
        # If there are multiple outgoing transitions → Choice (we already set in _state_to_asl)
        if len(state.outgoing_transitions) > 1:
            return "Choice"
        # If there is a single outgoing transition with a condition → Choice
        if len(state.outgoing_transitions) == 1 and state.outgoing_transitions[0].condition:
            return "Choice"
        # If the state has a timeout but no other work → Wait
        if state.timeout and not state.entry_actions and not state.do_actions:
            return "Wait"
        # If the state has entry actions that take time? Could be a Task with a heartbeat? We'll use Pass for now.
        if state.entry_actions or state.do_actions:
            return "Pass"
        # Default
        return "Pass"