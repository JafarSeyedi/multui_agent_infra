# engines/document/parsers/pptx_parser/animation_parser.py
"""
Parses slide transitions and animations from PPTX slide XML.
Produces PSDM PresentationTransition and list of Animation objects.
"""
from __future__ import annotations

from xml.etree.ElementTree import Element

from ...models.psdm_models import Animation
from ...models.psdm_models import AnimationType
from ...models.psdm_models import PresentationTransition
from ...models.psdm_models import TransitionType
from ...models.psdm_models import TriggerType
from .constants import NAMESPACES
from .constants import PPTX_ANIM_MAP
from .constants import PPTX_TRANSITION_MAP

NS = NAMESPACES


def parse_slide_transition(slide_xml: Element) -> PresentationTransition:
    """
    Extract transition from a <p:sld> element.

    Looks for <p:transition> child directly under the slide.
    """
    trans_elem = slide_xml.find("p:transition", NS)
    if trans_elem is None:
        return PresentationTransition()

    # Determine the transition type – it's the local name of the first child element
    trans_type = TransitionType.NO_TRANSITION
    duration = 500.0
    advance = None

    for child in trans_elem:
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        mapped = PPTX_TRANSITION_MAP.get(tag)
        if mapped:
            trans_type = TransitionType(mapped)
            # Duration in ms (attribute "dur" in milliseconds)
            dur_str = child.get("dur")
            if dur_str:
                duration = _parse_duration_ms(dur_str)
            # Advance after
            adv_str = trans_elem.get("advTm")
            if adv_str:
                advance = _parse_duration_ms(adv_str)
            break

    return PresentationTransition(
        type=trans_type,
        duration_ms=duration,
        advance_after_ms=advance,
    )


def parse_slide_animations(slide_xml: Element) -> list[Animation]:
    """
    Extract animations from a <p:sld> element.

    Animations are stored under <p:timing> structure.
    We search for <p:animEffect>, <p:animMotion>, <p:anim>, etc.
    """
    animations: list[Animation] = []

    timing = slide_xml.find("p:timing", NS)
    if timing is None:
        return animations

    # Process timing tree – look for animation nodes
    _process_timing_node(timing, animations, None, 0.0)

    return animations


def _process_timing_node(
    elem: Element,
    animations: list[Animation],
    parent_trigger: TriggerType | None,
    cumulative_delay: float,
) -> None:
    """Recursively traverse a <p:timing> subtree and collect animations."""
    tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag

    if tag == "animEffect":
        anim = _parse_anim_effect(elem, parent_trigger, cumulative_delay)
        if anim:
            animations.append(anim)
        return

    # Container nodes: par, seq, excl, etc.
    # They may have child timings
    child_tnlst = elem.find("p:childTnLst", NS)
    if child_tnlst is not None:
        # Determine trigger for children from this container
        trigger = parent_trigger
        # Override with container's own trigger
        ctn = elem.find("p:cTn", NS)
        if ctn is not None:
            node_type = ctn.get("nodeType")
            # "interactive" usually means onclick
            if node_type == "interactive" or ctn.get("after") == "indefinite":
                trigger = TriggerType.ON_CLICK
            elif node_type == "after":
                trigger = TriggerType.AFTER_PREVIOUS
            elif node_type == "with":
                trigger = TriggerType.WITH_PREVIOUS

        for child in child_tnlst:
            _process_timing_node(child, animations, trigger, cumulative_delay)


def _parse_anim_effect(
    elem: Element,
    parent_trigger: TriggerType | None,
    cumulative_delay: float,
) -> Animation | None:
    """Parse a <p:animEffect> element into an Animation."""
    # Target shape
    target = elem.get("spid", "")

    # Determine animation type from preset or filter
    anim_type = AnimationType.APPEAR
    # Look inside child <p:cBhvr> or <p:attrName>
    cbvr = elem.find("p:cBhvr", NS)
    if cbvr is not None:
        # Check for <p:attrNameLst>
        attr_name = cbvr.find("p:attrName", NS)
        if attr_name is not None:
            val = attr_name.text
            if val == "style.visibility" or val == "ppt_x":
                anim_type = AnimationType.APPEAR
            elif val == "ppt_y":
                anim_type = AnimationType.FLY_IN
            elif val == "r":
                anim_type = AnimationType.SPIN
            elif val == "ppt_w" or val == "ppt_h":
                anim_type = AnimationType.GROW

        # Also check for preset ID
        preset = cbvr.find("p:presetID", NS)
        if preset is not None and preset.text:
            mapped = PPTX_ANIM_MAP.get(preset.text)
            if mapped:
                anim_type = AnimationType(mapped)

    # Duration and delay
    duration = 500.0
    delay = cumulative_delay

    ctn = elem.find("p:cTn", NS)
    if ctn is not None:
        dur_str = ctn.get("dur")
        if dur_str:
            duration = _parse_duration_ms(dur_str)
        delay_str = ctn.get("stCondLst/p:cond/delay")  # not exactly; need to parse
        # Simpler: get "st" attribute or child conditions
    # Fallback: use the elem's own duration/delay from cBhvr
    if cbvr is not None:
        tgt_el = cbvr.find("p:tgtEl", NS)
        if tgt_el is not None:
            # Can retrieve spid from tgtEl/spTgt if not on parent
            sp_tgt = tgt_el.find("p:spTgt", NS)
            if sp_tgt is not None and not target:
                target = sp_tgt.get("spid", "")

    # Trigger
    trigger = parent_trigger or TriggerType.ON_CLICK

    return Animation(
        target_shape_id=target,
        type=anim_type,
        duration_ms=duration,
        delay_ms=delay,
        trigger=trigger,
    )


def _parse_duration_ms(dur_str: str) -> float:
    """
    Convert a PPTX duration string to milliseconds.
    Format: "indefinite", or a number in milliseconds (e.g., "2000").
    """
    if dur_str == "indefinite":
        return 0.0
    try:
        return float(dur_str)
    except ValueError:
        return 0.0
