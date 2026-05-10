# engines/document/models/usdm_models.py
from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from typing import Any
from typing import Literal
from typing import Union

from .base import BaseDocument
from .base import ElementType
from .media_types import DocumentStandard

class USDMDocument(BaseDocument):
    kind: DocumentStandard = DocumentStandard.USDM
    sections: list[Section] = field(default_factory=list)
    pages: list[Page] = field(default_factory=list)
# elements: لایه‌ی منطقی (Logical tree) → محتوای واقعی سند
# sections: لایه‌ی سازمانی/سرفصلی → ساختار معنایی سند
# pages: لایه‌ی فیزیکی/صفحه‌بندی → خروجی صفحه‌بندی شده (PDF-like)
    elements: list[DocumentElement] = field(default_factory=list)
    logical_elements: list[LogicalElement] = field(default_factory=list)
    stylesheet: StyleSheet = field(default_factory=StyleSheet)


@dataclass
class DocumentElement:
    element_id: str
    element_type: ElementType
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class Section:
    section_id: str = ""
    title: HeadingContent | None = None
    elements: list[DocumentElement] = field(default_factory=list)
    section_type: str | None = None  # e.g. "body", "header", "footer"
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class PageContent:
    number: int | None = None
    elements: list[DocumentElement] = field(default_factory=list)
    page_width: float | None = None
    page_height: float | None = None
    margin_top: float | None = None
    margin_bottom: float | None = None
    margin_left: float | None = None
    margin_right: float | None = None


@dataclass
class LogicalElement:
    element_id: str
    element_type: ElementType
    content: Any
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def _meta(self) -> dict[str, Any]:
        return self.metadata


# ============================================================
# RICH TEXT
# ============================================================

@dataclass
class RichTextSpan:
    text: str = ""
    character_style: str | None = None  # key into StyleSheet.character_styles
    code: bool = False
    background: str | None = None
    href: str | None = None
    math: str | None = None  # inline math
    display_math: bool = False

    # New fields for inline formatting (Excel rich text)
    bold: bool = False
    italic: bool = False
    underline: bool = False
    color: str | None = None      # e.g. "#FF0000"
    font: str | None = None       # font name
    
@dataclass
class RichTextContent:
    spans: list[RichTextSpan] = field(default_factory=list)


# ============================================================
# LOGICAL CONTENT TYPES
# ============================================================

@dataclass
class ParagraphContent:
    text: RichTextContent
    style: str | None = None


@dataclass
class HeadingContent:
    level: int
    text: RichTextContent


@dataclass
class MathContent:
    latex: str
    display: bool = True


@dataclass
class CodeContent:
    code: str
    language: str | None = None


@dataclass
class ImageContent:
    src: str
    width: float | None = None
    height: float | None = None
    alt: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ListItemContent:
    elements: list[LogicalElement]


@dataclass
class ListContent:
    ordered: bool
    items: list[ListItemContent]


# TABLES
@dataclass
class TableCell:
    content: list[LogicalElement]
    row_span: int = 1
    col_span: int = 1
    is_header: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TableRow:
    cells: list[TableCell] = []
    is_header: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TableContent:
    rows: list[TableRow]
    grid: list[int] | None = None     # Word-style table grid definition
    caption: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class QuoteContent:
    elements: list[LogicalElement]


@dataclass
class BinaryContent:
    data: bytes


# ============================================================
# LEVEL 2 — PAGE & LAYOUT (PDF-LIKE)
# ============================================================

@dataclass
class TextRun:
    text: str
    x: float
    y: float
    font: str
    size: float
    color: str | None = None
    style_id: str | None = None
    bbox: dict[str, float] | None = None
    language: str | None = None

@dataclass
class ImageObject:
    src: str
    x: float
    y: float
    width: float
    height: float
    format: str = 'jpg'
    bbox: dict[str, float] | None = None

@dataclass
class VectorPath:
    commands: list[str]
    stroke_color: str | None = None
    fill_color: str | None = None
    stroke_width: float | None = None
    points: list[dict[str, float]] | None = None


@dataclass
class AnnotationObject:
    x: float
    y: float
    width: float
    height: float
    subtype: str
    contents: str | None = None


@dataclass
class Page:
    page_number: int
    width: float
    height: float
    elements: list[TextRun | ImageObject | VectorPath | AnnotationObject] = field(default_factory=list)



