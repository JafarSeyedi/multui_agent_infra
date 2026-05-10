# engines/document/parsers/docx_parser/docx_models.py
"""
Intermediate models for DOCX parsing.
These models represent DOCX-specific structures extracted from the underlying XML.
They will be transformed into USDM models in the final step.
"""
from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from typing import Any
from typing import Literal

from ...models.usdm_models import ChartContent
from ...models.usdm_models import ShapeContent
from ..drawingml.diagram_parser import DiagramNode

# ============================================================
# ENUMS
# ============================================================

class DOCXElementType(str, Enum):
    """Types of elements found in a DOCX document."""
    PARAGRAPH = "paragraph"
    TABLE = "table"
    IMAGE = "image"
    MATH = "math"
    TEXT_BOX = "text_box"
    SHAPE = "shape"
    CHART = "chart"
    DIAGRAM = "diagram"
    COMMENT = "comment"
    FOOTNOTE = "footnote"
    ENDNOTE = "endnote"
    HEADER = "header"
    FOOTER = "footer"
    FIELD = "field"
    HYPERLINK = "hyperlink"
    BOOKMARK_START = "bookmark_start"
    BOOKMARK_END = "bookmark_end"
    SECTION_BREAK = "section_break"
    PAGE_BREAK = "page_break"
    COLUMN_BREAK = "column_break"
    EMBEDDED_OBJECT = "embedded_object"
    OLE_OBJECT = "ole_object"
    EQUATION = "equation"


class RunPropertyName(str, Enum):
    """Names of run-level properties."""
    BOLD = "bold"
    ITALIC = "italic"
    UNDERLINE = "underline"
    STRIKE = "strike"
    DOUBLE_STRIKE = "double_strike"
    SUPERSCRIPT = "superscript"
    SUBSCRIPT = "subscript"
    SMALL_CAPS = "small_caps"
    ALL_CAPS = "all_caps"
    HIGHLIGHT = "highlight"
    COLOR = "color"
    FONT_NAME = "font_name"
    FONT_SIZE = "font_size"
    FONT_SIZE_CS = "font_size_cs"  # complex script font size
    KERNING = "kerning"
    SPACING = "spacing"
    POSITION = "position"
    LANGUAGE = "language"
    NO_PROOF = "no_proof"
    WEB_HIDDEN = "web_hidden"
    SHADOW = "shadow"
    OUTLINE = "outline"
    EMBOSS = "emboss"
    IMPRINT = "imprint"
    VANISHED = "vanished"
    EAST_ASIAN_LAYOUT = "east_asian_layout"


class ParagraphAlignment(str, Enum):
    """Paragraph alignment values."""
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    BOTH = "both"  # justified
    DISTRIBUTE = "distribute"


class NumberingLevelSuffix(str, Enum):
    """Suffix type for numbering levels."""
    TAB = "tab"
    SPACE = "space"
    NOTHING = "nothing"


class SectionType(str, Enum):
    """Type of section break."""
    CONTINUOUS = "continuous"
    NEXT_PAGE = "next_page"
    EVEN_PAGE = "even_page"
    ODD_PAGE = "odd_page"


class VerticalAlignment(str, Enum):
    """Vertical alignment for table cells."""
    TOP = "top"
    CENTER = "center"
    BOTTOM = "bottom"


class TextDirection(str, Enum):
    """Text direction for runs and paragraphs."""
    LTR = "ltr"
    RTL = "rtl"


# ============================================================
# RUN-LEVEL MODELS (Character formatting)
# ============================================================

