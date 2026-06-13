"""Mixin for BPMN root element parsers — messages, errors, resources, artifacts, etc."""

from __future__ import annotations

from typing import Any, Optional
from xml.etree import ElementTree as ET

from engines.orchestration.models.osdm_models import (
    Association, AssociationDirection, Artifact, Auditing,
    CorrelationKey, CorrelationProperty, CorrelationPropertyType,
    CorrelationSubscription, DataInput, DataOutput, Error,
    Escalation, FormalExpression, GlobalTask, Group,
    InputOutputSpecification, Interface, ItemDefinition, ItemKind,
    Message, Operation, Property, Rendering, Resource,
    ResourceAssignmentExpression, ResourceParameter,
    ResourceParameterType, ResourceRole, ResourceRoleType,
    ScriptLanguage, Signal, TextAnnotation,
)
from .bpmn_constants import NS


class BPMNRootElementParser:
    """Mixin providing root-level BPMN element parsing methods."""

    @staticmethod
    def _map_enum(cls: type, value: str, default: Any) -> Any:
        try:
            return cls(value)
        except ValueError:
            return default

    @staticmethod
    def _map_item_kind(value: str) -> ItemKind:
        return BPMNRootElementParser._map_enum(ItemKind, value, ItemKind.INFORMATION)

    @staticmethod
    def _map_association_direction(value: str) -> AssociationDirection:
        return BPMNRootElementParser._map_enum(AssociationDirection, value, AssociationDirection.NONE)

    def _parse_resource_assignment_expression(self, elem: ET.Element) -> ResourceAssignmentExpression | None:
        expr = elem.find("bpmn:formalExpression", NS)
        if expr is None:
            return None
        formal_expr = self._parse_expression(expr)
        if formal_expr is None:
            return None
        return ResourceAssignmentExpression(
            id=elem.get("id", ""),
            expression=formal_expr,
        )

    def _parse_data_input(self, elem: ET.Element) -> DataInput:
        inp = DataInput(
            id=elem.get("id", ""),
            name=elem.get("name") or "",
            item_subject_ref=None,
            is_collection=elem.get("isCollection") == "true",
        )
        inp.item_subject_ref_id = elem.get("itemSubjectRef")
        return inp

    def _parse_data_output(self, elem: ET.Element) -> DataOutput:
        out = DataOutput(
            id=elem.get("id", ""),
            name=elem.get("name") or "",
            item_subject_ref=None,
            is_collection=elem.get("isCollection") == "true",
        )
        out.item_subject_ref_id = elem.get("itemSubjectRef")
        return out

    def _parse_global_task(self, elem: ET.Element, cls: type) -> GlobalTask:
        gt = cls(
            id=elem.get("id", ""),
            name=elem.get("name"),
        )
        io = elem.find("bpmn:ioSpecification", NS)
        if io is not None:
            gt.io_specification = self._parse_io_specification(io)
        return gt

    def _parse_expression(self, elem: ET.Element | None) -> FormalExpression | None:
        if elem is None:
            return None
        lang = elem.get("language")
        lang_enum = self._map_enum(ScriptLanguage, lang, ScriptLanguage.PYTHON) if lang else None
        body = elem.text or ""
        return FormalExpression(
            id=elem.get("id", ""),
            language=lang_enum,
            body=body,
        )

    def _parse_rendering(self, elem: ET.Element) -> Rendering:
        return Rendering(
            id=elem.get("id", ""),
            name=elem.get("name"),
        )

    def _parse_message(self, elem: ET.Element) -> Message:
        msg = Message(id=elem.get("id", ""), name=elem.get("name"))
        msg.item_ref_id = elem.get("itemRef")
        return msg

    def _parse_error(self, elem: ET.Element) -> Error:
        err = Error(id=elem.get("id", ""), name=elem.get("name"))
        err.error_code = elem.get("errorCode")
        return err

    def _parse_escalation(self, elem: ET.Element) -> Escalation:
        esc = Escalation(id=elem.get("id", ""), name=elem.get("name"))
        esc.escalation_code = elem.get("escalationCode")
        return esc

    def _parse_signal(self, elem: ET.Element) -> Signal:
        return Signal(id=elem.get("id", ""), name=elem.get("name"))

    def _parse_resource(self, elem: ET.Element) -> Resource:
        res = Resource(id=elem.get("id", ""), name=elem.get("name"))
        for rp in elem.findall("bpmn:resourceParameter", NS):
            res.resource_parameters.append(self._parse_resource_parameter(rp))
        return res

    def _parse_resource_parameter(self, elem: ET.Element) -> ResourceParameter:
        type_str = elem.get("type", "UserField")
        param_type = self._map_enum(ResourceParameterType, type_str, ResourceParameterType.USER_FIELD)
        return ResourceParameter(
            id=elem.get("id", ""),
            name=elem.get("name"),
            type=param_type,
            is_required=elem.get("isRequired", "false") == "true",
        )

    def _parse_resource_role(self, elem: ET.Element) -> ResourceRole:
        type_str = elem.get("type", "None")
        role_type = self._map_enum(ResourceRoleType, type_str, ResourceRoleType.NONE)
        role = ResourceRole(
            id=elem.get("id", ""),
            name=elem.get("name"),
            type=role_type,
            resource_ref=None,
        )
        role.resource_ref_id = elem.get("resourceRef")
        expr_elem = elem.find("bpmn:resourceAssignmentExpression", NS)
        if expr_elem is not None:
            role.resource_assignment_expression = self._parse_resource_assignment_expression(expr_elem)
        return role

    def _parse_interface(self, elem: ET.Element) -> Interface:
        iface = Interface(id=elem.get("id", ""), name=elem.get("name"))
        for op_elem in elem.findall("bpmn:operation", NS):
            op = self._parse_operation(op_elem)
            iface.operations[op.id] = op
        return iface

    def _parse_operation(self, elem: ET.Element) -> Operation:
        op = Operation(id=elem.get("id", ""), name=elem.get("name"))
        op.in_message_ref_id = elem.get("inMessageRef")
        op.out_message_ref_id = elem.get("outMessageRef")
        op.error_ref_ids = [err_id for err in elem.findall("bpmn:errorRef", NS) if (err_id := err.get("id")) is not None]
        return op

    def _parse_item_definition(self, elem: ET.Element) -> ItemDefinition:
        kind_str = elem.get("itemKind", "Information")
        kind = self._map_item_kind(kind_str)
        return ItemDefinition(
            id=elem.get("id", ""),
            name=elem.get("name"),
            item_kind=kind,
            is_collection=elem.get("isCollection", "false") == "true",
        )

    def _parse_correlation_property(self, elem: ET.Element) -> CorrelationProperty:
        prop_type_str = elem.get("type", "key")
        prop_type = self._map_enum(CorrelationPropertyType, prop_type_str, CorrelationPropertyType.KEY)
        cp = CorrelationProperty(
            id=elem.get("id", ""),
            name=elem.get("name"),
            property_type=prop_type,
        )
        return cp

    def _parse_correlation_key(self, elem: ET.Element) -> CorrelationKey:
        key = CorrelationKey(id=elem.get("id", ""), name=elem.get("name"))
        key.property_ref_ids = [pref_id for pref in elem.findall("bpmn:correlationPropertyRef", NS) if (pref_id := pref.get("id")) is not None]
        return key

    def _parse_correlation_subscription(self, elem: ET.Element) -> CorrelationSubscription:
        cs = CorrelationSubscription(id=elem.get("id", ""))
        cs.correlation_key_ref_id = elem.get("correlationKeyRef")
        return cs

    def _parse_io_specification(self, elem: ET.Element) -> InputOutputSpecification:
        ios = InputOutputSpecification(id=elem.get("id", ""), name=elem.get("name"))
        for di in elem.findall("bpmn:dataInput", NS):
            ios.data_inputs.append(self._parse_data_input(di))
        for do in elem.findall("bpmn:dataOutput", NS):
            ios.data_outputs.append(self._parse_data_output(do))
        return ios

    def _parse_auditing(self, elem: ET.Element) -> Auditing:
        aud = Auditing(id=elem.get("id", ""))
        aud.save_instances = elem.get("saveInstances", "false") == "true"
        aud.generate_trace_log = elem.get("generateTraceLog", "false") == "true"
        return aud

    def _parse_property(self, elem: ET.Element) -> Property:
        prop = Property(id=elem.get("id", ""), name=elem.get("name"))
        prop.item_subject_ref_id = elem.get("itemSubjectRef")
        return prop

    def _parse_artifact(self, elem: ET.Element) -> Artifact | None:
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if tag == "association":
            assoc = Association(
                id=elem.get("id", ""),
                direction=self._map_association_direction(elem.get("associationDirection", "None")),
                source_ref=None,
                target_ref=None,
            )
            assoc.source_ref_id = elem.get("sourceRef")
            assoc.target_ref_id = elem.get("targetRef")
            return assoc
        elif tag == "textAnnotation":
            text_elem = elem.find("bpmn:text", NS)
            text = text_elem.text if text_elem is not None and text_elem.text is not None else ""
            return TextAnnotation(id=elem.get("id", ""), text=text)
        elif tag == "group":
            return Group(id=elem.get("id", ""))
        return None
