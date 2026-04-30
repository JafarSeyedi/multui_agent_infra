# engines/document/parsers/osdm_parsers/cncf_serverless_workflow_parser.py
"""
CNCF Serverless Workflow Parser – converts a CNCF Serverless Workflow JSON/YAML
file into a StateMachineDocument (unified OSDM model).

Mapping rules:
- Workflow → StateMachineModel
- Start state → top_region.initial_state
- States (operation, event, switch, delay, parallel, foreach, inject, callback, subFlow)
  → OSDM State with appropriate type stored in state_type annotation (to preserve round‑trip).
- Transitions (transition, defaultCondition, eventConditions, etc.) → StateTransition
- Data filters (actionDataFilter, eventDataFilter, stateDataFilter) are stored as Script
  objects in entry_actions / exit_actions.
- Error handling (retryable, nonRetryable, compensation) is stored in RetryConfig /
  ErrorHandlingConfig if applicable, otherwise as annotations.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Union

import yaml  # requires PyYAML; fallback to json if not available

from .base_osdm_parser import BaseOSDMParser
from ..base import ParseOptions
from ...models.osdm_models import (
    BaseOSDMDocument,
    StateMachineDocument,
    StateMachineModel,
    StateMachineRegion,
    State,
    StateTransition,
    Script,
    ScriptLanguage,
    RetryConfig,
    ErrorHandlingConfig,
    TimeoutConfig,
    FormalExpression,
    WorkflowStateType
)
from ...models.base import BaseDocument


class CNCFServerlessWorkflowParser(BaseOSDMParser):
    """Parser for CNCF Serverless Workflow files (.sw.json, .sw.yaml, .sw.yml)."""

    name = "cncf_serverless_workflow"
    supported_extensions = (".sw.json", ".sw.yaml", ".sw.yml")

    async def _parse_to_document(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> BaseOSDMDocument:
        encoding = options.encoding or "utf-8"
        text = data.decode(encoding)

        # Try JSON first, then YAML
        try:
            wf = json.loads(text)
        except json.JSONDecodeError:
            try:
                wf = yaml.safe_load(text)
            except Exception:
                raise ValueError("Invalid CNCF Serverless Workflow: not valid JSON or YAML")

        doc = StateMachineDocument()
        sm = self._build_state_machine(wf)
        doc.state_machines.append(sm)
        return doc

    def _build_state_machine(self, wf: dict) -> StateMachineModel:
        sm = StateMachineModel(
            id=wf.get("id", ""),
            name=wf.get("name", ""),
        )
        top_region = StateMachineRegion()
        sm.top_region = top_region

        # Parse states
        states = wf.get("states", [])
        state_map: Dict[str, State] = {}

        # First pass: create all states
        for state_def in states:
            st = self._parse_state(state_def)
            state_map[st.id] = st
            top_region.states.append(st)

        # Second pass: resolve transitions (usually within each state definition)
        for state_def in states:
            state_name = state_def["name"]
            source = state_map.get(state_name)
            if source is None:
                continue

            # Transition (simple Next state)
            transition = state_def.get("transition")
            if transition:
                next_state = transition if isinstance(transition, str) else transition.get("nextState")
                if next_state and next_state in state_map:
                    trans = StateTransition(
                        id=f"{state_name}->{next_state}",
                        source=source,
                        target=state_map[next_state],
                    )
                    top_region.transitions.append(trans)

            # Event state transitions
            if state_def.get("type") == "event":
                on_events = state_def.get("onEvents", [])
                for ev in on_events:
                    event_refs = ev.get("eventRefs", [])
                    actions = ev.get("actions", [])
                    # Each action may have a transition
                    for action in actions:
                        action_next = action.get("transition")
                        if action_next and action_next in state_map:
                            trans = StateTransition(
                                id=f"{state_name}_event_{action_next}",
                                source=source,
                                target=state_map[action_next],
                            )
                            top_region.transitions.append(trans)

            # Switch state transitions
            if state_def.get("type") == "switch":
                data_conditions = state_def.get("dataConditions", [])
                event_conditions = state_def.get("eventConditions", [])
                for cond in data_conditions + event_conditions:
                    cond_next = cond.get("transition")
                    if cond_next and cond_next in state_map:
                        guard = cond.get("condition")
                        trans = StateTransition(
                            id=f"{state_name}_switch_{cond_next}",
                            source=source,
                            target=state_map[cond_next],
                            guard=FormalExpression(body=guard) if guard else None,
                        )
                        top_region.transitions.append(trans)
                default_cond = state_def.get("defaultCondition")
                if default_cond and default_cond.get("transition") in state_map:
                    def_next = default_cond["transition"]
                    trans = StateTransition(
                        id=f"{state_name}_default_{def_next}",
                        source=source,
                        target=state_map[def_next],
                    )
                    top_region.transitions.append(trans)

        # Set initial state
        start = wf.get("start")
        if isinstance(start, str):
            start_state_name = start
        elif isinstance(start, dict):
            start_state_name = start.get("stateName")
        else:
            start_state_name = None

        if start_state_name and start_state_name in state_map:
            top_region.initial_state = state_map[start_state_name]

        return sm

    def _parse_state(self, state_def: dict) -> State:
        name = state_def.get("name", "")
        state_type = state_def.get("type", "operation")
        st = State(id=name, name=name)
        # Store state type as annotation for round‑trip
        st.workflow_state_type = WorkflowStateType(state_type)

        # Timeouts
        timeout_str = state_def.get("timeDuration")
        if timeout_str:
            seconds = self._parse_iso8601_duration(timeout_str)
            st.timeout = TimeoutConfig(timeout_seconds=seconds)

        # Error handling (retryable, nonRetryable, compensation)
        error_handling = state_def.get("errorHandling")
        if error_handling:
            # We'll store the whole error handling definition as a Script for round‑trip
            script_body = json.dumps(error_handling)
            st.entry_actions.append(Script(script_body=script_body, script_language=ScriptLanguage.JSON))

        # Data filters
        data_filter = state_def.get("stateDataFilter")
        if data_filter:
            script_body = json.dumps(data_filter)
            st.do_actions.append(Script(script_body=script_body, script_language=ScriptLanguage.JSON))

        # Action (for operation states)
        action = state_def.get("action")
        if action:
            # Store action as a Script
            script_body = json.dumps(action)
            st.do_actions.append(Script(script_body=script_body, script_language=ScriptLanguage.JSON))

        # SubFlow state
        if state_type == "subFlow":
            subflow_name = state_def.get("workflowId", "")
            st.do_actions.append(Script(script_body=f"subflow:{subflow_name}", script_language=ScriptLanguage.JSON))

        # Inject state
        if state_type == "inject":
            inject_data = state_def.get("data", {})
            st.do_actions.append(Script(script_body=json.dumps(inject_data), script_language=ScriptLanguage.JSON))

        # Callback state
        if state_type == "callback":
            callback_action = state_def.get("action", {})
            st.do_actions.append(Script(script_body=json.dumps(callback_action), script_language=ScriptLanguage.JSON))

        # Foreach state
        if state_type == "foreach":
            input_collection = state_def.get("inputCollection", "")
            iteration_param = state_def.get("iterationParam", "")
            st.do_actions.append(Script(
                script_body=f"foreach {iteration_param} in {input_collection}",
                script_language=ScriptLanguage.JSON,
            ))

        # Sleep state
        if state_type == "sleep":
            duration = state_def.get("duration", "")
            st.timeout = TimeoutConfig(timeout_seconds=self._parse_iso8601_duration(duration))

        # Parallel state
        if state_type == "parallel":
            branches = state_def.get("branches", [])
            # Each branch becomes a sub‑region
            for branch in branches:
                sub_sm = self._build_state_machine(branch)
                sub_region = StateMachineRegion(
                    states=sub_sm.top_region.states,
                    transitions=sub_sm.top_region.transitions,
                    initial_state=sub_sm.top_region.initial_state,
                )
                st.regions.append(sub_region)

        return st

    @staticmethod
    def _parse_iso8601_duration(duration_str: str) -> int:
        """Parse ISO 8601 duration like 'PT1H30M' to seconds. Simplified."""
        import re
        total = 0
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
        if match:
            h, m, s = (int(x) if x else 0 for x in match.groups())
            total = h * 3600 + m * 60 + s
        return total


# Missing import inside the module:
from ...models.osdm_models import Annotation