@dataclass
class DOCXRunProperties:
    """Properties applied to a run of text."""
    bold: bool | None = None
    italic: bool | None = None
    underline: str | None = None  # "single", "double", "dotted", "dash", etc.
    strike: bool | None = None
    double_strike: bool | None = None
    superscript: bool | None = None
    subscript: bool | None = None
    small_caps: bool | None = None
    all_caps: bool | None = None
    highlight: str | None = None  # color value (e.g., "yellow", "green")
    color: str | None = None  # hex or auto
    font_name: str | None = None
    font_size: float | None = None  # in half-points
    font_size_cs: float | None = None  # complex script size in half-points
    kerning: float | None = None
    spacing: float | None = None
    position: float | None = None
    language: str | None = None  # w:lang value
    no_proof: bool | None = None
    web_hidden: bool | None = None
    shadow: bool | None = None
    outline: bool | None = None
    emboss: bool | None = None
    imprint: bool | None = None
    vanished: bool | None = None

    # Raw XML for properties that don't map cleanly
    additional_properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class DOCXTextRun:
    """A single run of text with uniform formatting."""
    text: str
    properties: DOCXRunProperties = field(default_factory=DOCXRunProperties)

    # For fields, hyperlinks, etc.
    field_code: str | None = None
    field_result: str | None = None

    # Revision tracking
    is_insertion: bool = False
    is_deletion: bool = False
    revision_author: str | None = None
    revision_date: str | None = None
    revision_id: int | None = None

class DOCXDiagram:
    """Intermediate model for a Diagram (SmartArt)."""
    def __init__(self, name=None, description=None) -> None:
        self.name = name
        self.description = description
        self.texts: list[str] = []
        self.layout_type: str | None = None
        self.root: DiagramNode | None = None

@dataclass
class DOCXDrawing:
    """Inline drawing (image, shape, chart)."""
    relationship_id: str
    name: str | None = None
    description: str | None = None

    # Positioning
    width: float | None = None  # in EMUs
    height: float | None = None

    # Alternative text
    alt_text: str | None = None

    # For charts and diagrams
    drawing_type: Literal["image", "chart", "diagram", "shape"] = "image"
    # For charts – fully parsed, typed chart model
    chart: ChartContent | None = None
    shape: ShapeContent | None = None
    diagram: DOCXDiagram | None = None


@dataclass
class DOCXField:
    """A Word field (e.g., PAGE, DATE, HYPERLINK)."""
    field_type: str  # e.g., "PAGE", "DATE", "NUMPAGES", "REF", "HYPERLINK"
    instruction: str | None = None
    result: str | DOCXMath | Any | None = None
    is_locked: bool = False
    is_dirty: bool = False


@dataclass
class DOCXSymbol:
    """A special symbol or character."""
    char: str
    font: str | None = None


@dataclass
class DOCXBreak:
    """A line, page, or column break."""
    break_type: Literal["line", "page", "column", "text_wrapping"]
    clear: str | None = None  # Literal["none", "left", "right", "all"]


@dataclass
class DOCXTab:
    """A tab character."""
    pass  # Could be extended with alignment/leader properties


@dataclass
class DOCXRunContent:
    """Union type for all possible run-level content items."""
    items: list[DOCXTextRun | DOCXDrawing | DOCXField | DOCXSymbol | DOCXBreak | DOCXTab] = field(default_factory=list)


# ============================================================
# PARAGRAPH-LEVEL MODELS
# ============================================================

@dataclass
class DOCXParagraphProperties:
    """Properties applied to an entire paragraph."""
    style_id: str | None = None
    style_name: str | None = None

    # Alignment
    alignment: ParagraphAlignment | None = None

    # Indentation
    indent_left: float | None = None  # in DXA (twentieths of a point)
    indent_right: float | None = None
    indent_first_line: float | None = None
    indent_hanging: float | None = None

    # Spacing
    spacing_before: float | None = None  # in DXA
    spacing_after: float | None = None
    line_spacing: float | None = None
    line_spacing_rule: Literal["auto", "exact", "at_least"] | None = None

    # Pagination
    keep_lines_together: bool = False
    keep_with_next: bool = False
    page_break_before: bool = False
    widow_control: bool = True

    # Borders
    border_top: dict[str, Any] | None = None
    border_bottom: dict[str, Any] | None = None
    border_left: dict[str, Any] | None = None
    border_right: dict[str, Any] | None = None

    # Shading
    shading_fill: str | None = None
    shading_pattern: str | None = None

    # Outline level (for heading levels, 0-9)
    outline_level: int | None = None

    # Text direction
    text_direction: TextDirection = TextDirection.LTR

    # Numbering
    numbering_id: str | None = None
    numbering_level: int | None = None

    # Tabs
    tabs: list[dict[str, Any]] = field(default_factory=list)

    # Frame properties
    frame_properties: dict[str, Any] | None = None

    # Raw XML for unhandled properties
    additional_properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class DOCXParagraph:
    """A complete paragraph with runs and properties."""
    paragraph_id: str | None = None
    properties: DOCXParagraphProperties = field(default_factory=DOCXParagraphProperties)
    content: DOCXRunContent = field(default_factory=DOCXRunContent)

    # Revision tracking
    is_insertion: bool = False
    is_deletion: bool = False
    revision_author: str | None = None
    revision_date: str | None = None

    # For comments
    comment_reference: str | None = None


