# engines/document/writers/pptx_writer/constants.py
"""
PPTX writer constants – shared namespace definitions and reverse mappings.
"""
from __future__ import annotations

# ── XML Namespaces (identical to parser) ────────────────────────────
NAMESPACES = {
    "a":   "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r":   "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "p":   "http://schemas.openxmlformats.org/presentationml/2006/main",
    "p14": "http://schemas.microsoft.com/office/powerpoint/2010/main",
    "p15": "http://schemas.microsoft.com/office/powerpoint/2012/main",
    "mc":  "http://schemas.openxmlformats.org/markup-compatibility/2006",
}

# ── Relationship Types (same as parser) ─────────────────────────────
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

# ── Reverse PresentationTransition Map (PSDM → PPTX) ───────────────────────────
PSDM_TO_PPTX_TRANSITION = {
    "fade":    "fade",
    "push":    "push",
    "wipe":    "wipe",
    "split":   "split",
    "cover":   "cover",
    "uncover": "uncover",
    "zoom":    "zoom",
    "random":  "random",
    "none":    "none",
}

# ── Reverse Animation Map (PSDM → PPTX preset) ──────────────────────
PSDM_TO_PPTX_ANIM = {
    "appear":   "appear",
    "fadeIn":   "fadeIn",
    "flyIn":    "flyIn",
    "zoomIn":   "zoomIn",
    "spin":     "spin",
    "grow":     "grow",
    "customPath":"customPath",
}

# ── Reverse Placeholder Map ─────────────────────────────────────────
PSDM_TO_PPTX_PLACEHOLDER = {
    "title":        "title",
    "subtitle":     "subTitle",
    "body":         "body",
    "picture":      "pic",
    "chart":        "chart",
    "table":        "tbl",
    "media":        "media",
    "clipArt":      "clipArt",
    "diagram":      "dgm",
    "object":       "obj",
    "slideNumber":  "sldNum",
    "header":       "hd",
    "footer":       "ftr",
    "date":         "dt",
}
