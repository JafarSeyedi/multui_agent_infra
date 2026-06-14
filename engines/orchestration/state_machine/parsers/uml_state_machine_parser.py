# engines/document/parsers/osdm_parsers/uml_state_machine_parser.py
"""
UML State Machine Parser – converts a UML 2.x XMI file (.uml, .xmi) into a
StateMachineDocument (unified OSDM model).

Mapping rules (UML → OSDM):
- <StateMachine>          → StateMachineModel
- <region>                → StateMachineRegion
- <state>                 → State (entry/exit/do → Script in actions)
- <transition>            → StateTransition (trigger→trigger, guard→guard, effect→effect)
- <pseudostate>           → PseudoState (parent_state set to the owning state/region)
- <finalState>            → State with is_final=True
- Composite states (nested regions) handled recursively.
- All cross‑references resolved during parsing.

No annotations are used; all data is stored in typed fields defined by the unified model.
"""
from __future__ import annotations

import uuid
from xml.etree import ElementTree as ET

from engines.document.models.media_types import MEDIA_TYPES
from ..models.state_machine_models import (
    BaseOSDMDocument, PseudoState, PseudoStateKind,
    State, StateMachineDocument, StateMachineModel,
    StateMachineRegion, StateTransition
)
from ...bpmn.models.bpmn_models import Script, ScriptLanguage, FormalExpression
from engines.document.parsers.base import ParseOptions
from ...models.parsers.base_osdm_parser import BaseOSDMParser

UML_NS = "http://www.omg.org/spec/UML/20131001"
XMI_NS = "http://www.omg.org/spec/XMI/20131001"
NS = {"uml": UML_NS, "xmi": XMI_NS}