# ============================================================
# TABLE MODELS
# ============================================================

@dataclass
class DOCXTableCellProperties:
    """Properties of a table cell."""
    width: float | None = None  # in DXA
    vertical_alignment: VerticalAlignment = VerticalAlignment.TOP

    # Merging
    grid_span: int = 1  # column span
    vertical_span: int = 1  # row span (vMerge)
    is_vertically_merged: bool = False
    is_vertically_merged_restart: bool = False

    # Borders
    border_top: dict[str, Any] | None = None
    border_bottom: dict[str, Any] | None = None
    border_left: dict[str, Any] | None = None
    border_right: dict[str, Any] | None = None

    # Shading
    shading_fill: str | None = None

    # Margins
    margin_top: float | None = None
    margin_bottom: float | None = None
    margin_left: float | None = None
    margin_right: float | None = None

    # Text direction
    text_direction: TextDirection = TextDirection.LTR


@dataclass
class DOCXTableCell:
    """A single cell in a table."""
    properties: DOCXTableCellProperties = field(default_factory=DOCXTableCellProperties)
    content: list[DOCXParagraph | DOCXTable] = field(default_factory=list)


@dataclass
class DOCXTableRow:
    """A row in a table."""
    row_index: int
    cells: list[DOCXTableCell] = field(default_factory=list)
    is_header: bool = False
    height: float | None = None


@dataclass
class DOCXTableProperties:
    """Properties of a table."""
    style_id: str | None = None
    style_name: str | None = None

    # Positioning
    alignment: ParagraphAlignment | None = None
    indent_left: float | None = None

    # Borders
    border_top: dict[str, Any] | None = None
    border_bottom: dict[str, Any] | None = None
    border_left: dict[str, Any] | None = None
    border_right: dict[str, Any] | None = None
    border_inside_horizontal: dict[str, Any] | None = None
    border_inside_vertical: dict[str, Any] | None = None

    # Cell defaults
    cell_margin_default: dict[str, float] | None = None
    cell_spacing: float | None = None

    # Layout
    layout_type: Literal["fixed", "auto"] = "auto"
    width: float | None = None

    # Header row repeat
    header_row_repeat: bool = False


@dataclass
class DOCXTableGrid:
    """Grid column definitions for a table."""
    column_widths: list[float] = field(default_factory=list)  # in DXA


@dataclass
class DOCXTable:
    """A complete table."""
    properties: DOCXTableProperties = field(default_factory=DOCXTableProperties)
    grid: DOCXTableGrid = field(default_factory=DOCXTableGrid)
    rows: list[DOCXTableRow] = field(default_factory=list)


# ============================================================
# STYLE MODELS
# ============================================================

@dataclass
class DOCXStyleRunProperties:
    """Run properties defined in a style."""
    properties: DOCXRunProperties = field(default_factory=DOCXRunProperties)
    based_on: str | None = None
    next_style: str | None = None


@dataclass
class DOCXStyleParagraphProperties:
    """Paragraph properties defined in a style."""
    properties: DOCXParagraphProperties = field(default_factory=DOCXParagraphProperties)


@dataclass
class DOCXStyleTableProperties:
    """Table properties defined in a style."""
    properties: DOCXTableProperties = field(default_factory=DOCXTableProperties)


@dataclass
class DOCXStyle:
    """A named style definition."""
    style_id: str
    name: str
    style_type: Literal["paragraph", "character", "table", "numbering"]

    # Inheritance
    based_on: str | None = None
    next_style: str | None = None

    # Properties by type
    run_properties: DOCXStyleRunProperties | None = None
    paragraph_properties: DOCXStyleParagraphProperties | None = None
    table_properties: DOCXStyleTableProperties | None = None

    # UI properties
    is_default: bool = False
    is_custom: bool = False
    is_latent: bool = False
    priority: int | None = None

    # Linked style (for character styles linked to paragraph styles)
    linked_style_id: str | None = None


