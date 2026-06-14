"""Mixin for BPMN collaboration/lane/choreography parsers."""

from __future__ import annotations

from typing import Optional
from xml.etree import ElementTree as ET

from ..models.bpmn_models import (
    Artifact, Association, AssociationDirection, Choreography,
    ChoreographyActivity, ChoreographyLoopType, Collaboration,
    ConversationAssociation, ConversationLink, ConversationNode,
    CorrelationKey, Group, Lane, LaneSet, MessageFlow,
    MessageFlowAssociation, Participant, ParticipantAssociation,
    ParticipantMultiplicity, TextAnnotation,
)
from .bpmn_constants import NS


class BPMNCollaborationParser:
    """Mixin providing collaboration, lane, choreography parsing methods."""

    @staticmethod
    def _map_choreography_loop_type(value: str) -> ChoreographyLoopType:
        try:
            return ChoreographyLoopType(value)
        except ValueError:
            return ChoreographyLoopType.NONE

    @staticmethod
    def _map_association_direction(value: str) -> AssociationDirection:
        try:
            return AssociationDirection(value)
        except ValueError:
            return AssociationDirection.NONE

    def _parse_message_flow(self, elem: ET.Element) -> MessageFlow:
        mf = MessageFlow(
            id=elem.get("id", ""),
            name=elem.get("name"),
            source_ref=None,
            target_ref=None,
            message_ref=None,
        )
        mf.source_ref_id = elem.get("sourceRef")
        mf.target_ref_id = elem.get("targetRef")
        mf.message_ref_id = elem.get("messageRef")
        return mf

    def _parse_artifact(self, elem: ET.Element) -> Artifact | None:
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if tag == "association":
            assoc = Association(
                id=elem.get("id", ""),
                direction=BPMNCollaborationParser._map_association_direction(elem.get("associationDirection", "None")),
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

    def _parse_correlation_key(self, elem: ET.Element) -> CorrelationKey:
        key = CorrelationKey(id=elem.get("id", ""), name=elem.get("name"))
        key.property_ref_ids = [pref_id for pref in elem.findall("bpmn:correlationPropertyRef", NS) if (pref_id := pref.get("id")) is not None]
        return key

    def _parse_lane_set(self, elem: ET.Element) -> LaneSet:
        ls = LaneSet(id=elem.get("id", ""), name=elem.get("name"))
        for lane_elem in elem.findall("bpmn:lane", NS):
            lane = self._parse_lane(lane_elem)
            ls.lanes.append(lane)
        return ls

    def _parse_lane(self, elem: ET.Element) -> Lane:
        lane = Lane(id=elem.get("id", ""), name=elem.get("name"))
        lane.partition_element_ref_id = elem.get("partitionElement")
        lane.flow_node_ref_ids = [fn_id for fn in elem.findall("bpmn:flowNodeRef", NS) if (fn_id := fn.get("id")) is not None]
        child_ls = elem.find("bpmn:childLaneSet", NS)
        if child_ls is not None:
            lane.child_lane_set = self._parse_lane_set(child_ls)
        return lane

    def _parse_collaboration(self, elem: ET.Element) -> Collaboration:
        collab = Collaboration(
            id=elem.get("id", ""),
            name=elem.get("name"),
            is_closed=elem.get("isClosed", "false") == "true",
        )
        for p in elem.findall("bpmn:participant", NS):
            collab.participants.append(self._parse_participant(p))
        for mf in elem.findall("bpmn:messageFlow", NS):
            collab.message_flows.append(self._parse_message_flow(mf))
        for art in (elem.findall("bpmn:association", NS) +
                    elem.findall("bpmn:group", NS) +
                    elem.findall("bpmn:textAnnotation", NS)):
            a = self._parse_artifact(art)
            if a:
                collab.artifacts.append(a)
        for key in elem.findall("bpmn:correlationKey", NS):
            collab.correlation_keys.append(self._parse_correlation_key(key))
        for conv in (elem.findall("bpmn:conversation", NS) +
                     elem.findall("bpmn:callConversation", NS) +
                     elem.findall("bpmn:subConversation", NS)):
            collab.conversations.append(self._parse_conversation_node(conv))
        for ca in elem.findall("bpmn:conversationAssociation", NS):
            collab.conversation_associations.append(self._parse_conversation_association(ca))
        for cl in elem.findall("bpmn:conversationLink", NS):
            collab.conversation_links.append(self._parse_conversation_link(cl))
        for mfa in elem.findall("bpmn:messageFlowAssociation", NS):
            collab.message_flow_associations.append(self._parse_message_flow_association(mfa))
        for pa in elem.findall("bpmn:participantAssociation", NS):
            collab.participant_associations.append(self._parse_participant_association(pa))
        return collab

    def _parse_choreography(self, elem: ET.Element) -> Choreography:
        choreo = Choreography(
            id=elem.get("id", ""),
            name=elem.get("name"),
            is_closed=elem.get("isClosed", "false") == "true",
        )
        for child in elem:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag == "choreographyActivity":
                act = self._parse_choreography_activity(child)
                choreo.flow_elements[act.id] = act
            elif tag == "participant":
                choreo.participants.append(self._parse_participant(child))
            elif tag == "messageFlow":
                choreo.message_flows.append(self._parse_message_flow(child))
        return choreo

    def _parse_choreography_activity(self, elem: ET.Element) -> ChoreographyActivity:
        act = ChoreographyActivity(
            id=elem.get("id", ""),
            name=elem.get("name"),
        )
        act.participant_ref_ids = [pref_id for pref in elem.findall("bpmn:participantRef", NS) if (pref_id := pref.get("id")) is not None]
        act.initiating_participant_ref_id = elem.get("initiatingParticipantRef")
        loop_str = elem.get("loopType", "None")
        act.loop_type = self._map_choreography_loop_type(loop_str)
        return act

    def _parse_participant(self, elem: ET.Element) -> Participant:
        part = Participant(id=elem.get("id", ""), name=elem.get("name"))
        part.process_ref_id = elem.get("processRef")
        mul = elem.find("bpmn:participantMultiplicity", NS)
        if mul is not None:
            part.participant_multiplicity = ParticipantMultiplicity(
                minimum=int(mul.get("minimum", "1")),
                maximum=int(mul.get("maximum", "0")),
            )
        return part

    def _parse_conversation_node(self, elem: ET.Element) -> ConversationNode:
        conv = ConversationNode(id=elem.get("id", ""), name=elem.get("name"))
        conv.participant_ref_ids = [pref_id for pref in elem.findall("bpmn:participantRef", NS) if (pref_id := pref.get("id")) is not None]
        conv.message_flow_ref_ids = [mf_id for mf in elem.findall("bpmn:messageFlowRef", NS) if (mf_id := mf.get("id")) is not None]
        return conv

    def _parse_conversation_association(self, elem: ET.Element) -> ConversationAssociation:
        ca = ConversationAssociation(id=elem.get("id", ""))
        ca.inner_conversation_node_ref_id = elem.get("innerConversationNodeRef")
        ca.outer_conversation_node_ref_ids = [outer_id for outer in elem.findall("bpmn:outerConversationNodeRef", NS) if (outer_id := outer.get("id")) is not None]
        return ca

    def _parse_conversation_link(self, elem: ET.Element) -> ConversationLink:
        link = ConversationLink(id=elem.get("id", ""))
        link.source_ref_id = elem.get("sourceRef")
        link.target_ref_id = elem.get("targetRef")
        return link

    def _parse_message_flow_association(self, elem: ET.Element) -> MessageFlowAssociation:
        mfa = MessageFlowAssociation(id=elem.get("id", ""))
        mfa.inner_message_flow_ref_id = elem.get("innerMessageFlowRef")
        mfa.outer_message_flow_ref_id = elem.get("outerMessageFlowRef")
        return mfa

    def _parse_participant_association(self, elem: ET.Element) -> ParticipantAssociation:
        pa = ParticipantAssociation(id=elem.get("id", ""))
        pa.inner_participant_ref_id = elem.get("innerParticipantRef")
        pa.outer_participant_ref_id = elem.get("outerParticipantRef")
        return pa
