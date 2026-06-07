# engines/document/writers/pptx_writer/animation_writer.py
"""
Writes slide transition and animation XML elements.
"""
from __future__ import annotations

from xml.etree.ElementTree import Element
from xml.etree.ElementTree import SubElement

from ...models.psdm_models import Animation
from ...models.psdm_models import PresentationTransition
from ...models.psdm_models import TriggerType
from .constants import NAMESPACES
from .constants import PSDM_TO_PPTX_ANIM
from .constants import PSDM_TO_PPTX_TRANSITION

NS = NAMESPACES
P = f"{{{NS['p']}}}"
A = f"{{{NS['a']}}}"


def write_transition(transition: PresentationTransition) -> Element | None:
    """
    Create a <p:transition> element from a PresentationTransition object.

    Returns None if the transition is NONE.
    """
    if transition.type.value == "none":
        return None

    trans_elem = Element(f"{P}transition")
    trans_type = PSDM_TO_PPTX_TRANSITION.get(transition.type.value, "fade")

    # Child element determines the transition type
    child = SubElement(trans_elem, f"{P}{trans_type}")
    if transition.duration_ms:
        child.set("dur", str(int(transition.duration_ms)))
    if transition.advance_after_ms:
        trans_elem.set("advTm", str(int(transition.advance_after_ms)))

    return trans_elem


def write_animations(animations: list[Animation]) -> Element | None:
    """
    Build the <p:timing> element tree for a list of animations.
    Returns None if the list is empty.
    """
    if not animations:
        return None

    # Simple approach: wrap all animations in a single sequence (seq)
    timing = Element(f"{P}timing")
    seq = SubElement(timing, f"{P}seq")

    for anim in animations:
        anim_elem = _build_animation_node(anim)
        if anim_elem is not None:
            seq.append(anim_elem)

    return timing


def _build_animation_node(anim: Animation) -> Element:
    """Build a <p:animEffect> or equivalent element for a single animation."""
    preset = PSDM_TO_PPTX_ANIM.get(anim.type.value, "appear")

    # Basic animEffect
    anim_elem = Element(f"{P}animEffect")

    # cBhvr
    cbvr = SubElement(anim_elem, f"{P}cBhvr")
    # Target element (the shape)
    tgt_el = SubElement(cbvr, f"{P}tgtEl")
    _sp_tgt = SubElement(tgt_el, f"{P}spTgt", {"spid": anim.target_shape_id})

    # Duration and delay
    if anim.duration_ms:
        cbvr.set("dur", str(int(anim.duration_ms)))
    if anim.delay_ms:
        cbvr.set("st", str(int(anim.delay_ms)))

    # Trigger (on click = default)
    if anim.trigger != TriggerType.ON_CLICK:
        # Set the appropriate attributes
        if anim.trigger == TriggerType.AFTER_PREVIOUS:
            cbvr.set("after", "prev")
        elif anim.trigger == TriggerType.WITH_PREVIOUS:
            cbvr.set("after", "with")

    # Preset ID
    SubElement(cbvr, f"{P}presetID", {"val": preset})

    return anim_elem