# ============================================================
# NUMBERING MODELS
# ============================================================

@dataclass
class DOCXNumberingLevel:
    """Definition for a single level in a numbering scheme."""
    level: int  # 0-8
    start: int = 1
    format: str = "decimal"  # "decimal", "lowerLetter", "upperLetter", "lowerRoman", "upperRoman", etc.
    text_template: str = "%1."  # e.g., "%1.", "(%1)", "%1)"
    alignment: ParagraphAlignment = ParagraphAlignment.LEFT
    suffix: NumberingLevelSuffix = NumberingLevelSuffix.TAB

    # Indentation
    indent_left: float | None = None
    indent_hanging: float | None = None

    # Font for the number
    font_name: str | None = None
    font_size: float | None = None
    bold: bool = False
    italic: bool = False


@dataclass
class DOCXNumberingDefinition:
    """A numbering definition (abstract numbering)."""
    abstract_id: str
    name: str | None = None
    levels: dict[int, DOCXNumberingLevel] = field(default_factory=dict)

    # Style link
    style_link: str | None = None

    # Multi-level type
    is_multi_level: bool = True


@dataclass
class DOCXNumberingInstance:
    """A concrete instance of a numbering definition."""
    instance_id: str
    abstract_definition_id: str | None = None
    levels_overrides: dict[int, DOCXNumberingLevel] = field(default_factory=dict)


# ============================================================
# HEADERS AND FOOTERS
# ============================================================

@dataclass
class DOCXHeaderFooter:
    """A header or footer definition."""
    header_footer_id: str
    header_footer_type: Literal["default", "first", "even"]
    content: list[DOCXParagraph | DOCXTable | DOCXSection] = field(default_factory=list)

    # References to images
    relationships: dict[str, str] = field(default_factory=dict)


# ============================================================
# SECTION MODELS
# ============================================================

@dataclass
class DOCXPageSize:
    """Page dimensions."""
    width: float  # in DXA
    height: float  # in DXA
    orientation: Literal["portrait", "landscape"] = "portrait"


@dataclass
class DOCXPageMargins:
    """Page margins."""
    top: float  # in DXA
    bottom: float
    left: float
    right: float
    header: float | None = None
    footer: float | None = None
    gutter: float | None = None


@dataclass
class DOCXColumns:
    """Column layout definition."""
    count: int = 1
    equal_width: bool = True
    widths: list[float] = field(default_factory=list)
    space_between: float | None = None
    separator: bool = False  # line between columns


@dataclass
class DOCXSection:
    """A document section with page layout properties."""
    section_id: str | None = None
    break_type: SectionType = SectionType.CONTINUOUS

    page_size: DOCXPageSize = field(default_factory=lambda: DOCXPageSize(width=12240, height=15840))
    margins: DOCXPageMargins = field(default_factory=lambda: DOCXPageMargins(top=1440, bottom=1440, left=1440, right=1440))
    columns: DOCXColumns = field(default_factory=DOCXColumns)

    # Header/footer references
    header_default_id: str | None = None
    header_first_id: str | None = None
    header_even_id: str | None = None
    footer_default_id: str | None = None
    footer_first_id: str | None = None
    footer_even_id: str | None = None

    # Page numbering
    page_number_start: int | None = None
    page_number_format: str | None = None

    # Line numbering
    line_numbering: dict[str, Any] | None = None


# ============================================================
# COMMENTS AND ANNOTATIONS
# ============================================================

@dataclass
class DOCXComment:
    """A comment attached to a document range."""
    comment_id: str
    author: str
    date: str
    initials: str | None = None
    content: list[DOCXParagraph] = field(default_factory=list)


@dataclass
class DOCXFootnoteEndnote:
    """A footnote or endnote."""
    note_id: str
    note_type: Literal["footnote", "endnote"]
    content: list[DOCXParagraph] = field(default_factory=list)


# ============================================================
# MATH MODELS
# ============================================================

