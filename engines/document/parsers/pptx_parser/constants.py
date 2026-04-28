# engines/document/parsers/pptx_parser/constants.py
"""
PPTX parser constants – namespaces, relationship types, and mappings.
"""

from __future__ import annotations
from enum import Enum

# ── XML Namespaces ─────────────────────────────────────────────────
NAMESPACES = {
    "a":   "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r":   "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "p":   "http://schemas.openxmlformats.org/presentationml/2006/main",
    "p14": "http://schemas.microsoft.com/office/powerpoint/2010/main",
    "p15": "http://schemas.microsoft.com/office/powerpoint/2012/main",
    "mc":  "http://schemas.openxmlformats.org/markup-compatibility/2006",
}

# ── Relationship Types ─────────────────────────────────────────────
REL_TYPE = {
    "slide":         "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide",
    "slideLayout":   "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout",
    "slideMaster":   "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster",
    "notes":         "http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide",
    "image":         "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image",
    "chart":         "http://schemas.openxmlformats.org/officeDocument/2006/relationships/chart",
    "diagram":       "http://schemas.openxmlformats.org/officeDocument/2006/relationships/diagram",
    "hyperlink":     "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
    "media":         "http://schemas.openxmlformats.org/officeDocument/2006/relationships/media",
    "audio":         "http://schemas.openxmlformats.org/officeDocument/2006/relationships/audio",
    "video":         "http://schemas.openxmlformats.org/officeDocument/2006/relationships/video",
    "theme":         "http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme",
    "vmlDrawing":    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/vmlDrawing",
}

# ── Transition Mappings ────────────────────────────────────────────
# PPTX transition token → PSDM TransitionType
PPTX_TRANSITION_MAP = {
    "fade":    "fade",
    "push":    "push",
    "wipe":    "wipe",
    "split":   "split",
    "cover":   "cover",
    "uncover": "uncover",
    "zoom":    "zoom",
    "random":  "random",
    "none":    "none",
    # Additional types often encountered
    "blinds":  "wipe",       # mapped to wipe
    "checker": "random",     # mapped to random bar
    "comb":    "push",
    "dissolve":"fade",
    "fadeThroughBlack": "fade",
    "morph":   "fade",       # morph not explicitly modeled, treated as fade
    "pageCurl":"cover",
    "pan":     "push",
    "plus":    "split",
    "pull":    "push",
    "randomBar":"random",
    "ripple":  "fade",
    "shape":   "wipe",
    "strips":  "wipe",
    "vortex":  "zoom",
    "wheel":   "wipe",
}

# ── Animation Mappings ─────────────────────────────────────────────
# PPTX animation preset → PSDM AnimationType
PPTX_ANIM_MAP = {
    # Entrance
    "appear":       "appear",
    "fadeIn":       "fadeIn",
    "flyIn":        "flyIn",
    "zoomIn":       "zoomIn",
    "grow":         "grow",
    "spin":         "spin",
    "customPath":   "customPath",
    # Additional common presets mapped to base types
    "fade":         "fadeIn",
    "zoom":         "zoomIn",
    "swivel":       "spin",
    "bounce":       "grow",
    "floatIn":      "flyIn",
    "basicZoom":    "zoomIn",
    "split":        "appear",
    "wipe":         "appear",
    "wheel":        "appear",
    "shape":        "appear",
}

# ── Placeholder Type Mapping ───────────────────────────────────────
PPTX_PLACEHOLDER_MAP = {
    "title":    "title",
    "subTitle": "subtitle",
    "body":     "body",
    "ctrTitle": "subtitle",
    "pic":      "picture",
    "chart":    "chart",
    "tbl":      "table",
    "media":    "media",
    "clipArt":  "clipArt",
    "dgm":      "diagram",
    "obj":      "object",
    "sldNum":   "slideNumber",
    "hd":       "header",
    "ftr":      "footer",
    "dt":       "date",
}