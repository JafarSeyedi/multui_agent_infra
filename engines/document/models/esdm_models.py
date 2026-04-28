# engines/spreadsheet/models/esdm_models.py
"""
ESDM Models
===============
Excel Structured Data Model (ESDM)
Complete, industrial-grade modeling of Excel workbooks, built on top of USDM.

ESDM supports:
    - Workbooks with multiple worksheets
    - Cells with data types, formulas, rich text
    - Full Excel styling (fonts, fills, borders, number formats, alignment, protection)
    - Tables, auto filters, conditional formatting
    - Data validation, hyperlinks, comments (legacy & threaded)
    - Named ranges, shared formulas, external links
    - Pivot tables, calculation chain, sheet/page setup
    - Row/column properties, merged cells, relationships

This model reuses USDM components via inheritance and composition.
No changes to usdm_models.py are required.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple
from enum import Enum
from .base import BaseDocument

# ============================================================
# USDM imports (reused without modification)
# ============================================================
from engines.document.models.usdm_models import (
    RichTextContent,
    RichTextSpan,
    CharacterStyle,
    ParagraphStyle,
    TableStyle,
    ListStyle,
    DocumentMetadata,
    ImageContent,
    ChartContent,
    ShapeContent,
    CommentContent,          # legacy comment from USDM (can be mapped)
    StyleSheet,
)

@dataclass
class ESDMDocument(BaseDocument):
    """ESDM document that wraps a full Excel Workbook model."""
    kind: DocumentStandard = DocumentStandard.ESDM
    workbook: Optional[Workbook] = None

# ============================================================
# Base model (simple metadata container)
# ============================================================
@dataclass
class DocumentBaseModel:
    """Base class for all ESDM models, providing metadata hook."""
    _meta: Dict[str, Any] = field(default_factory=dict, repr=False, init=False)


# ============================================================
# Workbook-level models
# ============================================================
@dataclass
class WorkbookProperties(DocumentBaseModel):
    date_1904: bool = False
    default_theme_version: int = 0
    window_width: int = 1920
    window_height: int = 1080
    active_tab: int = 0

@dataclass
class Relationship(DocumentBaseModel):
    id: str
    type: str
    target: str
    mode: str = "Internal"  # "Internal" or "External"

@dataclass
class RelationshipCollection(DocumentBaseModel):
    relationships: List[Relationship] = field(default_factory=list)

    def add(self, rel: Relationship) -> None:
        self.relationships.append(rel)

    def find_by_type(self, rel_type: str) -> List[Relationship]:
        return [r for r in self.relationships if r.type == rel_type]

@dataclass
class SharedStrings(DocumentBaseModel):
    strings: List[str] = field(default_factory=list)
    index_map: Dict[str, int] = field(default_factory=dict, repr=False)

    def get_index(self, value: str) -> int:
        if value not in self.index_map:
            idx = len(self.strings)
            self.strings.append(value)
            self.index_map[value] = idx
        return idx


# ============================================================
# Cell, Row, Column (core spreadsheet primitives)
# ============================================================
@dataclass
class Cell(DocumentBaseModel):
    row: int
    col: int
    value: Any = None
    formula: Optional[str] = None
    style_id: Optional[int] = None
    hyperlink: Optional[str] = None
    comment: Optional[str] = None          # plain text comment (legacy)
    rich_text: Optional[RichTextContent] = None   # USDM rich text for cell

    @property
    def coordinate(self) -> str:
        return f"{self._col_to_letter(self.col)}{self.row}"

    @staticmethod
    def _col_to_letter(col: int) -> str:
        result = ""
        while col > 0:
            col, remainder = divmod(col - 1, 26)
            result = chr(65 + remainder) + result
        return result

@dataclass
class Row(DocumentBaseModel):
    index: int
    height: Optional[float] = None
    hidden: bool = False
    cells: Dict[int, Cell] = field(default_factory=dict)
    style_id: Optional[int] = None

    def get_or_create_cell(self, col: int) -> Cell:
        if col not in self.cells:
            self.cells[col] = Cell(row=self.index, col=col)
        return self.cells[col]

@dataclass
class Column(DocumentBaseModel):
    index: int
    width: Optional[float] = None
    hidden: bool = False
    style_id: Optional[int] = None


# ============================================================
# Ranges and Merged Cells
# ============================================================
@dataclass
class CellRange(DocumentBaseModel):
    min_row: int
    max_row: int
    min_col: int
    max_col: int

    @property
    def coord(self) -> str:
        return f"{self._coord(self.min_row, self.min_col)}:{self._coord(self.max_row, self.max_col)}"

    def _coord(self, row: int, col: int) -> str:
        return f"{Cell._col_to_letter(col)}{row}"

@dataclass
class MergedCellRange(CellRange):
    pass

@dataclass
class NamedRange(DocumentBaseModel):
    name: str
    range: CellRange
    scope: Optional[str] = None   # workbook or sheet name


# ============================================================
# Style Components – inheriting from USDM where appropriate
# ============================================================

# ------------------------------------------------------------
# Number Formats
# ------------------------------------------------------------
@dataclass
class NumberFormat(DocumentBaseModel):
    id: int
    format_code: str

@dataclass
class NumberFormatCollection(DocumentBaseModel):
    builtin_formats: Dict[int, str] = field(default_factory=dict)
    custom_formats: Dict[int, NumberFormat] = field(default_factory=dict)

    def add_custom_format(self, format_code: str) -> int:
        new_id = max(self.custom_formats.keys(), default=163) + 1
        fmt = NumberFormat(id=new_id, format_code=format_code)
        self.custom_formats[new_id] = fmt
        return new_id

    def find(self, id: int) -> Optional[str]:
        if id in self.builtin_formats:
            return self.builtin_formats[id]
        if id in self.custom_formats:
            return self.custom_formats[id].format_code
        return None

# ------------------------------------------------------------
# Font (Excel-specific, not from USDM)
# ------------------------------------------------------------
class FontUnderline(Enum):
    NONE = "none"
    SINGLE = "single"
    DOUBLE = "double"
    SINGLE_ACCOUNTING = "singleAccounting"
    DOUBLE_ACCOUNTING = "doubleAccounting"

@dataclass
class Font(DocumentBaseModel):
    name: str = "Calibri"
    size: float = 11.0
    bold: bool = False
    italic: bool = False
    underline: FontUnderline = FontUnderline.NONE
    strike: bool = False
    color: Optional[str] = None
    charset: Optional[int] = None
    family: Optional[int] = None
    scheme: Optional[str] = None

@dataclass
class FontCollection(DocumentBaseModel):
    fonts: List[Font] = field(default_factory=list)

    def register(self, font: Font) -> int:
        self.fonts.append(font)
        return len(self.fonts) - 1

# ------------------------------------------------------------
# Fill (Pattern and Gradient)
# ------------------------------------------------------------
class PatternType(Enum):
    NONE = "none"
    SOLID = "solid"
    DARK_GRAY = "darkGray"
    MEDIUM_GRAY = "mediumGray"
    LIGHT_GRAY = "lightGray"
    GRAY_125 = "gray125"
    GRAY_0625 = "gray0625"
    DARK_DOWN = "darkDown"
    DARK_UP = "darkUp"
    DARK_HORIZ = "darkHorizontal"
    DARK_VERT = "darkVertical"
    DARK_GRID = "darkGrid"
    DARK_TRELLIS = "darkTrellis"
    LIGHT_DOWN = "lightDown"
    LIGHT_UP = "lightUp"
    LIGHT_HORIZ = "lightHorizontal"
    LIGHT_VERT = "lightVertical"
    LIGHT_GRID = "lightGrid"
    LIGHT_TRELLIS = "lightTrellis"

@dataclass
class PatternFill(DocumentBaseModel):
    pattern_type: PatternType = PatternType.NONE
    fg_color: Optional[str] = None
    bg_color: Optional[str] = None

@dataclass
class GradientStop(DocumentBaseModel):
    position: float
    color: str

@dataclass
class GradientFill(DocumentBaseModel):
    degree: Optional[float] = None
    left: Optional[float] = None
    right: Optional[float] = None
    top: Optional[float] = None
    bottom: Optional[float] = None
    stops: List[GradientStop] = field(default_factory=list)

@dataclass
class Fill(DocumentBaseModel):
    pattern: Optional[PatternFill] = None
    gradient: Optional[GradientFill] = None

@dataclass
class FillCollection(DocumentBaseModel):
    fills: List[Fill] = field(default_factory=list)

    def register(self, fill: Fill) -> int:
        self.fills.append(fill)
        return len(self.fills) - 1

# ------------------------------------------------------------
# Border
# ------------------------------------------------------------
class BorderStyle(Enum):
    NONE = "none"
    THIN = "thin"
    MEDIUM = "medium"
    THICK = "thick"
    DOTTED = "dotted"
    DASHED = "dashed"
    DOUBLE = "double"
    HAIR = "hair"
    DASH_DOT = "dashDot"
    DASH_DOT_DOT = "dashDotDot"
    MEDIUM_DASH = "mediumDashed"
    MEDIUM_DASH_DOT = "mediumDashDot"
    MEDIUM_DASH_DOT_DOT = "mediumDashDotDot"
    SLANT_DASH_DOT = "slantDashDot"

@dataclass
class BorderSide(DocumentBaseModel):
    style: BorderStyle = BorderStyle.NONE
    color: Optional[str] = None

@dataclass
class Border(DocumentBaseModel):
    left: BorderSide = field(default_factory=BorderSide)
    right: BorderSide = field(default_factory=BorderSide)
    top: BorderSide = field(default_factory=BorderSide)
    bottom: BorderSide = field(default_factory=BorderSide)
    diagonal: BorderSide = field(default_factory=BorderSide)
    diagonal_up: bool = False
    diagonal_down: bool = False

@dataclass
class BorderCollection(DocumentBaseModel):
    borders: List[Border] = field(default_factory=list)

    def register(self, border: Border) -> int:
        self.borders.append(border)
        return len(self.borders) - 1

# ------------------------------------------------------------
# Alignment
# ------------------------------------------------------------
class HorizontalAlign(Enum):
    GENERAL = "general"
    LEFT = "left"
    RIGHT = "right"
    CENTER = "center"
    JUSTIFY = "justify"
    FILL = "fill"
    CENTER_CONTINUOUS = "centerContinuous"
    DISTRIBUTED = "distributed"

class VerticalAlign(Enum):
    TOP = "top"
    CENTER = "center"
    BOTTOM = "bottom"
    JUSTIFY = "justify"
    DISTRIBUTED = "distributed"

@dataclass
class Alignment(DocumentBaseModel):
    horizontal: HorizontalAlign = HorizontalAlign.GENERAL
    vertical: VerticalAlign = VerticalAlign.BOTTOM
    wrap_text: bool = False
    shrink_to_fit: bool = False
    indent: int = 0
    text_rotation: int = 0

# ------------------------------------------------------------
# Protection
# ------------------------------------------------------------
@dataclass
class Protection(DocumentBaseModel):
    locked: bool = True
    hidden: bool = False

# ------------------------------------------------------------
# Cell Format (xf) – uses USDM's CharacterStyle as base via composition
# but we keep separate because Excel uses indices.
# For maximum inheritance we could have CellStyle inherit, but we already did that.
# Here we define Excel's CellFormat as a container of references.
@dataclass
class CellFormat(DocumentBaseModel):
    number_format_id: Optional[int] = None
    font_id: Optional[int] = None
    fill_id: Optional[int] = None
    border_id: Optional[int] = None
    alignment: Optional[Alignment] = None
    protection: Optional[Protection] = None

@dataclass
class CellFormatCollection(DocumentBaseModel):
    formats: List[CellFormat] = field(default_factory=list)

    def register(self, xf: CellFormat) -> int:
        self.formats.append(xf)
        return len(self.formats) - 1

# ------------------------------------------------------------
# CellStyle (named style) – can inherit from USDM's CharacterStyle
# because a named style in Excel is essentially a CharacterStyle plus an xf_id.
@dataclass
class CellStyle(CharacterStyle):
    """Excel named style – extends USDM CharacterStyle with Excel-specific fields."""
    name: str
    builtin_id: Optional[int] = None
    xf_id: Optional[int] = None   # reference to a CellFormat

# ------------------------------------------------------------
# Differential Format (dxf) – used for conditional formatting and table styles
@dataclass
class DifferentialFormat(DocumentBaseModel):
    font: Optional[Font] = None
    fill: Optional[Fill] = None
    border: Optional[Border] = None
    alignment: Optional[Alignment] = None
    number_format: Optional[NumberFormat] = None

# ------------------------------------------------------------
# Table Styles (Excel specific)
@dataclass
class TableStyleElement(DocumentBaseModel):
    type: str   # "wholeTable", "headerRow", "totalRow", etc.
    dxf_id: Optional[int] = None
    size: Optional[int] = None

@dataclass
class ExcelTableStyle(DocumentBaseModel):
    name: str
    show_first_column: bool = False
    show_last_column: bool = False
    show_row_stripes: bool = False
    show_column_stripes: bool = False
    elements: List[TableStyleElement] = field(default_factory=list)

# ------------------------------------------------------------
# Master Stylesheet – inherits from USDM StyleSheet and adds Excel collections
@dataclass
class SpreadsheetStyleSheet(StyleSheet):
    """Extends USDM stylesheet with Excel-specific formatting collections."""
    number_formats: NumberFormatCollection = field(default_factory=NumberFormatCollection)
    excel_fonts: FontCollection = field(default_factory=FontCollection)
    fills: FillCollection = field(default_factory=FillCollection)
    borders: BorderCollection = field(default_factory=BorderCollection)
    cell_formats: CellFormatCollection = field(default_factory=CellFormatCollection)
    cell_styles: Dict[str, CellStyle] = field(default_factory=dict)  # name -> CellStyle
    dxfs: List[DifferentialFormat] = field(default_factory=list)
    excel_table_styles: Dict[str, ExcelTableStyle] = field(default_factory=dict)


# ============================================================
# Tables, AutoFilter, Conditional Formatting, etc.
# ============================================================

# ------------------------------------------------------------
# AutoFilter
# ------------------------------------------------------------
class DynamicFilterType(Enum):
    ABOVE_AVERAGE = "aboveAverage"
    BELOW_AVERAGE = "belowAverage"
    LAST_MONTH = "lastMonth"
    LAST_QUARTER = "lastQuarter"
    LAST_WEEK = "lastWeek"
    LAST_YEAR = "lastYear"
    NEXT_MONTH = "nextMonth"
    NEXT_QUARTER = "nextQuarter"
    NEXT_WEEK = "nextWeek"
    NEXT_YEAR = "nextYear"
    THIS_MONTH = "thisMonth"
    THIS_QUARTER = "thisQuarter"
    THIS_WEEK = "thisWeek"
    THIS_YEAR = "thisYear"
    TODAY = "today"
    TOMORROW = "tomorrow"
    YEAR_TO_DATE = "yearToDate"
    YESTERDAY = "yesterday"

class FilterOperator(Enum):
    EQUAL = "equal"
    NOT_EQUAL = "notEqual"
    GREATER_THAN = "greaterThan"
    LESS_THAN = "lessThan"
    GREATER_OR_EQUAL = "greaterThanOrEqual"
    LESS_OR_EQUAL = "lessThanOrEqual"

@dataclass
class CustomFilter(DocumentBaseModel):
    operator: FilterOperator
    value: Any

@dataclass
class Filters(DocumentBaseModel):
    values: List[Any] = field(default_factory=list)
    blank: bool = False

@dataclass
class FilterColumn(DocumentBaseModel):
    col_id: int
    filters: Optional[Filters] = None
    custom_filters: List[CustomFilter] = field(default_factory=list)
    dynamic_filter: Optional[DynamicFilterType] = None

@dataclass
class AutoFilter(DocumentBaseModel):
    ref: Optional[str] = None
    filter_columns: List[FilterColumn] = field(default_factory=list)

# ------------------------------------------------------------
# Table
# ------------------------------------------------------------
@dataclass
class TableColumn(DocumentBaseModel):
    id: int
    name: str
    totals_row_function: Optional[str] = None
    totals_row_label: Optional[str] = None
    calculated_column_formula: Optional[str] = None

@dataclass
class ExcelTableRow(DocumentBaseModel):
    index: int
    values: Dict[int, Any] = field(default_factory=dict)

@dataclass
class TableStyleInfo(DocumentBaseModel):
    name: str = "TableStyleMedium9"
    show_first_column: bool = False
    show_last_column: bool = False
    show_row_stripes: bool = True
    show_column_stripes: bool = False

@dataclass
class Table(DocumentBaseModel):
    id: int
    name: str
    display_name: Optional[str] = None
    ref: Optional[str] = None
    header_row_count: int = 1
    totals_row_count: int = 0
    columns: List[TableColumn] = field(default_factory=list)
    rows: List[ExcelTableRow] = field(default_factory=list)
    auto_filter: Optional[AutoFilter] = None
    table_style_info: TableStyleInfo = field(default_factory=TableStyleInfo)

# ------------------------------------------------------------
# Conditional Formatting
# ------------------------------------------------------------
class CFType(Enum):
    CELL_IS = "cellIs"
    EXPRESSION = "expression"
    COLOR_SCALE = "colorScale"
    DATA_BAR = "dataBar"
    ICON_SET = "iconSet"
    TOP_10 = "top10"
    UNIQUE_VALUES = "uniqueValues"
    DUPLICATE_VALUES = "duplicateValues"
    CONTAINS_TEXT = "containsText"
    NOT_CONTAINS_TEXT = "notContainsText"
    BEGINS_WITH = "beginsWith"
    ENDS_WITH = "endsWith"
    CONTAINS_BLANKS = "containsBlanks"
    NOT_CONTAINS_BLANKS = "notContainsBlanks"
    CONTAINS_ERRORS = "containsErrors"
    NOT_CONTAINS_ERRORS = "notContainsErrors"
    TIME_PERIOD = "timePeriod"
    ABOVE_AVERAGE = "aboveAverage"

class CFOperator(Enum):
    LESS_THAN = "lessThan"
    LESS_OR_EQUAL = "lessThanOrEqual"
    GREATER_THAN = "greaterThan"
    GREATER_OR_EQUAL = "greaterThanOrEqual"
    EQUAL = "equal"
    NOT_EQUAL = "notEqual"
    BETWEEN = "between"
    NOT_BETWEEN = "notBetween"

@dataclass
class CFValueObject(DocumentBaseModel):
    type: str   # "num", "percentile", "formula", "min", "max"
    value: Optional[Any] = None

@dataclass
class ColorScale(DocumentBaseModel):
    values: List[CFValueObject] = field(default_factory=list)
    colors: List[str] = field(default_factory=list)

@dataclass
class DataBar(DocumentBaseModel):
    min_value: CFValueObject = field(default_factory=lambda: CFValueObject(type="min"))
    max_value: CFValueObject = field(default_factory=lambda: CFValueObject(type="max"))
    color: str = "#638EC6"
    show_value: bool = True
    border: bool = False
    gradient: bool = True

class IconSetType(Enum):
    THREE_ARROWS = "3Arrows"
    THREE_ARROWS_GRAY = "3ArrowsGray"
    THREE_TRAFFIC_LIGHTS = "3TrafficLights1"
    THREE_TRAFFIC_LIGHTS2 = "3TrafficLights2"
    THREE_SYMBOLS = "3Symbols"
    THREE_SYMBOLS2 = "3Symbols2"
    FOUR_RATINGS = "4Rating"
    FIVE_ARROWS = "5Arrows"
    FIVE_ARROWS_GRAY = "5ArrowsGray"
    FIVE_RATINGS = "5Rating"

@dataclass
class IconCriterion(DocumentBaseModel):
    type: str
    value: Optional[Any] = None
    operator: Optional[str] = None
    icon_id: int = 0

@dataclass
class IconSet(DocumentBaseModel):
    icon_set_type: IconSetType = IconSetType.THREE_TRAFFIC_LIGHTS
    criteria: List[IconCriterion] = field(default_factory=list)
    show_value: bool = True
    reverse: bool = False

@dataclass
class CFRule(DocumentBaseModel):
    type: CFType
    priority: int
    dxf_id: Optional[int] = None
    stop_if_true: bool = False
    operator: Optional[CFOperator] = None
    formula: List[str] = field(default_factory=list)
    color_scale: Optional[ColorScale] = None
    data_bar: Optional[DataBar] = None
    icon_set: Optional[IconSet] = None

@dataclass
class ConditionalFormatting(DocumentBaseModel):
    ref: str
    rules: List[CFRule] = field(default_factory=list)


# ============================================================
# Formulas and Defined Names
# ============================================================
class FormulaTokenType(Enum):
    OPERAND = "operand"
    OPERATOR = "operator"
    FUNCTION = "function"
    PAREN_OPEN = "paren_open"
    PAREN_CLOSE = "paren_close"
    ARRAY = "array"
    RANGE = "range"
    STRUCTURED_REF = "structured_reference"

@dataclass
class FormulaToken(DocumentBaseModel):
    type: FormulaTokenType
    value: Any

@dataclass
class FormulaAST(DocumentBaseModel):
    tokens: List[FormulaToken] = field(default_factory=list)

    @classmethod
    def from_string(cls, formula: str) -> FormulaAST:
        return cls(tokens=[FormulaToken(type=FormulaTokenType.OPERAND, value=formula)])

    def to_string(self) -> str:
        if len(self.tokens) == 1 and self.tokens[0].type == FormulaTokenType.OPERAND:
            return str(self.tokens[0].value)
        return "".join(str(t.value) for t in self.tokens)

@dataclass
class SharedFormula(DocumentBaseModel):
    shared_index: int
    ref: str
    formula: FormulaAST

@dataclass
class DefinedName(DocumentBaseModel):
    name: str
    formula: str
    local_sheet_id: Optional[int] = None
    comment: Optional[str] = None
    hidden: bool = False
    function: bool = False
    vb_procedure: bool = False

@dataclass
class ExternalReference(DocumentBaseModel):
    workbook_name: str
    sheet_name: str
    ref: str

@dataclass
class ExternalLink(DocumentBaseModel):
    id: int
    file_path: str
    references: List[ExternalReference] = field(default_factory=list)

@dataclass
class CellFormula(DocumentBaseModel):
    text: str
    ast: Optional[FormulaAST] = None
    shared_index: Optional[int] = None
    array: bool = False

    @classmethod
    def create(cls, formula_text: str, shared_index: Optional[int] = None) -> CellFormula:
        return cls(text=formula_text,
                   ast=FormulaAST.from_string(formula_text),
                   shared_index=shared_index)

    def get(self) -> str:
        if self.ast:
            return self.ast.to_string()
        return self.text


# ============================================================
# Data Validation, Hyperlinks, Comments
# ============================================================
class DataValidationType(Enum):
    WHOLE = "whole"
    DECIMAL = "decimal"
    LIST = "list"
    DATE = "date"
    TIME = "time"
    TEXT_LENGTH = "textLength"
    CUSTOM = "custom"

class DataValidationOperator(Enum):
    BETWEEN = "between"
    NOT_BETWEEN = "notBetween"
    LESS_THAN = "lessThan"
    GREATER_THAN = "greaterThan"
    EQUAL = "equal"
    NOT_EQUAL = "notEqual"

@dataclass
class DataValidationRule(DocumentBaseModel):
    type: DataValidationType
    operator: Optional[DataValidationOperator] = None
    allow_blank: bool = False
    show_input_message: bool = False
    show_error_message: bool = True
    error_title: Optional[str] = None
    error_message: Optional[str] = None
    prompt_title: Optional[str] = None
    prompt_message: Optional[str] = None
    formula1: Optional[str] = None
    formula2: Optional[str] = None

@dataclass
class DataValidation(DocumentBaseModel):
    ref: str
    rule: DataValidationRule

@dataclass
class Hyperlink(DocumentBaseModel):
    ref: str
    target: str
    tooltip: Optional[str] = None
    display: Optional[str] = None

# Legacy comments
@dataclass
class Author(DocumentBaseModel):
    name: str

@dataclass
class CommentTextRun(DocumentBaseModel):
    text: str
    bold: bool = False
    italic: bool = False
    underline: bool = False
    color: Optional[str] = None

@dataclass
class CommentText(DocumentBaseModel):
    runs: List[CommentTextRun] = field(default_factory=list)

    @classmethod
    def from_string(cls, text: str) -> CommentText:
        return cls(runs=[CommentTextRun(text=text)])

@dataclass
class Comment(DocumentBaseModel):
    ref: str
    author_id: int
    text: CommentText

@dataclass
class CommentCollection(DocumentBaseModel):
    authors: List[Author] = field(default_factory=list)
    comments: List[Comment] = field(default_factory=list)

# Threaded comments (modern)
@dataclass
class ThreadedComment(DocumentBaseModel):
    ref: str
    text: str
    author: str
    date: Optional[str] = None


# ============================================================
# Worksheet Properties, Protection, Page Setup
# ============================================================
@dataclass
class SheetProperties(DocumentBaseModel):
    tab_color: Optional[str] = None
    filter_mode: bool = False
    published: bool = True
    show_gridlines: bool = True

@dataclass
class SheetProtection(DocumentBaseModel):
    sheet: bool = False
    objects: bool = False
    scenarios: bool = False
    format_cells: bool = True
    format_columns: bool = True
    format_rows: bool = True
    insert_columns: bool = True
    insert_rows: bool = True
    insert_hyperlinks: bool = True
    delete_columns: bool = True
    delete_rows: bool = True
    select_locked_cells: bool = True
    select_unlocked_cells: bool = True

class Orientation(Enum):
    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"

@dataclass
class PageMargins(DocumentBaseModel):
    left: float = 0.7
    right: float = 0.7
    top: float = 0.75
    bottom: float = 0.75
    header: float = 0.3
    footer: float = 0.3

@dataclass
class PageSetup(DocumentBaseModel):
    orientation: Orientation = Orientation.PORTRAIT
    scale: int = 100
    paper_size: int = 9
    fit_to_width: Optional[int] = None
    fit_to_height: Optional[int] = None

@dataclass
class SheetDimensions(DocumentBaseModel):
    min_row: int = 1
    max_row: int = 1
    min_col: int = 1
    max_col: int = 1


# ============================================================
# Calculation Chain
# ============================================================
@dataclass
class CalcChainEntry(DocumentBaseModel):
    sheet_id: int
    ref: str
    array: bool = False

@dataclass
class CalculationChain(DocumentBaseModel):
    items: List[CalcChainEntry] = field(default_factory=list)


# ============================================================
# Pivot Tables
# ============================================================
@dataclass
class PivotField(DocumentBaseModel):
    name: str
    orientation: str   # row, column, data, page
    subtotal: Optional[str] = None

@dataclass
class PivotCacheReference(DocumentBaseModel):
    sheet: str
    ref: str

@dataclass
class PivotCache(DocumentBaseModel):
    id: int
    source: PivotCacheReference

@dataclass
class PivotTable(DocumentBaseModel):
    name: str
    location: str
    cache_id: int
    fields: List[PivotField] = field(default_factory=list)


# # ============================================================
# # Shape Content (for floating shapes)
# # ============================================================

# @dataclass
# class ShapeContent(DocumentBaseModel):
#     """Shape for drawing (rectangle, line, ellipse, textbox, etc.)"""
#     shape_type: str                              # "rectangle", "line", "ellipse", "circle", "textbox"
#     x: int = 0                                   # position in EMU (left)
#     y: int = 0                                   # position in EMU (top)
#     width: int = 100                             # width in EMU (1/12700 cm)
#     height: int = 100                            # height in EMU
#     name: Optional[str] = None                   # shape name
#     text: Optional[RichTextContent] = None       # text content (for textbox)
#     fill_color: Optional[str] = None             # hex color (e.g., "#FF0000")
#     line_color: Optional[str] = None             # stroke color
#     line_width: int = 12700                      # stroke width in EMU (1 pt = 12700 EMU)
#     rotation: int = 0                            # rotation in degrees
#     hidden: bool = False
    
# ============================================================
# Worksheet (complete)
# ============================================================
@dataclass
class Worksheet(DocumentBaseModel):
    name: str
    rows: Dict[int, Row] = field(default_factory=dict)
    columns: Dict[int, Column] = field(default_factory=dict)
    merged_cells: List[MergedCellRange] = field(default_factory=list)
    named_ranges: List[NamedRange] = field(default_factory=list)
    tables: List[Table] = field(default_factory=list)
    conditional_formattings: List[ConditionalFormatting] = field(default_factory=list)
    data_validations: List[DataValidation] = field(default_factory=list)
    hyperlinks: List[Hyperlink] = field(default_factory=list)
    comments: CommentCollection = field(default_factory=CommentCollection)
    threaded_comments: List[ThreadedComment] = field(default_factory=list)
    properties: SheetProperties = field(default_factory=SheetProperties)
    protection: SheetProtection = field(default_factory=SheetProtection)
    page_setup: PageSetup = field(default_factory=PageSetup)
    margins: PageMargins = field(default_factory=PageMargins)
    dimensions: SheetDimensions = field(default_factory=SheetDimensions)
    auto_filter: Optional[AutoFilter] = None
    shapes: List[ShapeContent] = field(default_factory=list)
    # Floating USDM objects (reused)
    floating_images: List[ImageContent] = field(default_factory=list)
    floating_charts: List[ChartContent] = field(default_factory=list)

    def get_row(self, index: int) -> Row:
        if index not in self.rows:
            self.rows[index] = Row(index=index)
        return self.rows[index]

    def get_cell(self, row: int, col: int) -> Cell:
        return self.get_row(row).get_or_create_cell(col)

    def merge_cells(self, min_row: int, min_col: int, max_row: int, max_col: int) -> None:
        self.merged_cells.append(
            MergedCellRange(min_row=min_row, max_row=max_row,
                            min_col=min_col, max_col=max_col)
        )


# ============================================================
# Workbook (top-level)
# ============================================================
@dataclass
class Workbook(DocumentBaseModel):
    properties: WorkbookProperties = field(default_factory=WorkbookProperties)
    sheets: List[Worksheet] = field(default_factory=list)
    shared_strings: SharedStrings = field(default_factory=SharedStrings)
    relationships: RelationshipCollection = field(default_factory=RelationshipCollection)
    named_ranges: List[NamedRange] = field(default_factory=list)
    defined_names: List[DefinedName] = field(default_factory=list)
    external_links: List[ExternalLink] = field(default_factory=list)
    stylesheet: SpreadsheetStyleSheet = field(default_factory=SpreadsheetStyleSheet)
    calculation_chain: CalculationChain = field(default_factory=CalculationChain)
    pivot_caches: List[PivotCache] = field(default_factory=list)
    pivot_tables: List[PivotTable] = field(default_factory=list)

    vba_project: Optional[bytes] = None                # Raw VBA binary
    full_calculation_on_load: bool = True              # Whether to recalculate on open

    # Reuse USDM metadata
    metadata: DocumentMetadata = field(default_factory=DocumentMetadata)
    
    
    def add_sheet(self, name: str) -> Worksheet:
        sheet = Worksheet(name=name)
        self.sheets.append(sheet)
        return sheet

    def get_sheet_by_name(self, name: str) -> Optional[Worksheet]:
        for sheet in self.sheets:
            if sheet.name == name:
                return sheet
        return None