@dataclass
class DOCXMathElement:
    """A math element (Office Math Markup Language - OMML)."""
    element_type: str  # e.g., "acc", "bar", "box", "d", "eqArr", "f", "func", "groupChr", "limLow", "limUpp", "m", "nary", "ph", "r", "rad", "sPre", "sSub", "sSubSup", "sSup"

    # For run elements (text)
    text: str | None = None
    text_properties: DOCXRunProperties | None = None

    # For fraction
    numerator: DOCXMathElement | None = None
    denominator: DOCXMathElement | None = None

    # For radicals
    degree: DOCXMathElement | None = None
    base: DOCXMathElement | None = None

    # For n-ary operators (sum, product, integral)
    sub: DOCXMathElement | None = None
    sup: DOCXMathElement | None = None

    # For matrices
    rows: list[list[DOCXMathElement]] = field(default_factory=list)

    # For general containers
    children: list[DOCXMathElement] = field(default_factory=list)

    # Properties
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class DOCXMath:
    """A complete math equation (display or inline)."""
    is_display: bool = True
    root: DOCXMathElement | None = None


# ============================================================
# DOCUMENT METADATA
# ============================================================

@dataclass
class DOCXCoreProperties:
    """Core document properties (Dublin Core)."""
    title: str | None = None
    subject: str | None = None
    creator: str | None = None
    keywords: list[str] = field(default_factory=list)
    description: str | None = None
    last_modified_by: str | None = None
    revision: int | None = None
    created: str | None = None  # ISO 8601
    modified: str | None = None  # ISO 8601
    category: str | None = None
    content_status: str | None = None


@dataclass
class DOCXExtendedProperties:
    """Extended document properties."""
    template: str | None = None
    manager: str | None = None
    company: str | None = None
    presentation_format: str | None = None
    pages: int | None = None
    words: int | None = None
    characters: int | None = None
    characters_with_spaces: int | None = None
    lines: int | None = None
    paragraphs: int | None = None
    total_time: int | None = None  # in minutes
    application: str | None = None
    app_version: str | None = None
    scale_crop: bool = False
    links_up_to_date: bool = False
    shared_doc: bool = False
    hyperlinks_changed: bool = False


@dataclass
class DOCXCustomProperties:
    """User-defined custom properties."""
    properties: dict[str, Any] = field(default_factory=dict)


# ============================================================
# MAIN INTERMEDIATE DOCUMENT
# ============================================================

@dataclass
class DOCXDocument:
    """Complete intermediate representation of a DOCX document."""

    # Metadata
    core_properties: DOCXCoreProperties = field(default_factory=DOCXCoreProperties)
    extended_properties: DOCXExtendedProperties = field(default_factory=DOCXExtendedProperties)
    custom_properties: DOCXCustomProperties = field(default_factory=DOCXCustomProperties)

    # Styles
    styles: dict[str, DOCXStyle] = field(default_factory=dict)
    default_paragraph_style_id: str | None = None
    default_character_style_id: str | None = None
    default_table_style_id: str | None = None

    # Numbering
    numbering_definitions: dict[str, DOCXNumberingDefinition] = field(default_factory=dict)
    numbering_instances: dict[str, DOCXNumberingInstance] = field(default_factory=dict)

    # Headers and footers
    headers: dict[str, DOCXHeaderFooter] = field(default_factory=dict)
    footers: dict[str, DOCXHeaderFooter] = field(default_factory=dict)

    # Comments and annotations
    comments: dict[str, DOCXComment] = field(default_factory=dict)
    footnotes: dict[str, DOCXFootnoteEndnote] = field(default_factory=dict)
    endnotes: dict[str, DOCXFootnoteEndnote] = field(default_factory=dict)

    # Document body
    body: list[DOCXParagraph | DOCXTable | DOCXSection] = field(default_factory=list)

    # Sections (in order of appearance)
    sections: list[DOCXSection] = field(default_factory=list)

    # Relationships (for images, hyperlinks, embedded objects)
    relationships: dict[str, dict[str, str]] = field(default_factory=dict)

    # Embedded binary data (by relationship ID)
    binary_parts: dict[str, bytes] = field(default_factory=dict)

    # Settings
    settings: dict[str, Any] = field(default_factory=dict)

    # Themes, fonts, etc.
    theme: dict[str, Any] | None = None
    font_table: dict[str, dict[str, Any]] = field(default_factory=dict)

    # Web settings
    web_settings: dict[str, Any] = field(default_factory=dict)
