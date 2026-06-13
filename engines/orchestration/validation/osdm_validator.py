"""OSDM validation layer.

Validates process definitions against OSDM schema constraints.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from ..._types import RawData

logger = logging.getLogger(__name__)


@dataclass
class ValidationError:
    code: str = ""
    message: str = ""
    element_id: str | None = None
    severity: str = "error"
    category: str = ""


@dataclass
class ValidationResult:
    valid: bool = True
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[ValidationError] = field(default_factory=list)

    def add_error(self, code: str, message: str, element_id: str | None = None, category: str = "") -> None:
        self.errors.append(ValidationError(code=code, message=message, element_id=element_id, severity="error", category=category))
        self.valid = False

    def add_warning(self, code: str, message: str, element_id: str | None = None, category: str = "") -> None:
        self.warnings.append(ValidationError(code=code, message=message, element_id=element_id, severity="warning", category=category))

    def merge(self, other: ValidationResult) -> None:
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        if not other.valid:
            self.valid = False


class BpmnOsdmValidator:
    """Validates BPMN process definitions against OSDM schema."""

    def validate(self, definition: RawData) -> ValidationResult:
        result = ValidationResult()
        self._validate_structure(definition, result)
        self._validate_start_events(definition, result)
        self._validate_end_events(definition, result)
        self._validate_activities(definition, result)
        self._validate_sequence_flows(definition, result)
        self._validate_gateways(definition, result)
        self._validate_events(definition, result)
        self._validate_sub_processes(definition, result)
        return result

    def _validate_structure(self, definition: RawData, result: ValidationResult) -> None:
        if not definition.get("id"):
            result.add_error("BPMN001", "Process definition must have an id", category="structure")
        if not definition.get("activities") and not definition.get("flow_elements"):
            result.add_warning("BPMN002", "Process definition has no activities", category="structure")

    def _validate_start_events(self, definition: RawData, result: ValidationResult) -> None:
        activities = definition.get("activities", [])
        start_events = [a for a in activities if str(a.get("type", "")).lower() in ("startevent", "start")]
        if len(start_events) == 0:
            result.add_error("BPMN003", "Process must have exactly one start event", category="events")
        elif len(start_events) > 1:
            result.add_error("BPMN004", f"Process has {len(start_events)} start events; only one is allowed", category="events")

    def _validate_end_events(self, definition: RawData, result: ValidationResult) -> None:
        activities = definition.get("activities", [])
        end_events = [a for a in activities if str(a.get("type", "")).lower() in ("endevent", "end")]
        if len(end_events) == 0:
            result.add_warning("BPMN005", "Process has no end events", category="events")

    def _validate_activities(self, definition: RawData, result: ValidationResult) -> None:
        activities = definition.get("activities", [])
        for activity in activities:
            aid = activity.get("id", "")
            if not aid:
                result.add_error("BPMN006", "Activity must have an id", category="activities")
            atype = activity.get("type", "")
            if not atype:
                result.add_error("BPMN007", f"Activity '{aid}' must have a type", element_id=aid, category="activities")

    def _validate_sequence_flows(self, definition: RawData, result: ValidationResult) -> None:
        flows = definition.get("flows", [])
        activities = definition.get("activities", [])
        activity_ids = {a.get("id") for a in activities if a.get("id")}
        for flow in flows:
            source = flow.get("source") or flow.get("sourceRef")
            target = flow.get("target") or flow.get("targetRef")
            fid = flow.get("id", f"{source}->{target}")
            if not source:
                result.add_error("BPMN008", f"Sequence flow '{fid}' missing source", element_id=fid, category="flows")
            if not target:
                result.add_error("BPMN009", f"Sequence flow '{fid}' missing target", element_id=fid, category="flows")
            if source and source not in activity_ids:
                result.add_warning("BPMN010", f"Sequence flow '{fid}' source '{source}' not found in activities", element_id=fid, category="flows")
            if target and target not in activity_ids:
                result.add_warning("BPMN011", f"Sequence flow '{fid}' target '{target}' not found in activities", element_id=fid, category="flows")

    def _validate_gateways(self, definition: RawData, result: ValidationResult) -> None:
        activities = definition.get("activities", [])
        gateway_types = {"exclusivegateway", "inclusivegateway", "parallelgateway", "eventbasedgateway", "complexgateway"}
        for activity in activities:
            atype = str(activity.get("type", "")).lower()
            if atype in gateway_types:
                aid = activity.get("id", "")
                outgoing = [f for f in definition.get("flows", [])
                           if (f.get("source") or f.get("sourceRef")) == aid]
                if len(outgoing) < 2:
                    result.add_warning("BPMN012", f"Gateway '{aid}' has fewer than 2 outgoing flows", element_id=aid, category="gateways")

    def _validate_events(self, definition: RawData, result: ValidationResult) -> None:
        activities = definition.get("activities", [])
        for activity in activities:
            atype = str(activity.get("type", "")).lower()
            aid = activity.get("id", "")
            if "boundary" in atype:
                payload = activity.get("payload", {})
                if not payload.get("attachedToRef"):
                    result.add_error("BPMN013", f"Boundary event '{aid}' must specify attachedToRef", element_id=aid, category="events")
                if not payload.get("eventDefinition"):
                    result.add_warning("BPMN014", f"Boundary event '{aid}' has no event definition", element_id=aid, category="events")

    def _validate_sub_processes(self, definition: RawData, result: ValidationResult) -> None:
        activities = definition.get("activities", [])
        for activity in activities:
            atype = str(activity.get("type", "")).lower()
            aid = activity.get("id", "")
            if "subprocess" in atype:
                payload = activity.get("payload", {})
                children = payload.get("children", [])
                if not children:
                    result.add_warning("BPMN015", f"Sub-process '{aid}' has no child elements", element_id=aid, category="subprocess")


class CmmnOsdmValidator:
    """Validates CMMN case definitions against OSDM schema."""

    def validate(self, definition: RawData) -> ValidationResult:
        result = ValidationResult()
        if not definition.get("id"):
            result.add_error("CMMN001", "Case definition must have an id", category="structure")
        stages = definition.get("stages", [])
        if not stages:
            result.add_warning("CMMN002", "Case definition has no stages", category="structure")
        for stage in stages:
            sid = stage.get("id", "")
            if not sid:
                result.add_error("CMMN003", "Stage must have an id", category="structure")
        return result


class DmnOsdmValidator:
    """Validates DMN decision definitions against OSDM schema."""

    def validate(self, definition: RawData) -> ValidationResult:
        result = ValidationResult()
        if not definition.get("id"):
            result.add_error("DMN001", "Decision definition must have an id", category="structure")
        decisions = definition.get("decisions", [])
        if not decisions:
            result.add_warning("DMN002", "DMN definition has no decisions", category="structure")
        for decision in decisions:
            did = decision.get("id", "")
            if not did:
                result.add_error("DMN003", "Decision must have an id", category="structure")
            table = decision.get("decisionTable")
            if table:
                inputs = table.get("inputs", [])
                outputs = table.get("outputs", [])
                rules = table.get("rules", [])
                if not inputs:
                    result.add_warning("DMN004", f"Decision table for '{did}' has no inputs", element_id=did, category="decisionTable")
                if not outputs:
                    result.add_error("DMN005", f"Decision table for '{did}' has no outputs", element_id=did, category="decisionTable")
                if not rules:
                    result.add_warning("DMN006", f"Decision table for '{did}' has no rules", element_id=did, category="decisionTable")
        return result


class StateMachineOsdmValidator:
    """Validates state machine definitions against OSDM schema."""

    def validate(self, definition: RawData) -> ValidationResult:
        result = ValidationResult()
        if not definition.get("id"):
            result.add_error("SM001", "State machine definition must have an id", category="structure")
        states = definition.get("states", [])
        if not states:
            result.add_error("SM002", "State machine has no states", category="structure")
        initial_states = [s for s in states if s.get("kind", "").lower() == "initial"]
        if len(initial_states) == 0:
            result.add_warning("SM003", "State machine has no initial state", category="structure")
        elif len(initial_states) > 1:
            result.add_error("SM004", f"State machine has {len(initial_states)} initial states; only one is allowed", category="structure")
        return result
