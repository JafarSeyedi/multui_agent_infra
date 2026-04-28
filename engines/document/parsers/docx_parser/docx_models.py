# engines/document/parsers/docx_parser/docx_models.py
"""
Intermediate models for DOCX parsing.
These models represent DOCX-specific structures extracted from the underlying XML.
They will be transformed into USDM models in the final step.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Literal, Union
from enum import Enum
from ...models.usdm_models import ChartContent, ShapeContent, ChartContent 

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
    bold: Optional[bool] = None
    italic: Optional[bool] = None
    underline: Optional[str] = None  # "single", "double", "dotted", "dash", etc.
    strike: Optional[bool] = None
    double_strike: Optional[bool] = None
    superscript: Optional[bool] = None
    subscript: Optional[bool] = None
    small_caps: Optional[bool] = None
    all_caps: Optional[bool] = None
    highlight: Optional[str] = None  # color value (e.g., "yellow", "green")
    color: Optional[str] = None  # hex or auto
    font_name: Optional[str] = None
    font_size: Optional[float] = None  # in half-points
    font_size_cs: Optional[float] = None  # complex script size in half-points
    kerning: Optional[float] = None
    spacing: Optional[float] = None
    position: Optional[float] = None
    language: Optional[str] = None  # w:lang value
    no_proof: Optional[bool] = None
    web_hidden: Optional[bool] = None
    shadow: Optional[bool] = None
    outline: Optional[bool] = None
    emboss: Optional[bool] = None
    imprint: Optional[bool] = None
    vanished: Optional[bool] = None

    # Raw XML for properties that don't map cleanly
    additional_properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DOCXTextRun:
    """A single run of text with uniform formatting."""
    text: str
    properties: DOCXRunProperties = field(default_factory=DOCXRunProperties)
    
    # For fields, hyperlinks, etc.
    field_code: Optional[str] = None
    field_result: Optional[str] = None
    
    # Revision tracking
    is_insertion: bool = False
    is_deletion: bool = False
    revision_author: Optional[str] = None
    revision_date: Optional[str] = None
    revision_id: Optional[int] = None

@dataclass
class DOCXDiagram:
    """Intermediate model for a Diagram (SmartArt)."""
    name: Optional[str] = None
    description: Optional[str] = None
    # Flat list of all text runs found in the diagram
    texts: List[str] = field(default_factory=list)
    # Hierarchical structure could be added later (list of nodes)
    # For now, a list of text lines is sufficient.

@dataclass
class DOCXDrawing:
    """Inline drawing (image, shape, chart)."""
    relationship_id: str
    name: Optional[str] = None
    description: Optional[str] = None
        
    # Positioning
    width: Optional[float] = None  # in EMUs
    height: Optional[float] = None
    
    # Alternative text
    alt_text: Optional[str] = None
    
    # For charts and diagrams
    drawing_type: Literal["image", "chart", "diagram", "shape"] = "image"
    # For charts – fully parsed, typed chart model
    chart: Optional[ChartContent] = None   
    shape: Optional[ShapeContent] = None
    diagram: Optional[DOCXDiagram] = None
    
    
@dataclass
class DOCXField:
    """A Word field (e.g., PAGE, DATE, HYPERLINK)."""
    field_type: str  # e.g., "PAGE", "DATE", "NUMPAGES", "REF", "HYPERLINK"
    instruction: Optional[str] = None
    result: Optional[Union[str, 'DOCXMath', Any]] = None
    is_locked: bool = False
    is_dirty: bool = False


@dataclass
class DOCXSymbol:
    """A special symbol or character."""
    char: str
    font: Optional[str] = None


@dataclass
class DOCXBreak:
    """A line, page, or column break."""
    break_type: Literal["line", "page", "column", "text_wrapping"]
    clear: Optional[str] = None  # Literal["none", "left", "right", "all"]


@dataclass
class DOCXTab:
    """A tab character."""
    pass  # Could be extended with alignment/leader properties


@dataclass
class DOCXRunContent:
    """Union type for all possible run-level content items."""
    items: List[Union[DOCXTextRun, DOCXDrawing, DOCXField, DOCXSymbol, DOCXBreak, DOCXTab]] = field(default_factory=list)


# ============================================================
# PARAGRAPH-LEVEL MODELS
# ============================================================

@dataclass
class DOCXParagraphProperties:
    """Properties applied to an entire paragraph."""
    style_id: Optional[str] = None
    style_name: Optional[str] = None
    
    # Alignment
    alignment: Optional[ParagraphAlignment] = None
    
    # Indentation
    indent_left: Optional[float] = None  # in DXA (twentieths of a point)
    indent_right: Optional[float] = None
    indent_first_line: Optional[float] = None
    indent_hanging: Optional[float] = None
    
    # Spacing
    spacing_before: Optional[float] = None  # in DXA
    spacing_after: Optional[float] = None
    line_spacing: Optional[float] = None
    line_spacing_rule: Optional[Literal["auto", "exact", "at_least"]] = None
    
    # Pagination
    keep_lines_together: bool = False
    keep_with_next: bool = False
    page_break_before: bool = False
    widow_control: bool = True
    
    # Borders
    border_top: Optional[Dict[str, Any]] = None
    border_bottom: Optional[Dict[str, Any]] = None
    border_left: Optional[Dict[str, Any]] = None
    border_right: Optional[Dict[str, Any]] = None
    
    # Shading
    shading_fill: Optional[str] = None
    shading_pattern: Optional[str] = None
    
    # Outline level (for heading levels, 0-9)
    outline_level: Optional[int] = None
    
    # Text direction
    text_direction: TextDirection = TextDirection.LTR
    
    # Numbering
    numbering_id: Optional[str] = None
    numbering_level: Optional[int] = None
    
    # Tabs
    tabs: List[Dict[str, Any]] = field(default_factory=list)
    
    # Frame properties
    frame_properties: Optional[Dict[str, Any]] = None
    
    # Raw XML for unhandled properties
    additional_properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DOCXParagraph:
    """A complete paragraph with runs and properties."""
    paragraph_id: Optional[str] = None
    properties: DOCXParagraphProperties = field(default_factory=DOCXParagraphProperties)
    content: DOCXRunContent = field(default_factory=DOCXRunContent)
    
    # Revision tracking
    is_insertion: bool = False
    is_deletion: bool = False
    revision_author: Optional[str] = None
    revision_date: Optional[str] = None
    
    # For comments
    comment_reference: Optional[str] = None


# ============================================================
# TABLE MODELS
# ============================================================

@dataclass
class DOCXTableCellProperties:
    """Properties of a table cell."""
    width: Optional[float] = None  # in DXA
    vertical_alignment: VerticalAlignment = VerticalAlignment.TOP
    
    # Merging
    grid_span: int = 1  # column span
    vertical_span: int = 1  # row span (vMerge)
    is_vertically_merged: bool = False
    is_vertically_merged_restart: bool = False
    
    # Borders
    border_top: Optional[Dict[str, Any]] = None
    border_bottom: Optional[Dict[str, Any]] = None
    border_left: Optional[Dict[str, Any]] = None
    border_right: Optional[Dict[str, Any]] = None
    
    # Shading
    shading_fill: Optional[str] = None
    
    # Margins
    margin_top: Optional[float] = None
    margin_bottom: Optional[float] = None
    margin_left: Optional[float] = None
    margin_right: Optional[float] = None
    
    # Text direction
    text_direction: TextDirection = TextDirection.LTR


@dataclass
class DOCXTableCell:
    """A single cell in a table."""
    properties: DOCXTableCellProperties = field(default_factory=DOCXTableCellProperties)
    content: List[Union[DOCXParagraph, 'DOCXTable']] = field(default_factory=list)


@dataclass
class DOCXTableRow:
    """A row in a table."""
    row_index: int
    cells: List[DOCXTableCell] = field(default_factory=list)
    is_header: bool = False
    height: Optional[float] = None


@dataclass
class DOCXTableProperties:
    """Properties of a table."""
    style_id: Optional[str] = None
    style_name: Optional[str] = None
    
    # Positioning
    alignment: Optional[ParagraphAlignment] = None
    indent_left: Optional[float] = None
    
    # Borders
    border_top: Optional[Dict[str, Any]] = None
    border_bottom: Optional[Dict[str, Any]] = None
    border_left: Optional[Dict[str, Any]] = None
    border_right: Optional[Dict[str, Any]] = None
    border_inside_horizontal: Optional[Dict[str, Any]] = None
    border_inside_vertical: Optional[Dict[str, Any]] = None
    
    # Cell defaults
    cell_margin_default: Optional[Dict[str, float]] = None
    cell_spacing: Optional[float] = None
    
    # Layout
    layout_type: Literal["fixed", "auto"] = "auto"
    width: Optional[float] = None
    
    # Header row repeat
    header_row_repeat: bool = False


@dataclass
class DOCXTableGrid:
    """Grid column definitions for a table."""
    column_widths: List[float] = field(default_factory=list)  # in DXA


@dataclass
class DOCXTable:
    """A complete table."""
    properties: DOCXTableProperties = field(default_factory=DOCXTableProperties)
    grid: DOCXTableGrid = field(default_factory=DOCXTableGrid)
    rows: List[DOCXTableRow] = field(default_factory=list)


# ============================================================
# STYLE MODELS
# ============================================================

@dataclass
class DOCXStyleRunProperties:
    """Run properties defined in a style."""
    properties: DOCXRunProperties = field(default_factory=DOCXRunProperties)
    based_on: Optional[str] = None
    next_style: Optional[str] = None


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
    based_on: Optional[str] = None
    next_style: Optional[str] = None
    
    # Properties by type
    run_properties: Optional[DOCXStyleRunProperties] = None
    paragraph_properties: Optional[DOCXStyleParagraphProperties] = None
    table_properties: Optional[DOCXStyleTableProperties] = None
    
    # UI properties
    is_default: bool = False
    is_custom: bool = False
    is_latent: bool = False
    priority: Optional[int] = None
    
    # Linked style (for character styles linked to paragraph styles)
    linked_style_id: Optional[str] = None


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
    indent_left: Optional[float] = None
    indent_hanging: Optional[float] = None
    
    # Font for the number
    font_name: Optional[str] = None
    font_size: Optional[float] = None
    bold: bool = False
    italic: bool = False


@dataclass
class DOCXNumberingDefinition:
    """A numbering definition (abstract numbering)."""
    abstract_id: str
    name: Optional[str] = None
    levels: Dict[int, DOCXNumberingLevel] = field(default_factory=dict)
    
    # Style link
    style_link: Optional[str] = None
    
    # Multi-level type
    is_multi_level: bool = True


@dataclass
class DOCXNumberingInstance:
    """A concrete instance of a numbering definition."""
    instance_id: str
    abstract_definition_id: Optional[str] = None
    levels_overrides: Dict[int, DOCXNumberingLevel] = field(default_factory=dict)


# ============================================================
# HEADERS AND FOOTERS
# ============================================================

@dataclass
class DOCXHeaderFooter:
    """A header or footer definition."""
    header_footer_id: str
    header_footer_type: Literal["default", "first", "even"]
    content: List[Union[DOCXParagraph, DOCXTable, DOCXSection]] = field(default_factory=list)
    
    # References to images
    relationships: Dict[str, str] = field(default_factory=dict)


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
    header: Optional[float] = None
    footer: Optional[float] = None
    gutter: Optional[float] = None


@dataclass
class DOCXColumns:
    """Column layout definition."""
    count: int = 1
    equal_width: bool = True
    widths: List[float] = field(default_factory=list)
    space_between: Optional[float] = None
    separator: bool = False  # line between columns


@dataclass
class DOCXSection:
    """A document section with page layout properties."""
    section_id: Optional[str] = None
    break_type: SectionType = SectionType.CONTINUOUS
    
    page_size: DOCXPageSize = field(default_factory=lambda: DOCXPageSize(width=12240, height=15840))
    margins: DOCXPageMargins = field(default_factory=lambda: DOCXPageMargins(top=1440, bottom=1440, left=1440, right=1440))
    columns: DOCXColumns = field(default_factory=DOCXColumns)
    
    # Header/footer references
    header_default_id: Optional[str] = None
    header_first_id: Optional[str] = None
    header_even_id: Optional[str] = None
    footer_default_id: Optional[str] = None
    footer_first_id: Optional[str] = None
    footer_even_id: Optional[str] = None
    
    # Page numbering
    page_number_start: Optional[int] = None
    page_number_format: Optional[str] = None
    
    # Line numbering
    line_numbering: Optional[Dict[str, Any]] = None


# ============================================================
# COMMENTS AND ANNOTATIONS
# ============================================================

@dataclass
class DOCXComment:
    """A comment attached to a document range."""
    comment_id: str
    author: str
    date: str
    initials: Optional[str] = None
    content: List[DOCXParagraph] = field(default_factory=list)


@dataclass
class DOCXFootnoteEndnote:
    """A footnote or endnote."""
    note_id: str
    note_type: Literal["footnote", "endnote"]
    content: List[DOCXParagraph] = field(default_factory=list)


# ============================================================
# MATH MODELS
# ============================================================

@dataclass
class DOCXMathElement:
    """A math element (Office Math Markup Language - OMML)."""
    element_type: str  # e.g., "acc", "bar", "box", "d", "eqArr", "f", "func", "groupChr", "limLow", "limUpp", "m", "nary", "ph", "r", "rad", "sPre", "sSub", "sSubSup", "sSup"
    
    # For run elements (text)
    text: Optional[str] = None
    text_properties: Optional[DOCXRunProperties] = None
    
    # For fraction
    numerator: Optional[DOCXMathElement] = None
    denominator: Optional[DOCXMathElement] = None
    
    # For radicals
    degree: Optional[DOCXMathElement] = None
    base: Optional[DOCXMathElement] = None
    
    # For n-ary operators (sum, product, integral)
    sub: Optional[DOCXMathElement] = None
    sup: Optional[DOCXMathElement] = None
    
    # For matrices
    rows: List[List[DOCXMathElement]] = field(default_factory=list)
    
    # For general containers
    children: List[DOCXMathElement] = field(default_factory=list)
    
    # Properties
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DOCXMath:
    """A complete math equation (display or inline)."""
    is_display: bool = True
    root: Optional[DOCXMathElement] = None


# ============================================================
# DOCUMENT METADATA
# ============================================================

@dataclass
class DOCXCoreProperties:
    """Core document properties (Dublin Core)."""
    title: Optional[str] = None
    subject: Optional[str] = None
    creator: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    description: Optional[str] = None
    last_modified_by: Optional[str] = None
    revision: Optional[int] = None
    created: Optional[str] = None  # ISO 8601
    modified: Optional[str] = None  # ISO 8601
    category: Optional[str] = None
    content_status: Optional[str] = None


@dataclass
class DOCXExtendedProperties:
    """Extended document properties."""
    template: Optional[str] = None
    manager: Optional[str] = None
    company: Optional[str] = None
    presentation_format: Optional[str] = None
    pages: Optional[int] = None
    words: Optional[int] = None
    characters: Optional[int] = None
    characters_with_spaces: Optional[int] = None
    lines: Optional[int] = None
    paragraphs: Optional[int] = None
    total_time: Optional[int] = None  # in minutes
    application: Optional[str] = None
    app_version: Optional[str] = None
    scale_crop: bool = False
    links_up_to_date: bool = False
    shared_doc: bool = False
    hyperlinks_changed: bool = False


@dataclass
class DOCXCustomProperties:
    """User-defined custom properties."""
    properties: Dict[str, Any] = field(default_factory=dict)


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
    styles: Dict[str, DOCXStyle] = field(default_factory=dict)
    default_paragraph_style_id: Optional[str] = None
    default_character_style_id: Optional[str] = None
    default_table_style_id: Optional[str] = None
    
    # Numbering
    numbering_definitions: Dict[str, DOCXNumberingDefinition] = field(default_factory=dict)
    numbering_instances: Dict[str, DOCXNumberingInstance] = field(default_factory=dict)
    
    # Headers and footers
    headers: Dict[str, DOCXHeaderFooter] = field(default_factory=dict)
    footers: Dict[str, DOCXHeaderFooter] = field(default_factory=dict)
    
    # Comments and annotations
    comments: Dict[str, DOCXComment] = field(default_factory=dict)
    footnotes: Dict[str, DOCXFootnoteEndnote] = field(default_factory=dict)
    endnotes: Dict[str, DOCXFootnoteEndnote] = field(default_factory=dict)
    
    # Document body
    body: List[Union[DOCXParagraph, DOCXTable, DOCXSection]] = field(default_factory=list)
    
    # Sections (in order of appearance)
    sections: List[DOCXSection] = field(default_factory=list)
    
    # Relationships (for images, hyperlinks, embedded objects)
    relationships: Dict[str, Dict[str, str]] = field(default_factory=dict)
    
    # Embedded binary data (by relationship ID)
    binary_parts: Dict[str, bytes] = field(default_factory=dict)
    
    # Settings
    settings: Dict[str, Any] = field(default_factory=dict)
    
    # Themes, fonts, etc.
    theme: Optional[Dict[str, Any]] = None
    font_table: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Web settings
    web_settings: Dict[str, Any] = field(default_factory=dict)