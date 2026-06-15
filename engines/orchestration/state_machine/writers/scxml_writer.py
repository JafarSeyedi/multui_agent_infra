# engines/document/writers/osdm_writers/scxml_writer.py
"""
SCXML (State Chart XML) Writer – serialises OSDM StateMachineModel to W3C SCXML.

Uses only typed model fields – no annotations:
- State.parallel         → <parallel> element
- State.initial          → initial attribute (State or PseudoState)
- State.invoke           → <invoke> element
- State.is_final         → <final> element
- State.entry_actions    → <onentry> scripts
- State.exit_actions     → <onexit> scripts
- StateTransition.trigger → event attribute
- StateTransition.guard  → cond attribute
- StateTransition.effect → child <script>
- PseudoState (kind=INITIAL)      → <initial> element
- PseudoState (kind=DEEP_HISTORY or SHALLOW_HISTORY) → <history> element
- PseudoState.parent_state → places pseudo‑state inside the correct parent state
"""
from __future__ import annotations

from typing import cast
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import SubElement
from xml.etree.ElementTree import tostring

from ..models.state_machine_models import BaseOSDMDocument
from ..models.state_machine_models import PseudoState
from ..models.state_machine_models import PseudoStateKind
from ..models.state_machine_models import Script
from ..models.state_machine_models import State
from ..models.state_machine_models import StateInvoke
from ..models.state_machine_models import StateMachineDocument
from ..models.state_machine_models import StateMachineModel
from ..models.state_machine_models import StateMachineRegion
from ..models.state_machine_models import StateTransition
from ..models.state_machine_models import Transition
from ...models.base_osdm_writer import BaseOSDMWriter
from ...models.base_osdm_writer import OSDMWriteOptions


SCXML_NS = "http://www.w3.org/2005/07/scxml"


