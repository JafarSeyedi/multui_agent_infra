# engines/document/models/usdm_models.py
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from .media_types import DocumentStandard

from .base import BaseDocument, ElementType

from typing import List, Optional, Dict, Any, Union, Literal, Type, Callable, Tuple
from abc import ABC, abstractmethod
from datetime import datetime

class USDMDocument(BaseDocument):
    kind: DocumentStandard = DocumentStandard.USDM
    sections: List[Section] = field(default_factory=list)
    pages: List[Page] = field(default_factory=list)
# elements: لایه‌ی منطقی (Logical tree) → محتوای واقعی سند
# sections: لایه‌ی سازمانی/سرفصلی → ساختار معنایی سند
# pages: لایه‌ی فیزیکی/صفحه‌بندی → خروجی صفحه‌بندی شده (PDF-like)
    elements: List[DocumentElement] = field(default_factory=list)
    logical_elements: List[LogicalElement] = field(default_factory=list)
    stylesheet: StyleSheet = field(default_factory=StyleSheet)


@dataclass
class DocumentElement:
    element_id: str
    element_type: ElementType
    metadata: Dict[str, Any] = field(default_factory=dict) 

@dataclass
class Section:
    section_id: str = ""
    title: Optional[HeadingContent] = None
    elements: List[DocumentElement] = field(default_factory=list)
    section_type: Optional[str] = None  # e.g. "body", "header", "footer"
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PageContent:
    number: Optional[int] = None
    elements: List[DocumentElement] = field(default_factory=list)
    page_width: Optional[float] = None
    page_height: Optional[float] = None
    margin_top: Optional[float] = None
    margin_bottom: Optional[float] = None
    margin_left: Optional[float] = None
    margin_right: Optional[float] = None


@dataclass
class LogicalElement:
    element_id: str
    element_type: ElementType
    content: Any
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================
# RICH TEXT
# ============================================================

@dataclass
class RichTextSpan:
    text: str = ""
    character_style: Optional[str] = None  # key into StyleSheet.character_styles
    code: bool = False
    background: Optional[str] = None
    href: Optional[str] = None
    math: Optional[str] = None  # inline math
    display_math: bool = False

@dataclass
class RichTextContent:
    spans: List[RichTextSpan] = field(default_factory=list)


# ============================================================
# LOGICAL CONTENT TYPES
# ============================================================

@dataclass
class ParagraphContent:
    text: RichTextContent
    style: Optional[str] = None


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
    language: Optional[str] = None


@dataclass
class ImageContent:
    src: str
    width: Optional[float] = None
    height: Optional[float] = None
    alt: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ListItemContent:
    elements: List[LogicalElement]


@dataclass
class ListContent:
    ordered: bool
    items: List[ListItemContent]


# TABLES
@dataclass
class TableCell:
    content: List[LogicalElement]
    row_span: int = 1
    col_span: int = 1
    is_header: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TableRow:
    cells: List[TableCell] = []
    is_header: bool = False    
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TableContent:
    rows: List[TableRow]
    grid: Optional[List[int]] = None     # Word-style table grid definition
    caption: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QuoteContent:
    elements: List[LogicalElement]


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
    color: Optional[str] = None
    style_id: Optional[str] = None
    bbox: Optional[Dict[str, float]] = None
    language: Optional[str] = None

@dataclass
class ImageObject:
    src: str
    x: float
    y: float
    width: float
    height: float
    format: str = 'jpg'
    bbox: Optional[Dict[str, float]] = None

@dataclass
class VectorPath:
    commands: List[str]
    stroke_color: Optional[str] = None
    fill_color: Optional[str] = None
    stroke_width: Optional[float] = None
    points: Optional[List[Dict[str, float]]] = None


@dataclass
class AnnotationObject:
    x: float
    y: float
    width: float
    height: float
    subtype: str
    contents: Optional[str] = None


@dataclass
class Page:
    page_number: int
    width: float
    height: float
    elements: List[Union[TextRun, ImageObject, VectorPath, AnnotationObject]] = field(default_factory=list)