# ============================================================
# LEVEL 3 — STYLES
# ============================================================

@dataclass
class CharacterStyle:
    name: str
    bold: bool | None = None
    italic: bool | None = None
    underline: bool | None = None
    underline_type: str | None = None
    color: str | None = None
    highlight: str | None = None
    background: str | None = None
    font: str | None = None
    font_family: str | None = None
    font_charset: str | None = None
    font_pitch: str | None = None
    size: float | None = None
    size_cs: float | None = None
    strike: bool | None = None
    double_strike: bool | None = None
    superscript: bool | None = None
    subscript: bool | None = None
    small_caps: bool | None = None
    all_caps: bool | None = None
    kerning: float | None = None
    spacing: float | None = None
    position: float | None = None
    shadow: bool | None = None
    outline: bool | None = None
    emboss: bool | None = None
    imprint: bool | None = None
    vanished: bool | None = None
    web_hidden: bool | None = None
    language: str | None = None
    no_proof: bool | None = None
    style_id: str | None = None
    based_on: str | None = None
    next_style: str | None = None
    linked_style: str | None = None
    _meta: dict[str, Any] = field(default_factory=dict)
    
@dataclass
class ParagraphStyle:
    name: str
    alignment: str | None = None  # "left", "right", "center", "justify"
    spacing_before: float | None = None
    spacing_after: float | None = None
    line_spacing: float | None = None
    indent_left: float | None = None
    indent_right: float | None = None
    first_line_indent: float | None = None

    line_spacing_rule: str | None = None
    indent_hanging: float | None = None
    keep_lines_together: bool | None = None
    keep_with_next: bool | None = None
    page_break_before: bool | None = None
    widow_control: bool | None = None
    borders: dict[str, Any] | None = None
    shading: dict[str, Any] | None = None
    outline_level: int | None = None
    text_direction: str | None = None   # "ltr", "rtl", etc.
    tabs: list[dict[str, Any]] | None = None
    frame_properties: dict[str, Any] | None = None
    style_id: str | None = None
    based_on: str | None = None
    next_style: str | None = None

@dataclass
class TableStyle:
    name: str
    border_color: str | None = None
    border_width: float | None = None
    cell_spacing: float | None = None
    header_row: bool | None = None
    banded_rows: bool | None = None
    banded_columns: bool | None = None

    alignment: str | None = None               # "left", "center", "right"
    indent_left: float | None = None
    width: float | None = None
    layout_type: str | None = None             # "fixed", "auto"
    borders: dict[str, Any] | None = None
    cell_margins: dict[str, float] | None = None
    shading: dict[str, Any] | None = None
    first_row: bool | None = None              # special formatting for first row
    last_row: bool | None = None
    first_column: bool | None = None
    last_column: bool | None = None
    style_id: str | None = None
    based_on: str | None = None

@dataclass
class ListStyle:
    name: str
    level_styles: dict[int, dict[str, Any]] = field(default_factory=dict)

@dataclass
class StyleSheet:
    character_styles: dict[str, CharacterStyle] = field(default_factory=dict)
    paragraph_styles: dict[str, ParagraphStyle] = field(default_factory=dict)
    table_styles: dict[str, TableStyle] = field(default_factory=dict)
    list_styles: dict[str, ListStyle] = field(default_factory=dict)



















@dataclass
class FormulaContent:
    latex: str
    display: bool = True

@dataclass
class LinkContent:
    url: str
    text: RichTextContent


@dataclass
class CommentContent:
    """Content for comment."""
    comment_id: str
    author: str
    date: str | None = None
    text: str = ""
    elements: list[LogicalElement] = field(default_factory=list)
    parent_id: str | None = None
    resolved: bool = False

@dataclass
class PageBreakContent:
    pass

@dataclass
class LineBreakContent:
    pass

@dataclass
class ColumnBreakContent:
    pass

# PDF layout models
@dataclass
class PDFTextRun:
    text: str
    x: float
    y: float
    font: str | None
    size: float | None

@dataclass
class PDFVectorPath:
    commands: list[str]
    stroke_color: str | None = None
    fill_color: str | None = None

@dataclass
class LaTeXEnvironmentContent:
    """محیط‌های LaTeX مانند theorem, proof, figure"""
    environment_type: str  # "theorem", "lemma", "figure", "table"
    label: str | None
    caption: str | None
    parameters: dict[str, str] = field(default_factory=dict)
    content: list[LogicalContent] = field(default_factory=list)

