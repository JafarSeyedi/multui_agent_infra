# engines/document/models/psdm_models.py
"""
PSDM (Presentation Structured Document Model)
===============================================
Domain model for presentations (e.g., PPTX).
Extends BaseDocument and reuses USDM content types.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Tuple, Union

from ..base import BaseDocument, ElementType
from ..media_types import DocumentStandard
from ..usdm_models import (
    # Content types used directly in slides
    RichTextContent,
    ShapeContent,
    ImageContent,
    ChartContent,
    TableContent,
    AudioContent,
    VideoContent,
    DrawingContent,   # for SmartArt/diagrams
    LogicalElement,
    # Reference to styles (optional, can be used for defaults)
    CharacterStyle,
    StyleSheet,
)


# ──────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────

class PlaceholderType(str, Enum):
    """Standard placeholder types."""
    TITLE = "title"
    SUBTITLE = "subtitle"
    BODY = "body"
    PICTURE = "picture"
    CHART = "chart"
    TABLE = "table"
    MEDIA = "media"
    CLIP_ART = "clipArt"
    DIAGRAM = "diagram"
    OBJECT = "object"
    SLIDE_NUMBER = "slideNumber"
    HEADER = "header"
    FOOTER = "footer"
    DATE = "date"


class TransitionType(str, Enum):
    """Slide transition types."""
    FADE = "fade"
    PUSH = "push"
    WIPE = "wipe"
    SPLIT = "split"
    COVER = "cover"
    UNCOVER = "uncover"
    ZOOM = "zoom"
    RANDOM = "random"
    NO_TRANSITION = "none"


class AnimationType(str, Enum):
    """Entry/exit/emphasis animation types."""
    APPEAR = "appear"
    FADE_IN = "fadeIn"
    FLY_IN = "flyIn"
    ZOOM_IN = "zoomIn"
    SPIN = "spin"
    GROW = "grow"
    CUSTOM_PATH = "customPath"


class TriggerType(str, Enum):
    """What triggers an animation."""
    ON_CLICK = "onClick"
    AFTER_PREVIOUS = "afterPrevious"
    WITH_PREVIOUS = "withPrevious"


class ShowType(str, Enum):
    """Presentation show type."""
    DEFAULT = "default"
    KIOSK = "kiosk"
    SPEAKER = "speaker"


# ──────────────────────────────────────────────
# Placeholder & Layout / Master
# ──────────────────────────────────────────────

@dataclass
class Placeholder:
    """A placeholder shape on a slide layout."""
    idx: int
    type: PlaceholderType
    shape: ShapeContent   # position, size, geometry


@dataclass
class SlideLayout:
    """Definition of a slide layout (template)."""
    name: str
    master_name: Optional[str] = None
    placeholders: List[Placeholder] = field(default_factory=list)


@dataclass
class SlideMaster:
    """A slide master contains one or more layouts and a theme."""
    name: str
    layouts: Dict[str, SlideLayout] = field(default_factory=dict)  # layout name → layout
    default_text_style: Optional[CharacterStyle] = None
    background_color: Optional[str] = None          # hex colour
    background_image: Optional[ImageContent] = None


# ──────────────────────────────────────────────
# Transitions, Animations, Media
# ──────────────────────────────────────────────

@dataclass
class Transition:
    """Slide transition effect."""
    type: TransitionType = TransitionType.NO_TRANSITION
    duration_ms: float = 500.0               # milliseconds
    advance_after_ms: Optional[float] = None  # auto‑advance timer


@dataclass
class Animation:
    """An animation applied to a shape on a slide."""
    target_shape_id: str                     # reference to shape name/ID in the slide
    type: AnimationType
    duration_ms: float = 500.0
    delay_ms: float = 0.0
    trigger: TriggerType = TriggerType.ON_CLICK


@dataclass
class MediaReference:
    """Reference to an embedded audio/video file."""
    relationship_id: str
    media_type: str                          # "audio" or "video"
    mime_type: str                           # e.g. "audio/mp4"
    start_time: Optional[float] = None       # trim start in seconds
    end_time: Optional[float] = None         # trim end in seconds
    loop: bool = False


# ──────────────────────────────────────────────
# Notes & Comments
# ──────────────────────────────────────────────

@dataclass
class NotesSlide:
    """Speaker notes for a slide."""
    text: RichTextContent                     # can be rich text
    plain_text: str = ""                      # convenience plain text


@dataclass
class SlideComment:
    """A comment attached to a slide."""
    comment_id: str
    author: str
    date: Optional[str] = None                # ISO 8601 string
    text: str = ""
    position_x: Optional[float] = None
    position_y: Optional[float] = None


# ──────────────────────────────────────────────
# Slide (main container)
# ──────────────────────────────────────────────

@dataclass
class Slide:
    """A single presentation slide."""
    slide_id: str
    layout: Optional[SlideLayout] = None      # layout template applied
    background_color: Optional[str] = None    # solid fill
    background_image: Optional[ImageContent] = None

    # Content – each LogicalElement wraps one USDM content object
    # (ParagraphContent, ImageContent, ShapeContent, ChartContent, TableContent, etc.)
    elements: List[LogicalElement] = field(default_factory=list)

    transition: Transition = field(default_factory=Transition)
    animations: List[Animation] = field(default_factory=list)

    notes: Optional[NotesSlide] = None
    comments: List[SlideComment] = field(default_factory=list)

    # Embedded media (audio/video) – referenced by relationships
    media_references: List[MediaReference] = field(default_factory=list)

    # Additional metadata (no raw XML) – e.g., original slide name
    name: Optional[str] = None
    actions: List[HyperlinkAction] = field(default_factory=list)   # attached to the slide, or you can put it inside LogicalElement metadata


# ──────────────────────────────────────────────
# Presentation‑wide properties
# ──────────────────────────────────────────────

@dataclass
class PresentationProperties:
    """Global presentation settings."""
    slide_width: Optional[float] = None       # in EMU or points (choose one)
    slide_height: Optional[float] = None
    auto_advance: bool = False
    show_type: ShowType = ShowType.DEFAULT
    loop: bool = False
    start_with_narration: bool = False


# Add inside psdm_models.py (additional dataclasses)

@dataclass
class Theme:
    """Office theme colours and fonts."""
    name: Optional[str] = None
    color_scheme: Dict[str, str] = field(default_factory=dict)   # e.g. "dk1": "#000000"
    major_font: Optional[str] = None      # Latin font for headings
    minor_font: Optional[str] = None      # Latin font for body

@dataclass
class HyperlinkAction:
    """Hyperlink / mouse‑click action on an element."""
    target: str                           # URL, "slide:3", or "file:..."
    tooltip: Optional[str] = None
    show_and_return: bool = False

@dataclass
class GroupShapeContent:
    """A group of shapes (recursive)."""
    name: Optional[str] = None
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    rotation: int = 0
    children: List[Union[ShapeContent, GroupShapeContent]] = field(default_factory=list)

def _default_shape_content() -> ShapeContent:
    return ShapeContent()

@dataclass
class ConnectorContent:
    """A connector line between two shapes."""
    start_shape_id: str
    end_shape_id: str
    start_connection_site: Optional[int] = None
    end_connection_site: Optional[int] = None
    line_shape: ShapeContent = field(default_factory=_default_shape_content)   # visual appearance

@dataclass
class Section:
    """A named section in the presentation."""
    name: str
    first_slide_id: str                   # slide id of the first slide in the section

# ──────────────────────────────────────────────
# Top‑level PSDM Document
# ──────────────────────────────────────────────

@dataclass
class PSDMDocument(BaseDocument):
    """Complete presentation document model."""
    kind: DocumentStandard = DocumentStandard.PSDM
    slides: List[Slide] = field(default_factory=list)
    slide_masters: Dict[str, SlideMaster] = field(default_factory=dict)  # master name → master
    presentation_properties: PresentationProperties = field(default_factory=PresentationProperties)
    # Optionally a default style sheet for text
    stylesheet: StyleSheet = field(default_factory=StyleSheet)

    # Inherited from BaseDocument: title, document_id, media_type, raw_binary, etc.
    theme: Optional[Theme] = None
    sections: List[Section] = field(default_factory=list)
    
    
    