# ============================================================
# LEVEL 3 — STYLES
# ============================================================

@dataclass
class CharacterStyle:
    name: str
    bold: Optional[bool] = None
    italic: Optional[bool] = None
    underline: Optional[bool] = None
    underline_type: Optional[str] = None
    color: Optional[str] = None
    highlight: Optional[str] = None
    background: Optional[str] = None
    font: Optional[str] = None
    font_family: Optional[str] = None
    font_charset: Optional[str] = None
    font_pitch: Optional[str] = None
    size: Optional[float] = None
    size_cs: Optional[float] = None
    strike: Optional[bool] = None
    double_strike: Optional[bool] = None
    superscript: Optional[bool] = None
    subscript: Optional[bool] = None
    small_caps: Optional[bool] = None
    all_caps: Optional[bool] = None
    kerning: Optional[float] = None
    spacing: Optional[float] = None
    position: Optional[float] = None
    shadow: Optional[bool] = None
    outline: Optional[bool] = None
    emboss: Optional[bool] = None
    imprint: Optional[bool] = None
    vanished: Optional[bool] = None
    web_hidden: Optional[bool] = None
    language: Optional[str] = None
    no_proof: Optional[bool] = None
    style_id: Optional[str] = None
    based_on: Optional[str] = None
    next_style: Optional[str] = None
    linked_style: Optional[str] = None

@dataclass
class ParagraphStyle:
    name: str
    alignment: Optional[str] = None  # "left", "right", "center", "justify"
    spacing_before: Optional[float] = None
    spacing_after: Optional[float] = None
    line_spacing: Optional[float] = None
    indent_left: Optional[float] = None
    indent_right: Optional[float] = None
    first_line_indent: Optional[float] = None

    line_spacing_rule: Optional[str] = None
    indent_hanging: Optional[float] = None
    keep_lines_together: Optional[bool] = None
    keep_with_next: Optional[bool] = None
    page_break_before: Optional[bool] = None
    widow_control: Optional[bool] = None
    borders: Optional[Dict[str, Any]] = None
    shading: Optional[Dict[str, Any]] = None
    outline_level: Optional[int] = None
    text_direction: Optional[str] = None   # "ltr", "rtl", etc.
    tabs: Optional[List[Dict[str, Any]]] = None
    frame_properties: Optional[Dict[str, Any]] = None
    style_id: Optional[str] = None
    based_on: Optional[str] = None
    next_style: Optional[str] = None

@dataclass
class TableStyle:
    name: str
    border_color: Optional[str] = None
    border_width: Optional[float] = None
    cell_spacing: Optional[float] = None
    header_row: Optional[bool] = None
    banded_rows: Optional[bool] = None
    banded_columns: Optional[bool] = None

    alignment: Optional[str] = None               # "left", "center", "right"
    indent_left: Optional[float] = None
    width: Optional[float] = None
    layout_type: Optional[str] = None             # "fixed", "auto"
    borders: Optional[Dict[str, Any]] = None
    cell_margins: Optional[Dict[str, float]] = None
    shading: Optional[Dict[str, Any]] = None
    first_row: Optional[bool] = None              # special formatting for first row
    last_row: Optional[bool] = None
    first_column: Optional[bool] = None
    last_column: Optional[bool] = None
    style_id: Optional[str] = None
    based_on: Optional[str] = None

@dataclass
class ListStyle:
    name: str
    level_styles: Dict[int, Dict[str, Any]] = field(default_factory=dict)

@dataclass
class StyleSheet:
    character_styles: Dict[str, CharacterStyle] = field(default_factory=dict)
    paragraph_styles: Dict[str, ParagraphStyle] = field(default_factory=dict)
    table_styles: Dict[str, TableStyle] = field(default_factory=dict)
    list_styles: Dict[str, ListStyle] = field(default_factory=dict)



















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
    date: Optional[str] = None
    text: str = ""
    elements: List[LogicalElement] = field(default_factory=list)
    parent_id: Optional[str] = None
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
    font: Optional[str]
    size: Optional[float]

