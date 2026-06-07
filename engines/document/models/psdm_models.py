# engines/document/models/psdm_models.py
"""
PSDM (Presentation Structured Document Model)
===============================================
Domain model for presentations (e.g., PPTX).
Extends BaseDocument and reuses USDM content types.
"""
from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from typing import Any

from .base import BaseDocument
from .media_types import MediaType
from .media_types import DocumentStandard
from .usdm_models import CharacterStyle
from .usdm_models import ImageContent
from .usdm_models import LogicalElement
from .usdm_models import RichTextContent
from .usdm_models import ShapeContent
from .usdm_models import StyleSheet


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
    master_name: str | None = None
    placeholders: list[Placeholder] = field(default_factory=list)
    _meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class SlideMaster:
    """A slide master contains one or more layouts and a theme."""
    name: str
    layouts: dict[str, SlideLayout] = field(default_factory=dict)  # layout name → layout
    default_text_style: CharacterStyle | None = None
    background_color: str | None = None          # hex colour
    background_image: ImageContent | None = None
    _meta: dict[str, Any] = field(default_factory=dict)

# ──────────────────────────────────────────────
# Transitions, Animations, Media
# ──────────────────────────────────────────────

@dataclass
class PresentationTransition:
    """Slide transition effect."""
    type: TransitionType = TransitionType.NO_TRANSITION
    duration_ms: float = 500.0               # milliseconds
    advance_after_ms: float | None = None  # auto‑advance timer


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
    start_time: float | None = None       # trim start in seconds
    end_time: float | None = None         # trim end in seconds
    loop: bool = False
    _meta: dict[str, Any] = field(default_factory=dict)


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
    date: str | None = None                # ISO 8601 string
    text: str = ""
    position_x: float | None = None
    position_y: float | None = None


# ──────────────────────────────────────────────
# Slide (main container)
# ──────────────────────────────────────────────

@dataclass
class Slide:
    """A single presentation slide."""
    slide_id: str
    layout: SlideLayout | None = None      # layout template applied
    background_color: str | None = None    # solid fill
    background_image: ImageContent | None = None

    # Content – each LogicalElement wraps one USDM content object
    # (ParagraphContent, ImageContent, ShapeContent, ChartContent, TableContent, etc.)
    elements: list[LogicalElement] = field(default_factory=list)

    transition: PresentationTransition = field(default_factory=PresentationTransition)
    animations: list[Animation] = field(default_factory=list)

    notes: NotesSlide | None = None
    comments: list[SlideComment] = field(default_factory=list)

    # Embedded media (audio/video) – referenced by relationships
    media_references: list[MediaReference] = field(default_factory=list)

    # Additional metadata (no raw XML) – e.g., original slide name
    name: str | None = None
    actions: list[HyperlinkAction] = field(default_factory=list)   # attached to the slide, or you can put it inside LogicalElement metadata
    _meta: dict[str, Any] = field(default_factory=dict)

# ──────────────────────────────────────────────
# Presentation‑wide properties
# ──────────────────────────────────────────────

@dataclass
class PresentationProperties:
    """Global presentation settings."""
    slide_width: float | None = None       # in EMU or points (choose one)
    slide_height: float | None = None
    auto_advance: bool = False
    show_type: ShowType = ShowType.DEFAULT
    loop: bool = False
    start_with_narration: bool = False
    paper_size: str | None = None
    paper_width: str | None = None
    paper_height: str | None = None
    scale: str | None = None
    orientation: str | None = None
    paper_source: str | None = None
    first_slide_number: int | None = None
    _meta: dict[str, Any] = field(default_factory=dict)

# Add inside psdm_models.py (additional dataclasses)

@dataclass
class Theme:
    """Office theme colours and fonts."""
    name: str | None = None
    color_scheme: dict[str, str] = field(default_factory=dict)   # e.g. "dk1": "#000000"
    major_font: str | None = None      # Latin font for headings
    minor_font: str | None = None      # Latin font for body
    _meta: dict[str, Any] = field(default_factory=dict)
    
@dataclass
class HyperlinkAction:
    """Hyperlink / mouse‑click action on an element."""
    target: str                           # URL, "slide:3", or "file:..."
    tooltip: str | None = None
    show_and_return: bool = False

@dataclass
class GroupShapeContent:
    """A group of shapes (recursive)."""
    name: str | None = None
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    rotation: int = 0
    children: list[ShapeContent | GroupShapeContent] = field(default_factory=list)

def _default_shape_content() -> ShapeContent:
    return ShapeContent(shape_type="line")

@dataclass
class ConnectorContent:
    """A connector line between two shapes."""
    start_shape_id: str
    end_shape_id: str
    start_connection_site: int | None = None
    end_connection_site: int | None = None
    line_shape: ShapeContent = field(default_factory=_default_shape_content)   # visual appearance

@dataclass
class PresentationSection:
    """A named section in the presentation."""
    name: str
    first_slide_id: str                   # slide id of the first slide in the section
    _meta: dict[str, Any] = field(default_factory=dict)
    
@dataclass
class CustomShow:
    """A custom show definition."""
    name: str = ""
    slide_ids: list[str] = field(default_factory=list)


@dataclass
class CustomShowList:
    """Collection of custom shows."""
    shows: list[CustomShow] = field(default_factory=list)


CustomShowCollection = CustomShowList


@dataclass
class HandoutMaster:
    """Handout master definition."""
    name: str = ""
    background_color: str | None = None
    background_image: ImageContent | None = None
    default_text_style: CharacterStyle | None = None
    _meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class NotesMaster:
    """Notes master definition."""
    name: str = ""
    background_color: str | None = None
    background_image: ImageContent | None = None
    default_text_style: CharacterStyle | None = None
    _meta: dict[str, Any] = field(default_factory=dict)


# ──────────────────────────────────────────────
# Top‑level PSDM Document
# ──────────────────────────────────────────────

@dataclass
class PSDMDocument(BaseDocument):
    """Complete presentation document model."""
    title: str = ""
    document_id: str = ""
    media_type: MediaType | None = None
    kind: DocumentStandard = DocumentStandard.PSDM
    slides: list[Slide] = field(default_factory=list)
    slide_masters: dict[str, SlideMaster] = field(default_factory=dict)
    presentation_properties: PresentationProperties = field(default_factory=PresentationProperties)
    stylesheet: StyleSheet = field(default_factory=StyleSheet)
    theme: Theme | None = None
    sections: list[PresentationSection] = field(default_factory=list)
    handout_master: HandoutMaster | None = None
    notes_master: NotesMaster | None = None
    custom_shows: CustomShowList | None = None
    psdm_meta: dict[str, Any] = field(default_factory=dict)
    file_extension: str | None = None

    @property
    def _meta(self) -> dict[str, Any]:
        return self.psdm_meta