@dataclass
class LaTeXCommandContent:
    """دستورات LaTeX مانند \\section{}, \\cite{}"""
    command: str
    arguments: list[str] = field(default_factory=list)
    options: dict[str, str] = field(default_factory=dict)

@dataclass
class SemanticHTMLContent:
    """عناصر معنایی HTML5"""
    element_type: Literal["article", "section", "nav", "aside", "header", "footer"]
    role: str | None  # برای ARIA roles
    aria_attributes: dict[str, str] = field(default_factory=dict)

@dataclass
class CanvasOperation:
    """Placeholder for canvas operations."""

@dataclass
class PDFInfo:
    """Placeholder for PDF metadata."""

@dataclass
class DOCXProperties:
    """Placeholder for DOCX properties."""

@dataclass
class Change:
    """Placeholder for tracked changes."""

@dataclass
class CanvasContent:
    """محتوای <canvas> در HTML5"""
    canvas_id: str
    drawing_operations: list[CanvasOperation]

@dataclass
class DocumentMetadata:
    """متادیتای جامع برای همه فرمت‌ها"""
    # متادیتای عمومی
    title: str | None = None
    authors: list[str] = field(default_factory=list)
    creation_date: datetime | None = None
    modification_date: datetime | None = None

    # subject: Optional[str] = None
    # keywords: Optional[List[str]] = field(default_factory=list)
    # creator: Optional[str] = None
    # rights: Optional[str] = None
    # license: Optional[str] = None
    # copyright: Optional[str] = None
    # language: Optional[str] = None

    # متادیتای فرمت‌خاص
    format_specific: dict[str, Any] = field(default_factory=dict)

    # برای PDF
    pdf_info: PDFInfo | None = None

    # برای DOCX
    docx_properties: DOCXProperties | None = None

    # برای HTML
    meta_tags: dict[str, str] = field(default_factory=dict)

@dataclass
class CrossReference:
    """سیستم ارجاع متقابل بین عناصر"""
    source_id: str
    target_id: str
    reference_type: Literal["internal", "external", "bibliography", "footnote"]
    context: str | None = None

@dataclass
class BibliographyEntry:
    """ورودی‌های کتاب‌شناسی"""
    key: str
    entry_type: str  # "article", "book", "inproceedings"
    fields: dict[str, str] = field(default_factory=dict)

@dataclass
class ChangeTracking:
    """ردیابی تغییرات (مهم برای DOCX و Google Docs)"""
    revisions: list[Revision] = field(default_factory=list)
    comments: list[CommentContent] = field(default_factory=list)
    track_changes_enabled: bool = False

@dataclass
class Revision:
    author: str
    timestamp: datetime
    changes: list[Change] = field(default_factory=list)
    accepted: bool = False

@dataclass
class PresentationHint:
    """نشانه‌های ارائه برای تبدیل بین فرمت‌ها"""
    css_classes: list[str] = field(default_factory=list)
    latex_packages: list[str] = field(default_factory=list)
    priority: int = 0  # اولویت در تبدیل

class FormatPlugin(ABC):
    @abstractmethod
    def to_usdm(self, document) -> USDMDocument: ...

    @abstractmethod
    def from_usdm(self, usdm_document): ...

@dataclass
class TransformationRule:
    source_type: type[LogicalContent]
    target_type: type[LogicalContent]
    converter: Callable
    loss_level: Literal["none", "minimal", "moderate", "high"]

class TransformationPipeline:
    def __init__(self) -> None:
        self.rules: dict[tuple[str, str], TransformationRule] = {}

    def add_rule(self, source_format: str, target_format: str, rule: TransformationRule):
        self.rules[(source_format, target_format)] = rule

@dataclass
class ConversionQuality:
    semantic_preservation: float  # 0.0 to 1.0
    style_preservation: float
    layout_preservation: float
    information_loss: list[str]  # لیست اطلاعات از دست رفته
    warnings: list[str]




@dataclass
class BookmarkContent:
    """Content for bookmark."""
    name: str
    text: str | None = None


@dataclass
class FootnoteContent:
    """Content for footnote."""
    note_id: str
    elements: list[LogicalElement] = field(default_factory=list)
    reference_text: str | None = None


@dataclass
class EndnoteContent:
    """Content for endnote."""
    note_id: str
    elements: list[LogicalElement] = field(default_factory=list)
    reference_text: str | None = None



