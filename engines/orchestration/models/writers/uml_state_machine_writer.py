# engines/document/writers/osdm_writers/uml_state_machine_writer.py
"""
UML State Machine Writer – serialises an OSDM StateMachineModel into UML 2.x XMI.

All UML‑specific semantics (entry/exit/do actions, triggers, guards, effects,
composite/orthogonal regions, pseudo‑states) are taken directly from the
unified OSDM model. No annotations are required.
"""
from __future__ import annotations

from typing import cast
from xml.etree.ElementTree import Element, SubElement, tostring

from engines.orchestration.models.osdm_models import (
    BaseElement, BaseOSDMDocument, PseudoState, Script, State,
    StateMachineDocument, StateMachineModel, StateMachineRegion, StateTransition, Transition
)
from .base_osdm_writer import BaseOSDMWriter, OSDMWriteOptions

# Namespaces
UML_NS = "http://www.omg.org/spec/UML/20131001"
XMI_NS = "http://www.omg.org/spec/XMI/20131001"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"


class UMLStateMachineWriter(BaseOSDMWriter):
    name = "uml_state_machine"
    supported_extensions = (".uml", ".xmi")

    def __init__(self, options: OSDMWriteOptions | None = None):
        super().__init__(options)
        self._id_counter = 0

    async def _write_design(self, base_document: BaseOSDMDocument) -> bytes:
        document = cast(StateMachineDocument, base_document)
        root = Element(f"{{{XMI_NS}}}XMI", {
            "xmlns:uml": UML_NS,
            "xmlns:xmi": XMI_NS,
            "xmlns:xsi": XSI_NS,
            f"{{{XSI_NS}}}schemaLocation": f"{UML_NS} {UML_NS}/UML.xmi",
            f"{{{XMI_NS}}}version": "2.4.1",
        })

        for sm in document.state_machines:
            self._write_state_machine(root, sm)

        xml_bytes = tostring(root, encoding="unicode", method="xml")
        return xml_bytes.encode(getattr(self.options, "encoding", "utf-8") or "utf-8")

    def get_supported_media_types(self) -> list[str]:
        return ["application/xmi+xml", "application/xml"]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    # ── Writing helpers ─────────────────────────────────────────
    def _new_id(self, prefix: str = "id") -> str:
        self._id_counter += 1
        return f"{prefix}_{self._id_counter}"

    def _add_uml_element(self, parent: Element, tag: str, obj: BaseElement | None = None, **attrs):
        """Create a UML element. If obj is given, its id is used as xmi:id."""
        if obj is not None:
            attrs.setdefault(f"{{{XMI_NS}}}id", obj.id)
        return SubElement(parent, f"{{{UML_NS}}}{tag}", attrs)

    # ── State Machine ───────────────────────────────────────────
    def _write_state_machine(self, root: Element, sm: StateMachineModel) -> None:
        # StateMachineModel is not a BaseElement; set attributes manually
        sm_elem = SubElement(root, f"{{{UML_NS}}}StateMachine", {
            f"{{{XMI_NS}}}id": sm.id,
            "name": sm.name or "",
        })
        # Write top region
        self._write_region(sm_elem, sm.top_region)
        # Write pseudo‑states
        for pseudo in sm.pseudo_states:
            self._write_pseudo_state(sm_elem, pseudo)

    def _write_region(self, parent: Element, region: StateMachineRegion) -> None:
        reg_elem = self._add_uml_element(parent, "region", None, id=self._new_id("region"))
        if region.initial_state:
            # Create an initial pseudo‑state and a transition to the initial state
            init_pseudo = self._add_uml_element(reg_elem, "pseudostate", None,
                id=self._new_id("initial"),
                name="",
                kind="initial")
            # Transition
            trans_elem = self._add_uml_element(reg_elem, "transition", None,
                id=self._new_id("trans_initial"))
            trans_elem.set("source", init_pseudo.get(f"{{{XMI_NS}}}id"))
            trans_elem.set("target", region.initial_state.id)

        # Write states
        for state in region.states:
            self._write_state(reg_elem, state)
        # Write transitions owned by the region
        for trans in region.transitions:
            self._write_transition(reg_elem, trans)

    def _write_state(self, parent: Element, state: State) -> None:
        is_final = len(state.outgoing_transitions) == 0 and not state.regions
        tag = "FinalState" if is_final else "State"
        elem = self._add_uml_element(parent, tag, state)
        if state.name:
            elem.set("name", state.name)

        if state.is_composite:
            elem.set("isComposite", "true")
        if state.is_orthogonal:
            elem.set("isOrthogonal", "true")

        # Entry/Exit/Do actions
        for action in state.entry_actions:
            self._write_activity(elem, "entry", action)
        for action in state.exit_actions:
            self._write_activity(elem, "exit", action)
        for action in state.do_actions:
            self._write_activity(elem, "doActivity", action)

        # Transitions owned by the state (filter only StateTransition)
        for trans in state.outgoing_transitions:
            if isinstance(trans, StateTransition):
                self._write_transition(elem, trans)

        # Sub‑regions (for composite/orthogonal)
        for sub_region in state.regions:
            self._write_region(elem, sub_region)

    def _write_pseudo_state(self, parent: Element, pseudo: PseudoState) -> None:
        elem = self._add_uml_element(parent, "pseudostate", pseudo)
        elem.set("kind", pseudo.kind.value)
        if pseudo.name:
            elem.set("name", pseudo.name)

    def _write_transition(self, parent: Element, trans: StateTransition) -> None:
        if not trans.source or not trans.target:
            return
        elem = self._add_uml_element(parent, "transition", trans)
        elem.set("source", trans.source.id)
        elem.set("target", trans.target.id)

        # Trigger
        if trans.trigger:
            trigger = SubElement(elem, f"{{{UML_NS}}}trigger")
            if trans.trigger.body:
                trigger.set("name", trans.trigger.body)

        # Guard
        if trans.guard:
            guard = SubElement(elem, f"{{{UML_NS}}}guard")
            body = trans.guard.body or ""
            if body:
                SubElement(guard, f"{{{UML_NS}}}specification", {
                    f"{{{XSI_NS}}}type": "uml:LiteralString",
                    "value": body,
                })

        # Effect
        if trans.effect:
            effect = SubElement(elem, f"{{{UML_NS}}}effect")
            body = trans.effect.body or ""
            if body:
                SubElement(effect, f"{{{UML_NS}}}specification", {
                    f"{{{XSI_NS}}}type": "uml:LiteralString",
                    "value": body,
                })

    def _write_activity(self, parent: Element, tag: str, script: Script) -> None:
        elem = SubElement(parent, f"{{{UML_NS}}}{tag}")
        if script.script_body:
            SubElement(elem, f"{{{UML_NS}}}specification", {
                f"{{{XSI_NS}}}type": "uml:LiteralString",
                "value": script.script_body,
            })