@dataclass
class PDFVectorPath:
    commands: List[str]
    stroke_color: Optional[str] = None
    fill_color: Optional[str] = None

@dataclass
class LaTeXEnvironmentContent:
    """محیط‌های LaTeX مانند theorem, proof, figure"""
    environment_type: str  # "theorem", "lemma", "figure", "table"
    label: Optional[str]
    caption: Optional[str]
    parameters: Dict[str, str] = field(default_factory=dict)
    content: List[LogicalContent] = field(default_factory=list)

@dataclass  
class LaTeXCommandContent:
    """دستورات LaTeX مانند \\section{}, \\cite{}"""
    command: str
    arguments: List[str] = field(default_factory=list)
    options: Dict[str, str] = field(default_factory=dict)

@dataclass
class SemanticHTMLContent:
    """عناصر معنایی HTML5"""
    element_type: Literal["article", "section", "nav", "aside", "header", "footer"]
    role: Optional[str]  # برای ARIA roles
    aria_attributes: Dict[str, str] = field(default_factory=dict)

@dataclass
class CanvasOperation:
    """Placeholder for canvas operations."""
    pass

@dataclass
class PDFInfo:
    """Placeholder for PDF metadata."""
    pass

@dataclass
class DOCXProperties:
    """Placeholder for DOCX properties."""
    pass

@dataclass
class Change:
    """Placeholder for tracked changes."""
    pass

@dataclass
class CanvasContent:
    """محتوای <canvas> در HTML5"""
    canvas_id: str
    drawing_operations: List[CanvasOperation]

@dataclass
class DocumentMetadata:
    """متادیتای جامع برای همه فرمت‌ها"""
    # متادیتای عمومی
    title: Optional[str] = None
    authors: List[str] = field(default_factory=list)
    creation_date: Optional[datetime] = None
    modification_date: Optional[datetime] = None
    
    # subject: Optional[str] = None
    # keywords: Optional[List[str]] = field(default_factory=list)
    # creator: Optional[str] = None
    # rights: Optional[str] = None
    # license: Optional[str] = None
    # copyright: Optional[str] = None
    # language: Optional[str] = None
        
    # متادیتای فرمت‌خاص
    format_specific: Dict[str, Any] = field(default_factory=dict)
    
    # برای PDF
    pdf_info: Optional[PDFInfo] = None
    
    # برای DOCX
    docx_properties: Optional[DOCXProperties] = None
    
    # برای HTML
    meta_tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class CrossReference:
    """سیستم ارجاع متقابل بین عناصر"""
    source_id: str
    target_id: str
    reference_type: Literal["internal", "external", "bibliography", "footnote"]
    context: Optional[str] = None
    
@dataclass
class BibliographyEntry:
    """ورودی‌های کتاب‌شناسی"""
    key: str
    entry_type: str  # "article", "book", "inproceedings"
    fields: Dict[str, str] = field(default_factory=dict)

@dataclass
class ChangeTracking:
    """ردیابی تغییرات (مهم برای DOCX و Google Docs)"""
    revisions: List[Revision] = field(default_factory=list)
    comments: List[CommentContent] = field(default_factory=list)
    track_changes_enabled: bool = False

@dataclass
class Revision:
    author: str
    timestamp: datetime
    changes: List[Change] = field(default_factory=list)
    accepted: bool = False

@dataclass
class PresentationHint:
    """نشانه‌های ارائه برای تبدیل بین فرمت‌ها"""
    css_classes: List[str] = field(default_factory=list)
    latex_packages: List[str] = field(default_factory=list)
    priority: int = 0  # اولویت در تبدیل

class FormatPlugin(ABC):
    @abstractmethod
    def to_usdm(self, document) -> USDMDocument: ...
    
    @abstractmethod
    def from_usdm(self, usdm_document): ...

@dataclass
class TransformationRule:
    source_type: Type[LogicalContent]
    target_type: Type[LogicalContent]
    converter: Callable
    loss_level: Literal["none", "minimal", "moderate", "high"]
    