class SCXMLWriter(BaseOSDMWriter):
    """Serialises a StateMachineDocument to SCXML XML."""

    name = "scxml"
    supported_extensions = (".scxml",)

    def __init__(self, options: OSDMWriteOptions | None = None):
        super().__init__(options)

    async def _write_design(self, base_document: BaseOSDMDocument) -> bytes:
        document = cast(StateMachineDocument, base_document)
        root = Element(f"{{{SCXML_NS}}}scxml", {
            "xmlns": SCXML_NS,
            "version": "1.0",
            "initial": "",
        })

        if document.state_machines:
            sm = document.state_machines[0]   # one SCXML per file
            self._write_scxml_body(root, sm)

        xml_bytes = tostring(root, encoding="unicode", method="xml")
        return xml_bytes.encode(getattr(self.options, "encoding", "utf-8") or "utf-8")

    def get_supported_media_types(self) -> list[str]:
        return ["application/xml"]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    # ── Build the <scxml> body ─────────────────────────────────────
    def _write_scxml_body(self, root: Element, sm: StateMachineModel) -> None:
        # Resolve initial state id (from top‑region.initial_state or from the initial pseudo‑state)
        initial_id = self._resolve_initial_state(sm)
        if initial_id:
            root.set("initial", initial_id)

        if sm.name:
            root.set("name", sm.name)

        # Write the top‑region contents (pseudo‑states are placed inside their parent states
        # during the recursive tree walk, so we just pass the list along)
        self._write_region(root, sm.top_region, sm.pseudo_states)

    def _resolve_initial_state(self, sm: StateMachineModel) -> str | None:
        if sm.top_region.initial_state:
            return sm.top_region.initial_state.id
        # Look for an initial pseudo‑state and follow its outgoing transition
        for pseudo in sm.pseudo_states:
            if pseudo.kind == PseudoStateKind.INITIAL and pseudo.outgoing_transitions:
                target = pseudo.outgoing_transitions[0].target
                if target and isinstance(target, State):
                    return target.id
        # Fallback: first state in top region
        if sm.top_region.states:
            return sm.top_region.states[0].id
        return None

    # ── Write a region ────────────────────────────────────────────
    def _write_region(self, parent: Element, region: StateMachineRegion,
                      pseudo_states: list[PseudoState]) -> None:
        # If the region has multiple top‑level states, wrap them in a <state>, otherwise
        # write the single state directly.
        if len(region.states) == 1 and not region.states[0].parallel:
            self._write_state(parent, region.states[0], pseudo_states)
        else:
            wrapper = SubElement(parent, f"{{{SCXML_NS}}}state", {"id": "top"})
            for state in region.states:
                if state.parallel:
                    self._write_parallel(wrapper, state, pseudo_states)
                else:
                    self._write_state(wrapper, state, pseudo_states)
            # Write region‑level transitions inside the wrapper
            self._write_transitions(wrapper, region)

    # ── Write a single state (or parallel) ─────────────────────────
    def _write_state(self, parent: Element, state: State,
                     pseudo_states: list[PseudoState], is_parallel: bool = False) -> None:
        tag = "parallel" if (is_parallel or state.parallel) else "state"
        elem = SubElement(parent, f"{{{SCXML_NS}}}{tag}", {"id": state.id})
        if state.name:
            elem.set("name", state.name)

        # Final state
        if state.is_final:
            final = SubElement(elem, f"{{{SCXML_NS}}}final", {"id": state.id})
            if state.name:
                final.set("name", state.name)
            self._write_entry_exit(final, state)
            return  # final state has no transitions

        # Pseudo‑states that belong to this state (parent_state matches)
        for pseudo in pseudo_states:
            if pseudo.parent_state is state:
                self._write_pseudo_state(elem, pseudo)

        # Initial attribute (points to a child state or pseudo‑state)
        if state.initial:
            if isinstance(state.initial, State):
                elem.set("initial", state.initial.id)
            elif isinstance(state.initial, PseudoState):
                elem.set("initial", state.initial.id)
            else:
                # Should not happen, but fallback to string
                elem.set("initial", str(state.initial))

        # Invoke
        if state.invoke:
            self._write_invoke(elem, state.invoke)

        # Entry / Exit actions
        self._write_entry_exit(elem, state)

        # Transitions
        for trans in state.outgoing_transitions:
            self._write_transition(elem, trans)

        # Sub‑regions (recursive)
        for sub_region in state.regions:
            for child_state in sub_region.states:
                if child_state.parallel:
                    self._write_parallel(elem, child_state, pseudo_states)
                else:
                    self._write_state(elem, child_state, pseudo_states)
            self._write_transitions(elem, sub_region)

    def _write_parallel(self, parent: Element, state: State,
                        pseudo_states: list[PseudoState]) -> None:
        self._write_state(parent, state, pseudo_states, is_parallel=True)

    # ── Pseudo‑state ──────────────────────────────────────────────
    def _write_pseudo_state(self, parent: Element, pseudo: PseudoState) -> None:
        if pseudo.kind == PseudoStateKind.INITIAL:
            tag = "initial"
        elif pseudo.kind in (PseudoStateKind.DEEP_HISTORY, PseudoStateKind.SHALLOW_HISTORY):
            tag = "history"
        else:
            return  # others not mapped
        elem = SubElement(parent, f"{{{SCXML_NS}}}{tag}", {"id": pseudo.id})
        # For history, set the type attribute
        if tag == "history":
            if pseudo.kind == PseudoStateKind.DEEP_HISTORY:
                elem.set("type", "deep")
            else:
                elem.set("type", "shallow")
        # Write the transition contained in the pseudo‑state
        for trans in pseudo.outgoing_transitions:
            self._write_transition(elem, trans)

    # ── Entry / Exit scripts ──────────────────────────────────────
    def _write_entry_exit(self, elem: Element, state: State) -> None:
        if state.entry_actions:
            onentry = SubElement(elem, f"{{{SCXML_NS}}}onentry")
            for action in state.entry_actions:
                if isinstance(action, Script):
                    self._write_script(onentry, action)
        if state.exit_actions:
            onexit = SubElement(elem, f"{{{SCXML_NS}}}onexit")
            for action in state.exit_actions:
                if isinstance(action, Script):
                    self._write_script(onexit, action)

    def _write_script(self, parent: Element, script: Script) -> None:
        script_elem = SubElement(parent, f"{{{SCXML_NS}}}script")
        script_elem.text = script.script_body
        if script.script_language:
            lang = script.script_language.value if hasattr(script.script_language, 'value') else str(script.script_language)
            script_elem.set("language", lang)

    # ── Invoke ────────────────────────────────────────────────────
    def _write_invoke(self, parent: Element, invoke: StateInvoke) -> None:
        inv = SubElement(parent, f"{{{SCXML_NS}}}invoke")
        inv.set("type", invoke.invoke_type)
        if invoke.src:
            if isinstance(invoke.src, str):
                inv.set("src", invoke.src)
            else:
                # SSDM document reference – ignore
                pass
        if invoke.id:
            inv.set("id", invoke.id)

    # ── Transition ────────────────────────────────────────────────
    def _write_transition(self, parent: Element, trans: Transition) -> None:
        """
        Write a transition. The parameter type is `Transition` (base class),
        but we know that in state machines it is always a `StateTransition`.
        """
        if not isinstance(trans, StateTransition):
            return
        if not trans.target:
            return
        elem = SubElement(parent, f"{{{SCXML_NS}}}transition")
        elem.set("target", trans.target.id)

        if trans.trigger:
            elem.set("event", trans.trigger.body or "")

        if trans.guard:
            elem.set("cond", trans.guard.body or "")

        if trans.effect:
            script = SubElement(elem, f"{{{SCXML_NS}}}script")
            script.text = trans.effect.body or ""

    def _write_transitions(self, parent: Element, region: StateMachineRegion) -> None:
        for trans in region.transitions:
            self._write_transition(parent, trans)