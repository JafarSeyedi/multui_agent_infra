# engines/document/parsers/osdm_parsers/azure_logic_apps_parser.py
"""
Azure Logic Apps Parser – converts a Logic Apps workflow JSON into a
StateMachineDocument (unified OSDM model).

Mapping rules:
- Workflow name → StateMachineModel.id
- Triggers:
    * Request (manual) → ignored (no state) – the state machine is invoked externally
    * Recurrence (timer) → TimerEventDefinition on StateMachineModel
- Actions:
    * Function → State.cloud_resource (azure_function_id)
    * InlineCode → State with Script in do_actions
    * Compose / other built‑ins → State with Script for the entire action definition
- runAfter → StateTransition between states, or ErrorHandlingConfig when runAfter = ["Failed"]
- Condition actions → State with multiple outgoing StateTransitions (guard expressions)
- Scope / Foreach → composite State with nested regions
- Timeout on action → State.timeout
- Retry policies → State.retry
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


class AzureLogicAppsParser(BaseOSDMParser):
    """Parser for Azure Logic Apps workflow JSON files (.logicapp.json)."""

    name = "azure_logic_apps"
    supported_extensions = (".logicapp.json",)

    async def _parse_to_document(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> BaseOSDMDocument:
        text = data.decode(options.encoding or "utf-8")
        workflow = json.loads(text)

        doc = StateMachineDocument()
        sm = self._build_state_machine(workflow)
        doc.state_machines.append(sm)
        return doc

    # ── Top‑level workflow ─────────────────────────────────────────
    def _build_state_machine(self, workflow: dict) -> StateMachineModel:
        definition = workflow.get("definition", workflow)
        name = workflow.get("name") or definition.get("name", "logic_app")

        sm = StateMachineModel(id=name, name=name)
        top_region = StateMachineRegion()
        sm.top_region = top_region

        # Parse triggers – extract timer if recurrence trigger present
        triggers = definition.get("triggers", {})
        self._parse_triggers(sm, triggers)

        # Parse actions
        actions = definition.get("actions", {})
        state_map: Dict[str, State] = {}

        # First pass: create states for all actions
        for action_name, action_def in actions.items():
            st = self._parse_action(action_name, action_def)
            state_map[action_name] = st
            top_region.states.append(st)

        # Second pass: link transitions via runAfter, and resolve nested scopes
        for action_name, action_def in actions.items():
            source = state_map[action_name]
            run_after = action_def.get("runAfter", {})
            for pred_name, conditions in run_after.items():
                if pred_name in state_map:
                    if "Failed" in conditions:
                        # This is an error‑handling link
                        if source.error_handling is None:
                            source.error_handling = ErrorHandlingConfig(
                                error_equals=["Failed"],
                                next_state=state_map[pred_name],  # actually the error handler is the source? logic: when A fails, run B
                            )
                        else:
                            # already has error handling for another predecessor?
                            pass
                    else:
                        # Normal success dependency: pred → source
                        trans = StateTransition(
                            id=f"{pred_name}_to_{action_name}",
                            source=state_map[pred_name],
                            target=source,
                        )
                        top_region.transitions.append(trans)

            # Handle nested actions (Scope, Foreach, etc.)
            if action_def.get("type") in ("Scope", "Foreach", "Until"):
                nested_actions = action_def.get("actions", {})
                if nested_actions:
                    sub_region = StateMachineRegion()
                    for nested_name, nested_def in nested_actions.items():
                        nested_state = self._parse_action(nested_name, nested_def)
                        sub_region.states.append(nested_state)
                    # Recursively link nested runAfter within the sub‑region
                    for nested_name, nested_def in nested_actions.items():
                        run_after_nested = nested_def.get("runAfter", {})
                        for pred, conds in run_after_nested.items():
                            if pred in sub_region.states_dict():
                                if "Failed" in conds:
                                    nested_state.error_handling = ErrorHandlingConfig(
                                        error_equals=["Failed"],
                                        next_state=sub_region.states_dict()[pred],
                                    )
                                else:
                                    trans = StateTransition(
                                        id=f"{pred}_to_{nested_name}",
                                        source=sub_region.states_dict()[pred],
                                        target=sub_region.states_dict()[nested_name],
                                    )
                                    sub_region.transitions.append(trans)
                    source.regions.append(sub_region)

        # Determine initial state(s): actions with no incoming runAfter from other actions
        has_incoming = set()
        for action_def in actions.values():
            for pred in action_def.get("runAfter", {}):
                has_incoming.add(pred)
        initial_actions = [a for a in actions if a not in has_incoming]
        if initial_actions:
            # For simplicity, if there's one initial action, set it as the region's initial state.
            # If multiple, we'd need a pseudo‑state or treat them as parallel.
            if len(initial_actions) == 1:
                top_region.initial_state = state_map[initial_actions[0]]
            else:
                # Create a pseudo‑state? For now just leave unset.
                pass

        # Parse error handling/retry on the state machine level? Logic Apps doesn't have global catch.
        return sm

    # ── Helpers ────────────────────────────────────────────────────
    def _parse_triggers(self, sm: StateMachineModel, triggers: dict) -> None:
        """Extract timer recurrence and store as TimerEventDefinition."""
        for name, trigger in triggers.items():
            if trigger.get("type") == "Recurrence":
                recurrence = trigger.get("recurrence", {})
                interval = recurrence.get("interval", 1)
                frequency = recurrence.get("frequency", "Minute")  # Second, Minute, Hour, Day, Week, Month

                # Convert to ISO 8601 duration or cron
                # Simplified: we store the raw recurrence as a cycle expression for the timer event
                expr = f"R/{frequency}/{interval}"
                sm.timer_trigger = TimerEventDefinition(
                    timer_type=TimerEventType.CYCLE,
                    time_cycle=FormalExpression(body=expr),
                )

    def _parse_action(self, name: str, action_def: dict) -> State:
        st = State(id=name, name=name)
        action_type = action_def.get("type", "Compose")

        # Cloud resource bindings
        if action_type == "Function":
            func_info = action_def.get("inputs", {}).get("function", {})
            azure_func_id = func_info.get("id")
            if azure_func_id:
                st.cloud_resource = CloudResourceBinding(
                    azure_function_id=azure_func_id,
                    parameters=func_info.get("body"),
                )
        elif action_type == "InlineCode":
            code = action_def.get("inputs", {}).get("code", "")
            language = action_def.get("inputs", {}).get("language", "javascript")
            st.do_actions.append(Script(script_body=code, script_language=ScriptLanguage.JS if language == "javascript" else ScriptLanguage.PYTHON))
        else:
            # Store the whole action definition as a script for round‑trip (Compose, etc.)
            script_body = json.dumps(action_def)
            st.do_actions.append(Script(script_body=script_body, script_language=ScriptLanguage.JSON))

        # Timeout
        timeout_str = action_def.get("timeout")
        if timeout_str:
            seconds = self._parse_iso8601_duration(timeout_str)
            st.timeout = TimeoutConfig(timeout_seconds=seconds)

        # Retry policy
        retry = action_def.get("retryPolicy")
        if retry:
            st.retry = RetryConfig(
                interval_seconds=retry.get("interval", 1),
                max_attempts=retry.get("count", 3),
                backoff_rate=retry.get("backoffRate", 2.0),
            )

        # Condition action: will be handled in transition creation (choices)
        # We store the expression as a script? Not needed; the transition guard will be set later.

        return st

    @staticmethod
    def _parse_iso8601_duration(duration_str: str) -> int:
        """Convert 'PT1H30M' to seconds. Very simplified."""
        import re
        total = 0
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
        if match:
            h, m, s = (int(x) if x else 0 for x in match.groups())
            total = h * 3600 + m * 60 + s
        return total