class UMLStateMachineParser(BaseOSDMParser):
    """Parser for UML 2.x State Machine XMI files (.uml, .xmi)."""

    name = "uml_state_machine"
    supported_extensions = (".uml", ".xmi",)

    async def _parse_to_document(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> BaseOSDMDocument:
        encoding = options.encoding or "utf-8"
        text = data.decode(encoding)
        root = ET.fromstring(text)

        doc = StateMachineDocument(
            document_id=root.get("id", source_name),
            title=root.get("name", source_name),
            media_type=MEDIA_TYPES.get("uml_state_machine", MEDIA_TYPES["xml"])
        )
        doc.source_file = source_name

        for sm_elem in root.findall(".//uml:StateMachine", NS):
            sm = self._parse_state_machine(sm_elem)
            doc.state_machines.append(sm)

        return doc

    def _parse_state_machine(self, sm_elem: ET.Element) -> StateMachineModel:
        sm_id = sm_elem.get(f"{{{XMI_NS}}}id", sm_elem.get("id", ""))
        sm_name = sm_elem.get("name", "")
        sm = StateMachineModel(id=sm_id, name=sm_name)

        region_elem = sm_elem.find("uml:region", NS)
        if region_elem is not None:
            region, pseudo_map = self._parse_region(region_elem, parent_state=None)
            sm.top_region = region
            sm.pseudo_states = list(pseudo_map.values())
        else:
            sm.top_region = StateMachineRegion(id=str(uuid.uuid4().hex))

        return sm

    def _parse_region(
        self, region_elem: ET.Element, parent_state: State | None
    ) -> tuple[StateMachineRegion, dict[str, PseudoState]]:
        region = StateMachineRegion(
            id=str(uuid.uuid4().hex),
            name=region_elem.get("name", "")
        )
        state_map: dict[str, State] = {}
        pseudo_map: dict[str, PseudoState] = {}

        # First pass: collect states, pseudo‑states, final states
        for child in region_elem:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag == "state":
                st, sub_pseudo_map = self._parse_state(child)
                state_map[st.id] = st
                region.states.append(st)
                pseudo_map.update(sub_pseudo_map)
            elif tag == "pseudostate":
                ps = self._parse_pseudo_state(child, parent_state)
                pseudo_map[ps.id] = ps
            elif tag == "finalState":
                final_st = self._parse_final_state(child)
                state_map[final_st.id] = final_st
                region.states.append(final_st)

        # Second pass: transitions (now all source/target ids are known)
        for child in region_elem:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag == "transition":
                trans = self._parse_transition(child, state_map, pseudo_map)
                if trans:
                    region.transitions.append(trans)

        # Initial state from the initial pseudo‑state
        for pseudo in pseudo_map.values():
            if pseudo.kind == PseudoStateKind.INITIAL and pseudo.outgoing_transitions:
                init_target = pseudo.outgoing_transitions[0].target
                if isinstance(init_target, State):
                    region.initial_state = init_target
                    break

        return region, pseudo_map

    def _parse_state(self, elem: ET.Element) -> tuple[State, dict[str, PseudoState]]:
        st = State(
            id=elem.get(f"{{{XMI_NS}}}id", elem.get("id", str(uuid.uuid4().hex))),
            name=elem.get("name", "")
        )
        pseudo_map: dict[str, PseudoState] = {}

        # Entry/Exit/Do activities
        for child in elem:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag == "entry":
                self._parse_activity(child, st.entry_actions)
            elif tag == "exit":
                self._parse_activity(child, st.exit_actions)
            elif tag == "doActivity":
                self._parse_activity(child, st.do_actions)
            elif tag == "region":
                sub_region, sub_pseudo_map = self._parse_region(child, parent_state=st)
                st.regions.append(sub_region)
                pseudo_map.update(sub_pseudo_map)
                st.is_composite = True

        return st, pseudo_map

    def _parse_activity(self, elem: ET.Element, actions: list[Script]) -> None:
        spec = elem.find("uml:specification", NS)
        body = ""
        if spec is not None:
            body = spec.get("value", "") or spec.text or ""
        elif elem.text:
            body = elem.text
        if body:
            script_id = str(uuid.uuid4().hex)
            actions.append(Script(
                id=script_id,
                script_body=body,
                script_language=ScriptLanguage.PYTHON
            ))

    def _parse_final_state(self, elem: ET.Element) -> State:
        st = State(
            id=elem.get(f"{{{XMI_NS}}}id", elem.get("id", str(uuid.uuid4().hex))),
            name=elem.get("name", ""),
            is_final=True
        )
        return st

    def _parse_pseudo_state(self, elem: ET.Element, parent_state: State | None) -> PseudoState:
        kind_str = elem.get("kind", "initial")
        kind_map = {
            "initial": PseudoStateKind.INITIAL,
            "deepHistory": PseudoStateKind.DEEP_HISTORY,
            "shallowHistory": PseudoStateKind.SHALLOW_HISTORY,
            "join": PseudoStateKind.JOIN,
            "fork": PseudoStateKind.FORK,
            "junction": PseudoStateKind.JUNCTION,
            "choice": PseudoStateKind.CHOICE,
            "entryPoint": PseudoStateKind.ENTRY_POINT,
            "exitPoint": PseudoStateKind.EXIT_POINT,
            "terminate": PseudoStateKind.TERMINATE,
        }
        kind = kind_map.get(kind_str, PseudoStateKind.INITIAL)
        ps = PseudoState(
            id=elem.get(f"{{{XMI_NS}}}id", elem.get("id", str(uuid.uuid4().hex))),
            kind=kind,
            parent_state=parent_state
        )
        return ps

    def _parse_transition(
        self, elem: ET.Element,
        state_map: dict[str, State],
        pseudo_map: dict[str, PseudoState],
    ) -> StateTransition | None:
        trans_id = elem.get(f"{{{XMI_NS}}}id", elem.get("id", str(uuid.uuid4().hex)))
        source_id = elem.get("source")
        target_id = elem.get("target")
        if not source_id or not target_id:
            return None

        source_obj = state_map.get(source_id) or pseudo_map.get(source_id)
        target_obj = state_map.get(target_id) or pseudo_map.get(target_id)
        if not source_obj or not target_obj:
            return None

        trans = StateTransition(
            id=trans_id,
            source=source_obj,
            target=target_obj,
        )

        # Trigger
        trigger_elem = elem.find("uml:trigger", NS)
        if trigger_elem is not None:
            name = trigger_elem.get("name", "")
            if name:
                trans.trigger = FormalExpression(
                    id=str(uuid.uuid4().hex),
                    body=name
                )

        # Guard
        guard_elem = elem.find("uml:guard", NS)
        if guard_elem is not None:
            spec = guard_elem.find("uml:specification", NS)
            if spec is not None:
                guard_body = spec.get("value", "") or spec.text or ""
                if guard_body:
                    trans.guard = FormalExpression(
                        id=str(uuid.uuid4().hex),
                        body=guard_body
                    )

        # Effect
        effect_elem = elem.find("uml:effect", NS)
        if effect_elem is not None:
            spec = effect_elem.find("uml:specification", NS)
            if spec is not None:
                effect_body = spec.get("value", "") or spec.text or ""
                if effect_body:
                    trans.effect = FormalExpression(
                        id=str(uuid.uuid4().hex),
                        body=effect_body
                    )

        return trans