class TransformationPipeline:
    def __init__(self) -> None:
        self.rules: Dict[Tuple[str, str], TransformationRule] = {}
    
    def add_rule(self, source_format: str, target_format: str, rule: TransformationRule):
        self.rules[(source_format, target_format)] = rule

@dataclass
class ConversionQuality:
    semantic_preservation: float  # 0.0 to 1.0
    style_preservation: float
    layout_preservation: float
    information_loss: List[str]  # لیست اطلاعات از دست رفته
    warnings: List[str]




@dataclass
class BookmarkContent:
    """Content for bookmark."""
    name: str
    text: Optional[str] = None


@dataclass
class FootnoteContent:
    """Content for footnote."""
    note_id: str
    elements: List[LogicalElement] = field(default_factory=list)
    reference_text: Optional[str] = None


@dataclass
class EndnoteContent:
    """Content for endnote."""
    note_id: str
    elements: List[LogicalElement] = field(default_factory=list)
    reference_text: Optional[str] = None



@dataclass
class EmbeddedObjectContent:
    """Content for embedded object."""
    name: Optional[str] = None
    mime_type: Optional[str] = None
    data: Optional[bytes] = None
    relationship_id: Optional[str] = None


@dataclass
class OLEObjectContent:
    """Content for OLE object."""
    prog_id: Optional[str] = None
    data: Optional[bytes] = None
    relationship_id: Optional[str] = None
    display_as_icon: bool = False


@dataclass
class VideoContent:
    """Content for video."""
    src: str
    width: Optional[int] = None
    height: Optional[int] = None
    poster: Optional[str] = None
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
    name: Optional[str] = None                   # shape name
    text: Optional[RichTextContent] = None       # text content (for textbox)
    fill_color: Optional[str] = None             # hex color (e.g., "#FF0000")
    line_color: Optional[str] = None             # stroke color
    line_width: int = 12700                      # stroke width in EMU (1 pt = 12700 EMU)
    rotation: int = 0                            # rotation in degrees
    hidden: bool = False
    _meta: Dict[str, Any] = field(default_factory=dict, repr=False, init=False)
    # data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DrawingContent:
    """Content for drawings and vector graphics."""
    vector_data: str  # SVG or other vector format
    width: Optional[float] = None
    height: Optional[float] = None


@dataclass
class ChartSeriesContent:
    """A data series within a chart – mapped from chart XML."""
    name: Optional[str] = None               # series name (e.g., "Sales")
    categories_ref: Optional[str] = None     # formula like "Sheet1!$A$2:$A$10"
    values_ref: Optional[str] = None         # formula like "Sheet1!$B$2:$B$10"
    fill_color: Optional[str] = None         # hex color of the series fill
    line_color: Optional[str] = None         # hex color of the series line

@dataclass
class ChartAxisContent:
    """Axis descriptor."""
    axis_type: str = "category"              # "category", "value", "date"
    title: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    format_code: Optional[str] = None
    axis_id: int = 0


@dataclass
class ChartContent:
    """Complete chart description – extended with semantic fields."""
    chart_type: str = "unknown"              # "bar", "line", "pie", etc.
    grouping: Optional[str] = None           # "clustered", "stacked", etc.
    direction: Optional[str] = None          # "bar" or "col" for bar charts
    title: Optional[str] = None
    series: List[ChartSeriesContent] = field(default_factory=list)
    category_axis: Optional[ChartAxisContent] = None
    value_axis: Optional[ChartAxisContent] = None
    width: Optional[float] = None
    height: Optional[float] = None

@dataclass
class DataContent:
    """Content for data fields (PAGE, DATE, etc.)."""
    field_type: str  # "PAGE", "DATE", "NUMPAGES", etc.
    value: Optional[str] = None
    format: Optional[str] = None


@dataclass
class SpreadsheetContent:
    """Content for embedded spreadsheet data."""
    text: str  # CSV or formula DSL
    sheet_name: Optional[str] = None
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
