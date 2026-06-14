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
- state initial attribute → State.initial_state_id (resolved later)
"""
from __future__ import annotations

import uuid
from xml.etree import ElementTree as ET
from typing import Any

from engines.document.models.media_types import MEDIA_TYPES
from ..bpmn.models.bpmn_models import FormalExpression, Script, ScriptLanguage
from .shared_models import BaseOSDMDocument, PseudoStateKind
from ..state_machine.models.state_machine_models import (
    PseudoState,
    State,
    StateInvoke,
    StateMachineDocument,
    StateMachineModel,
    StateMachineRegion,
    StateTransition,
)
from engines.document.parsers.base import ParseOptions
from .base_osdm_parser import BaseOSDMParser

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

        doc = StateMachineDocument(
            document_id=root.get("id", source_name),
            title=root.get("name", source_name),
            media_type=MEDIA_TYPES.get("scxml", MEDIA_TYPES["xml"])
        )
        doc.source_file = source_name

        sm = self._parse_scxml(root)
        doc.state_machines.append(sm)
        return doc

    def _parse_scxml(self, root: ET.Element) -> StateMachineModel:
        sm_id = root.get("id", root.get("name", "scxml"))
        sm_name = root.get("name", sm_id)
        sm = StateMachineModel(id=sm_id, name=sm_name)

        top_region = StateMachineRegion(id=str(uuid.uuid4().hex), name="top_region")
        sm.top_region = top_region

        # Collect all pseudo‑states and states for reference resolution
        pseudo_states: dict[str, PseudoState] = {}
        all_states: dict[str, State] = {}

        # Parse top‑level state or parallel (only one allowed as direct child)
        state_elem = None
        for child in root:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag in ("state", "parallel"):
                state_elem = child
                break

        if state_elem is not None:
            root_state = self._parse_state_or_parallel(state_elem, pseudo_states)
            top_region.states.append(root_state)

            # First pass: collect all states recursively
            self._collect_states(root_state, all_states)

            # Second pass: resolve references (transitions, initial state, etc.)
            self._resolve_references(root_state, pseudo_states, all_states)

            # Set initial state from top region's initial attribute or pseudo‑state
            initial_target = root.get("initial")
            if initial_target:
                # It may be a pseudo‑state id
                if initial_target in pseudo_states:
                    ps = pseudo_states[initial_target]
                    # The pseudo‑state should have an outgoing transition; use its target
                    if ps.outgoing_transitions:
                        target_state = ps.outgoing_transitions[0].target
                        if target_state and isinstance(target_state, State):
                            top_region.initial_state = target_state
                elif initial_target in all_states:
                    top_region.initial_state = all_states[initial_target]
            elif root_state and top_region.states:
                # Fallback: first state in top region
                top_region.initial_state = top_region.states[0]

        sm.pseudo_states = list(pseudo_states.values())
        return sm

    def _parse_state_or_parallel(self, elem: ET.Element, pseudo_states: dict[str, PseudoState]) -> State:
        tag_name = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        is_parallel = (tag_name == "parallel")
        state_id = elem.get("id", "")
        state = State(
            id=state_id,
            name=elem.get("name", ""),
            parallel=is_parallel,
        )

        # Initial attribute (pointer to a child state or pseudo‑state)
        initial_attr = elem.get("initial")
        if initial_attr:
            state.initial_state_id = initial_attr  # store ID for later resolution

        # Parse children
        for child in elem:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag in ("state", "parallel"):
                sub_state = self._parse_state_or_parallel(child, pseudo_states)
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
                kind = PseudoStateKind.DEEP_HISTORY if child.get("type") == "deep" else PseudoStateKind.SHALLOW_HISTORY
                pseudo = self._parse_pseudo_state(child, kind, state)
                pseudo_states[pseudo.id] = pseudo
            elif tag == "final":
                sub_state = self._parse_final(child)
                self._add_to_region(state, sub_state)

        return state

    def _add_to_region(self, parent: State, child: State) -> None:
        """Add child state to a sub‑region of the parent (creating if needed)."""
        if not parent.regions:
            parent.regions.append(StateMachineRegion(id=str(uuid.uuid4().hex)))
            parent.is_composite = True
        # For parallel states, we might want separate regions; but SCXML parallel <parallel> creates orthogonal regions.
        # However, in OSDM, a parallel state is indicated by the `parallel` flag and contains regions (one per parallel branch?).
        # In SCXML, a <parallel> element contains multiple <state> children – each becomes a separate region.
        # To keep it simple, we group all children into the first region unless we want to create one region per branch.
        # We'll follow the OSDM interpretation: if parent is parallel, each child becomes its own region.
        if parent.parallel:
            # Create a new region for this child
            region = StateMachineRegion(id=str(uuid.uuid4().hex))
            region.states.append(child)
            parent.regions.append(region)
        else:
            parent.regions[0].states.append(child)

    def _parse_transition(self, elem: ET.Element, source: State) -> StateTransition | None:
        target_id = elem.get("target")
        if not target_id:
            return None
        trans = StateTransition(
            id=elem.get("id", f"{source.id}_to_{target_id}"),
            source=source,
            target=None,  # will be resolved later
        )
        trans._target_id = target_id  # temporary attribute

        event = elem.get("event")
        if event:
            trans.trigger = FormalExpression(id=str(uuid.uuid4().hex), body=event)
        cond = elem.get("cond")
        if cond:
            trans.guard = FormalExpression(id=str(uuid.uuid4().hex), body=cond)
        # effect: child <script> or inline?
        script_elem = elem.find("scxml:script", NS)
        if script_elem is not None and script_elem.text:
            trans.effect = FormalExpression(id=str(uuid.uuid4().hex), body=script_elem.text)

        return trans

    def _parse_on_entry_exit(self, elem: ET.Element, actions: list[Script]) -> None:
        for child in elem:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag == "script":
                body = child.text or ""
                lang = child.get("language", "Python")
                lang_enum = ScriptLanguage.PYTHON
                if lang in ("js", "javascript"):
                    lang_enum = ScriptLanguage.JS
                script = Script(
                    id=str(uuid.uuid4().hex),
                    name=None,
                    script_body=body,
                    script_language=lang_enum,
                )
                actions.append(script)
            # Other tags (log, raise, assign) can be added later

    def _parse_invoke(self, elem: ET.Element) -> StateInvoke:
        return StateInvoke(
            invoke_type=elem.get("type", ""),
            src=elem.get("src"),
            id=elem.get("id"),
        )

    def _parse_final(self, elem: ET.Element) -> State:
        state = State(
            id=elem.get("id", ""),
            name=elem.get("name", ""),
            is_final=True,
        )
        return state

    def _parse_pseudo_state(self, elem: ET.Element, kind: PseudoStateKind, parent: State) -> PseudoState:
        pseudo = PseudoState(
            id=elem.get("id", ""),
            kind=kind,
            parent_state=parent,
        )
        # Pseudo‑state may have a single transition with target
        transition_elem = elem.find("scxml:transition", NS)
        if transition_elem is not None:
            target_id = transition_elem.get("target")
            if target_id:
                trans = StateTransition(
                    id=f"{pseudo.id}_to_{target_id}",
                    source=pseudo,
                    target=None,
                )
                trans._target_id = target_id
                pseudo.outgoing_transitions.append(trans)
        return pseudo

    def _collect_states(self, state: State, all_states: dict[str, State]) -> None:
        """Recursively collect all states into a dictionary by ID."""
        if state.id:
            all_states[state.id] = state
        for region in state.regions:
            for s in region.states:
                self._collect_states(s, all_states)

    def _resolve_references(
        self, root_state: State, pseudo_states: dict[str, PseudoState], all_states: dict[str, State]
    ) -> None:
        """Resolve all temporary ID references to actual objects."""
        # Resolve transitions targets
        def resolve_transitions(obj: Any) -> None:
            for trans in getattr(obj, 'outgoing_transitions', []):
                if hasattr(trans, '_target_id') and trans._target_id:
                    if trans._target_id in all_states:
                        trans.target = all_states[trans._target_id]
                    elif trans._target_id in pseudo_states:
                        # Pseudo‑state as target? OSDM Transition expects StateNode; PseudoState is a StateNode, good.
                        trans.target = pseudo_states[trans._target_id]
                    # Remove temporary attribute
                    del trans._target_id
            if isinstance(obj, State):
                for region in obj.regions:
                    for s in region.states:
                        resolve_transitions(s)

        resolve_transitions(root_state)
        for pseudo in pseudo_states.values():
            resolve_transitions(pseudo)

        # Resolve state.initial_state_id references
        def resolve_initial(state: State) -> None:
            if state.initial_state_id:
                if state.initial_state_id in all_states:
                    # We need to set the initial child state – OSDM doesn't have a direct field for the initial child.
                    # Instead, we can mark the target state as the initial state of the parent's first region.
                    # This is a known limitation; we store the reference in the region's initial_state field if applicable.
                    initial_child = all_states[state.initial_state_id]
                    # If the state is composite and has at least one region, set that region's initial state.
                    if state.regions:
                        # Find the region that contains this child
                        for region in state.regions:
                            if initial_child in region.states:
                                region.initial_state = initial_child
                                break
                elif state.initial_state_id in pseudo_states:
                    # Follow pseudo‑state's transition to get target
                    pseudo = pseudo_states[state.initial_state_id]
                    if pseudo.outgoing_transitions and pseudo.outgoing_transitions[0].target:
                        target = pseudo.outgoing_transitions[0].target
                        if isinstance(target, State) and state.regions:
                            for region in state.regions:
                                if target in region.states:
                                    region.initial_state = target
                                    break
                # Clear the temporary ID
                state.initial_state_id = None

            for region in state.regions:
                for s in region.states:
                    resolve_initial(s)

        resolve_initial(root_state)