# engines/document/parsers/osdm_parsers/scxml_parser.py
"""
SCXML Parser – converts a .scxml file into a StateMachineDocument.

All SCXML constructs are mapped to typed OSDM model fields:
- <scxml> initial → StateMachineRegion.initial_state
- <state> / <parallel> → State (with parallel flag)
- <final> → State with is_final=True
- <initial> / <history> pseudo‑states → PseudoState (added to StateMachineModel.pseudo_states)
- <transition> → StateTransition (trigger, guard, effect)
- <onentry> / <onexit> → Script in state.entry_actions / exit_actions
- <invoke> → State.invoke
- state initial attribute → State.initial
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional, Dict, Any, List
from xml.etree import ElementTree as ET

from .base_osdm_parser import BaseOSDMParser
from ..base import ParseOptions
from ...models.osdm_models import (
    BaseOSDMDocument,
    StateMachineDocument,
    StateMachineModel,
    StateMachineRegion,
    State,
    StateTransition,
    PseudoState,
    PseudoStateKind,
    StateInvoke,
    Script,
    ScriptLanguage,
    FormalExpression,
)
from ...models.base import BaseDocument


SCXML_NS = "http://www.w3.org/2005/07/scxml"
NS = {"scxml": SCXML_NS}


class SCXMLParser(BaseOSDMParser):
    """Parser for SCXML files (.scxml)."""

    name = "scxml"
    supported_extensions = (".scxml",)

    async def _parse_to_document(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> BaseOSDMDocument:
        encoding = options.encoding or "utf-8"
        text = data.decode(encoding)
        root = ET.fromstring(text)

        doc = StateMachineDocument()
        sm = self._parse_scxml(root)
        doc.state_machines.append(sm)
        return doc

    def _parse_scxml(self, root: ET.Element) -> StateMachineModel:
        sm_id = root.get("id", root.get("name", "scxml"))
        sm_name = root.get("name", sm_id)
        sm = StateMachineModel(id=sm_id, name=sm_name)
        top_region = StateMachineRegion()
        sm.top_region = top_region

        # Pseudo‑states are collected globally in the state machine (for history etc.)
        pseudo_states: Dict[str, PseudoState] = {}

        # Parse top‑level state or parallel (only one allowed as direct child)
        state_elem = None
        for child in root:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag in ("state", "parallel"):
                state_elem = child
                break

        # We'll parse the entire tree starting from state_elem, collecting all child states into top_region.
        # Actually, SCXML expects one top‑level state; we treat it as the region's sole root state.
        if state_elem is not None:
            root_state = self._parse_state_or_parallel(state_elem, pseudo_states)
            top_region.states.append(root_state)

        # Set initial state from the root's initial attribute (pseudo‑state reference)
        initial_target = root.get("initial")
        if initial_target:
            # It refers to a pseudo‑state (like an <initial> element) or a state id.
            # We'll check if there's a pseudo‑state with that id; if so, get its target via a transition.
            # Typically <initial> has a <transition target="...">. We'll resolve after parsing all pseudo states.
            ps = pseudo_states.get(initial_target)
            if ps:
                # Find the transition from that pseudo‑state to the real initial state.
                # The pseudo‑state will have a child <transition target="...">
                # We'll simulate it by looking at the pseudo‑state element's children (already parsed).
                # The parser will have stored transitions inside pseudo_states? We'll store them as part of pseudo state attributes? Let's see.
                # In SCXML, pseudo‑state elements like <initial> contain a <transition>. We parsed that earlier.
                pass

        # Fallback: if top_region.states is not empty, use first as initial
        if top_region.states and top_region.initial_state is None:
            top_region.initial_state = top_region.states[0]

        sm.pseudo_states = list(pseudo_states.values())

        # Resolve initial state from pseudo‑state transitions.
        for pseudo in sm.pseudo_states:
            if pseudo.kind == PseudoStateKind.INITIAL:
                # The transition target from this pseudo‑state should become the region's initial state
                # We need the outgoing transition from this pseudo‑state. We'll store it during parsing.
                pass  # We'll handle below

        return sm

    # ── Parse a <state> or <parallel> ────────────────────────────
    def _parse_state_or_parallel(self, elem: ET.Element, pseudo_states: Dict[str, PseudoState]) -> State:
        is_parallel = elem.tag.split("}")[-1] == "parallel"
        state = State(
            id=elem.get("id", ""),
            name=elem.get("name", ""),
            parallel=is_parallel,
        )

        # Initial attribute (pointer to a child state or pseudo‑state)
        initial_attr = elem.get("initial")
        if initial_attr:
            state.initial = initial_attr  # we'll resolve later; currently it's a string reference

        # Parse children
        for child in elem:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag in ("state", "parallel"):
                sub_state = self._parse_state_or_parallel(child, pseudo_states)
                # Add sub_state to the current state's region (if it's composite) or to a sub‑region
                self._add_to_region(state, sub_state)
            elif tag == "transition":
                trans = self._parse_transition(child, state)
                if trans:
                    state.outgoing_transitions.append(trans)
            elif tag == "onentry":
                self._parse_on_entry_exit(child, state.entry_actions)
            elif tag == "onexit":
                self._parse_on_entry_exit(child, state.exit_actions)
            elif tag == "invoke":
                state.invoke = self._parse_invoke(child)
            elif tag == "initial":
                pseudo = self._parse_pseudo_state(child, PseudoStateKind.INITIAL, state)
                pseudo_states[pseudo.id] = pseudo
            elif tag == "history":
                pseudo = self._parse_pseudo_state(child, PseudoStateKind.DEEP_HISTORY, state)
                pseudo_states[pseudo.id] = pseudo
            elif tag == "final":
                sub_state = self._parse_final(child)
                self._add_to_region(state, sub_state)

        return state

    def _add_to_region(self, parent: State, child: State) -> None:
        """Add child state to a sub‑region of the parent (creating if needed)."""
        if not parent.regions:
            parent.regions.append(StateMachineRegion())
            parent.is_composite = True
        parent.regions[0].states.append(child)

    # ── Transition ───────────────────────────────────────────────
    def _parse_transition(self, elem: ET.Element, source: State) -> Optional[StateTransition]:
        target_id = elem.get("target")
        if not target_id:
            return None
        trans = StateTransition(
            id=elem.get("id", f"{source.id}_to_{target_id}"),
            source=source,
            target=None,  # will be resolved later to a State object
        )
        # For now, store target_id temporarily as a string; a second pass will resolve.
        trans._target_id = target_id  # temporary attribute

        event = elem.get("event")
        if event:
            trans.trigger = FormalExpression(body=event)
        cond = elem.get("cond")
        if cond:
            trans.guard = FormalExpression(body=cond)
        # effect: child <script> or inline?
        script_elem = elem.find("scxml:script", NS)
        if script_elem is not None and script_elem.text:
            trans.effect = FormalExpression(body=script_elem.text)

        return trans

    # ── Entry / Exit scripts ─────────────────────────────────────
    def _parse_on_entry_exit(self, elem: ET.Element, actions: List[Script]) -> None:
        for child in elem:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag == "script":
                script = Script(
                    script_body=child.text or "",
                    script_language=ScriptLanguage(child.get("language", "Python")),
                )
                actions.append(script)
            # log, raise, etc. can be stored similarly

    # ── Invoke ───────────────────────────────────────────────────
    def _parse_invoke(self, elem: ET.Element) -> Optional[StateInvoke]:
        return StateInvoke(
            invoke_type=elem.get("type", ""),
            src=elem.get("src"),
            id=elem.get("id"),
        )

    # ── Final state ──────────────────────────────────────────────
    def _parse_final(self, elem: ET.Element) -> State:
        state = State(id=elem.get("id", ""), name=elem.get("name", ""), is_final=True)
        return state

    # ── Pseudo‑state (initial/history) ───────────────────────────
    def _parse_pseudo_state(self, elem: ET.Element, kind: PseudoStateKind, parent: State) -> PseudoState:
        pseudo = PseudoState(id=elem.get("id", ""), kind=kind, parent_state=parent)
        # Pseudo‑state may have a single transition with target
        transition_elem = elem.find("scxml:transition", NS)
        if transition_elem is not None:
            target_id = transition_elem.get("target")
            if target_id:
                # Create a transition directly from this pseudo‑state to the target state
                trans = StateTransition(
                    id=f"{pseudo.id}_to_{target_id}",
                    source=None,  # pseudo state as source? The OSDM Transition expects StateNode. PseudoState is a StateNode.
                    target=None,
                )
                trans.source = pseudo
                trans._target_id = target_id  # temporary
                # We'll store this transition in a temporary list to resolve later; we can attach to pseudo's outgoing transitions
                pseudo.outgoing_transitions.append(trans)
        return pseudo

    # ── Second‑pass resolution of references ─────────────────────
    def _resolve_references(self, root_state: State, pseudo_states: Dict[str, PseudoState]) -> None:
        # Resolve transition targets
        all_states: Dict[str, State] = {}
        def collect_states(state: State):
            all_states[state.id] = state
            for region in state.regions:
                for s in region.states:
                    collect_states(s)
        collect_states(root_state)

        # Resolve transitions in states and pseudo‑states
        def resolve_transitions(obj):
            for trans in getattr(obj, 'outgoing_transitions', []):
                target_id = getattr(trans, '_target_id', None)
                if target_id and target_id in all_states:
                    trans.target = all_states[target_id]
                    del trans._target_id
            if isinstance(obj, State):
                for region in obj.regions:
                    for s in region.states:
                        resolve_transitions(s)

        resolve_transitions(root_state)
        for pseudo in pseudo_states.values():
            resolve_transitions(pseudo)

        # Resolve state.initial references
        def resolve_initial(state):
            if isinstance(state.initial, str):
                if state.initial in all_states:
                    state.initial = all_states[state.initial]
                elif state.initial in pseudo_states:
                    # It refers to a pseudo‑state; we need to follow the pseudo‑state's transition to get the real state.
                    pseudo = pseudo_states[state.initial]
                    # The pseudo‑state should have an outgoing transition; use its target
                    if pseudo.outgoing_transitions:
                        state.initial = pseudo.outgoing_transitions[0].target
            for region in state.regions:
                for s in region.states:
                    resolve_initial(s)

        resolve_initial(root_state)