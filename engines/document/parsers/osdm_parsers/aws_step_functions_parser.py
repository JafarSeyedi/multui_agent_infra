# engines/document/parsers/osdm_parsers/aws_step_functions_parser.py
"""
AWS Step Functions Parser – converts an ASL JSON file into a
StateMachineDocument (unified OSDM model).

Every ASL state type is mapped to OSDM:
- Task → State with cloud_resource (Lambda/ECS ARN) + error handling / retry / timeout
- Choice → State with multiple StateTransitions (each with a guard expression)
- Wait → State with timeout
- Parallel / Map → State with nested regions (sub‑states)
- Pass / Succeed / Fail → plain State with appropriate entry/exit actions
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Union

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
    CloudResourceBinding,
    ErrorHandlingConfig,
    RetryConfig,
    TimeoutConfig,
    FormalExpression,
)
from ...models.base import BaseDocument


class AWSStepFunctionsParser(BaseOSDMParser):
    """Parser for AWS Step Functions ASL JSON files (.asl.json)."""

    name = "aws_step_functions"
    supported_extensions = (".asl.json",)

    async def _parse_to_document(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> BaseOSDMDocument:
        text = data.decode(options.encoding or "utf-8")
        asl = json.loads(text)

        doc = StateMachineDocument()

        # ASL files typically contain a single state machine
        sm = self._build_state_machine(asl)
        doc.state_machines.append(sm)
        return doc

    # ── Top‑level state machine ────────────────────────────────────
    def _build_state_machine(self, asl: dict) -> StateMachineModel:
        sm = StateMachineModel(
            id=asl.get("Comment", "aws_step_functions"),
            name=asl.get("Comment", "aws_step_functions"),
        )
        start_at = asl.get("StartAt")
        states = asl.get("States", {})

        top_region = StateMachineRegion()
        sm.top_region = top_region

        # Temporary map of state name → State
        state_map: Dict[str, State] = {}

        # First pass: create all states
        for state_name, state_def in states.items():
            st = self._parse_state(state_name, state_def)
            state_map[state_name] = st
            top_region.states.append(st)

        # Second pass: link transitions (Next, Choices, Catch next_state)
        for state_name, state_def in states.items():
            source = state_map[state_name]
            st_type = state_def.get("Type", "Pass")

            # Simple Next
            next_state = state_def.get("Next")
            if next_state and next_state in state_map:
                trans = StateTransition(
                    id=f"{state_name}->{next_state}",
                    source=source,
                    target=state_map[next_state],
                )
                top_region.transitions.append(trans)

            # End state
            if state_def.get("End", False):
                pass  # no transition

            # Choice state
            if st_type == "Choice":
                choices = state_def.get("Choices", [])
                for choice in choices:
                    next_choice = choice.get("Next")
                    if next_choice and next_choice in state_map:
                        # Build a guard expression from the choice rule
                        guard_body = self._choice_to_expression(choice)
                        trans = StateTransition(
                            id=f"{state_name}->{next_choice}",
                            source=source,
                            target=state_map[next_choice],
                            guard=FormalExpression(body=guard_body) if guard_body else None,
                        )
                        top_region.transitions.append(trans)
                default = state_def.get("Default")
                if default and default in state_map:
                    trans = StateTransition(
                        id=f"{state_name}->{default}",
                        source=source,
                        target=state_map[default],
                    )
                    top_region.transitions.append(trans)

            # Error handling next_state links
            catch_list = state_def.get("Catch", [])
            if isinstance(catch_list, list) and source.error_handling:
                for catch_entry in catch_list:
                    next_name = catch_entry.get("Next")
                    if next_name and next_name in state_map:
                        # Store the next state reference on the error_handling config
                        if source.error_handling.next_state is None:
                            source.error_handling.next_state = state_map[next_name]

        # Set initial state
        if start_at and start_at in state_map:
            top_region.initial_state = state_map[start_at]

        return sm

    # ── Parse a single state ───────────────────────────────────────
    def _parse_state(self, name: str, defn: dict) -> State:
        st_type = defn.get("Type", "Pass")
        state = State(id=name, name=name)

        # Cloud resource binding (for Task states)
        resource_arn = defn.get("Resource")
        if resource_arn:
            state.cloud_resource = CloudResourceBinding(
                resource_arn=resource_arn,
                parameters=defn.get("Parameters"),
            )

        # Timeout
        timeout_sec = defn.get("TimeoutSeconds")
        heartbeat_sec = defn.get("HeartbeatSeconds")
        if timeout_sec or heartbeat_sec:
            state.timeout = TimeoutConfig(
                timeout_seconds=timeout_sec if timeout_sec else 300,
                heartbeat_seconds=heartbeat_sec,
            )

        # Error handling (Catch)
        catches = defn.get("Catch", [])
        if isinstance(catches, list) and catches:
            # Take the first Catch as the error handling config (simplified)
            first = catches[0]
            state.error_handling = ErrorHandlingConfig(
                error_equals=first.get("ErrorEquals", ["States.ALL"]),
                next_state=None,  # resolved later in second pass
                result_path=first.get("ResultPath"),
            )

        # Retry policy
        retries = defn.get("Retry", [])
        if isinstance(retries, list) and retries:
            r = retries[0]
            state.retry = RetryConfig(
                error_equals=r.get("ErrorEquals", ["States.ALL"]),
                interval_seconds=r.get("IntervalSeconds", 1),
                max_attempts=r.get("MaxAttempts", 3),
                backoff_rate=r.get("BackoffRate", 2.0),
            )

        # For Wait states, store the wait duration as timeout (already set)
        if st_type == "Wait":
            seconds = defn.get("Seconds")
            timestamp = defn.get("Timestamp")
            if seconds:
                state.timeout = TimeoutConfig(timeout_seconds=seconds)
            elif timestamp:
                state.timeout = TimeoutConfig(timeout_seconds=0)  # handle differently if needed

        # For Pass states, store any Result as a script
        if st_type == "Pass":
            result = defn.get("Result")
            if result:
                script_body = json.dumps({"Result": result})
                state.do_actions.append(Script(script_body=script_body, script_language=ScriptLanguage.PYTHON))

        # For Succeed / Fail, mark as such via entry_actions? Not needed.

        # Parallel / Map: recursively parse nested states
        if st_type in ("Parallel", "Map"):
            nested = defn.get("Branches", [])
            # In ASL, Parallel has a list of branches, each of which is a mini‑state machine
            for branch in nested:
                sub_sm = self._build_state_machine(branch)
                # Merge the sub‑machine states into a sub‑region of the current state
                sub_region = StateMachineRegion(
                    states=sub_sm.top_region.states,
                    transitions=sub_sm.top_region.transitions,
                    initial_state=sub_sm.top_region.initial_state,
                )
                state.regions.append(sub_region)

        return state

    # ── Convert a Choice rule to a textual expression ──────────────
    def _choice_to_expression(self, choice: dict) -> Optional[str]:
        """Build a simple expression like '$.var == "value"' from a Choice rule."""
        variable = choice.get("Variable", "$")
        # Pick the first operator present
        for op in ("StringEquals", "StringLessThan", "StringGreaterThan",
                   "NumericEquals", "NumericLessThan", "NumericGreaterThan",
                   "BooleanEquals", "TimestampEquals", "TimestampLessThan", "TimestampGreaterThan"):
            val = choice.get(op)
            if val is not None:
                return f"{variable} {op} {json.dumps(val)}"
        # And/Or/Not more complex – omit for now
        return None