@dataclass
class EmbeddedObjectContent:
    """Content for embedded object."""
    name: str | None = None
    mime_type: str | None = None
    data: bytes | None = None
    relationship_id: str | None = None


@dataclass
class OLEObjectContent:
    """Content for OLE object."""
    prog_id: str | None = None
    data: bytes | None = None
    relationship_id: str | None = None
    display_as_icon: bool = False


@dataclass
class VideoContent:
    """Content for video."""
    src: str
    width: int | None = None
    height: int | None = None
    poster: str | None = None
    autoplay: bool = False
    controls: bool = True


@dataclass
class AudioContent:
    """Content for audio."""
    src: str
    autoplay: bool = False
    controls: bool = True
    loop: bool = False


@dataclass
class ShapeContent:
    """Shape for drawing (rectangle, line, ellipse, textbox, etc.)"""
    shape_type: str                              # "rectangle", "line", "ellipse", "circle", "textbox"
    x: int = 0                                   # position in EMU (left)
    y: int = 0                                   # position in EMU (top)
    width: int = 100                             # width in EMU (1/12700 cm)
    height: int = 100                            # height in EMU
    name: str | None = None                   # shape name
    text: RichTextContent | None = None       # text content (for textbox)
    fill_color: str | None = None             # hex color (e.g., "#FF0000")
    line_color: str | None = None             # stroke color
    line_width: int = 12700                      # stroke width in EMU (1 pt = 12700 EMU)
    rotation: int = 0                            # rotation in degrees
    hidden: bool = False
    _meta: dict[str, Any] = field(default_factory=dict, repr=False, init=False)
    # data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DrawingContent:
    """Content for drawings and vector graphics."""
    vector_data: str  # SVG or other vector format
    width: float | None = None
    height: float | None = None
    _diagram_rId: str | None = None
    _meta: dict[str, Any] = field(default_factory=dict)

@dataclass
class ChartSeriesContent:
    """A data series within a chart – mapped from chart XML."""
    name: str | None = None               # series name (e.g., "Sales")
    categories_ref: str | None = None     # formula like "Sheet1!$A$2:$A$10"
    values_ref: str | None = None         # formula like "Sheet1!$B$2:$B$10"
    fill_color: str | None = None         # hex color of the series fill
    line_color: str | None = None         # hex color of the series line

@dataclass
class ChartAxisContent:
    """Axis descriptor."""
    axis_type: str = "category"              # "category", "value", "date"
    title: str | None = None
    min_value: float | None = None
    max_value: float | None = None
    format_code: str | None = None
    axis_id: int = 0


@dataclass
class ChartContent:
    """Complete chart description – extended with semantic fields."""
    chart_type: str = "unknown"              # "bar", "line", "pie", etc.
    grouping: str | None = None           # "clustered", "stacked", etc.
    direction: str | None = None          # "bar" or "col" for bar charts
    title: str | None = None
    series: list[ChartSeriesContent] = field(default_factory=list)
    category_axis: ChartAxisContent | None = None
    value_axis: ChartAxisContent | None = None
    width: float | None = None
    height: float | None = None
    _chart_rId: str | None = None   # transient, for linking
    _meta: dict[str, Any] = field(default_factory=dict)
        
@dataclass
class DataContent:
    """Content for data fields (PAGE, DATE, etc.)."""
    field_type: str  # "PAGE", "DATE", "NUMPAGES", etc.
    value: str | None = None
    format: str | None = None


@dataclass
class SpreadsheetContent:
    """Content for embedded spreadsheet data."""
    text: str  # CSV or formula DSL
    sheet_name: str | None = None
    rows: int = 0
    columns: int = 0


LogicalContent = Union[
    ParagraphContent,
    HeadingContent,
    MathContent,
    CodeContent,
    ImageContent,
    ListContent,
    ListItemContent,
    TableContent,
    QuoteContent,
    DrawingContent,
    BinaryContent,
    DataContent,
    SpreadsheetContent,
    FormulaContent,
    LinkContent,
    FootnoteContent,
    EndnoteContent,
    CommentContent,
    BookmarkContent,
    PageBreakContent,
    LineBreakContent,
    ColumnBreakContent,
    EmbeddedObjectContent,
    OLEObjectContent,
    VideoContent,
    AudioContent,
    ShapeContent,
    ChartContent,
]
