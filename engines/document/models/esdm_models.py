"""
ESDM Models
===============
Excel Structured Data Model (ESDM)
Pythonic, complete, industrial-grade modeling of Excel workbooks

A clean, implementation-friendly data model for representing Excel workbooks
independent of file format (XLSX). The goal is to provide a complete and
consistent structure that can be parsed from, or written to, Excel files.

ESDM supports:
    - Multiple worksheets
    - Cells with different data types
    - Formulas
    - Styles
    - Merged cells
    - Tables
    - Named ranges
    - Hyperlinks
    - Row/Column properties
    - Worksheet metadata

This model is intentionally independent from USDM.
A converter (Excel → USDM View / USDM → Excel Table) will be built separately.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union, Tuple
from enum import Enum
from .media_types import DocumentStandard

from .base import BaseDocument

# ============================================================
# Base model
# ============================================================

@dataclass
class DocumentBaseModel:
    """
    Base class for all ESDM models.
    Provides consistent API surface and metadata hooks.
    """
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
    """
    A relationship inside XLSX (but represented Pythonically):
    connects workbook → sheets, styles, shared strings, drawings, etc.
    """
    id: str
    type: str
    target: str
    mode: str = "Internal"  # or "External"


@dataclass
class RelationshipCollection(DocumentBaseModel):
    relationships: List[Relationship] = field(default_factory=list)

    def add(self, rel: Relationship):
        self.relationships.append(rel)

    def find_by_type(self, rel_type: str) -> List[Relationship]:
        return [r for r in self.relationships if r.type == rel_type]


@dataclass
class SharedStrings(DocumentBaseModel):
    """
    Shared string table used by Excel to deduplicate strings.
    Pythonic version: simple list mapping index → string.
    """
    strings: List[str] = field(default_factory=list)
    index_map: Dict[str, int] = field(default_factory=dict, repr=False)

    def get_index(self, value: str) -> int:
        if value not in self.index_map:
            idx = len(self.strings)
            self.strings.append(value)
            self.index_map[value] = idx
        return self.index_map[value]


# ============================================================
# Worksheet-level models
# ============================================================

@dataclass
class SheetDimensions(DocumentBaseModel):
    """
    Sheet used area bounding box.
    """
    min_row: int = 1
    max_row: int = 1
    min_col: int = 1
    max_col: int = 1


@dataclass
class WorksheetProperties(DocumentBaseModel):
    show_gridlines: bool = True
    show_headings: bool = True
    tab_color: Optional[str] = None  # Hex color


# ============================================================
# Cell, Row, Column
# ============================================================

@dataclass
class Cell(DocumentBaseModel):
    row: int
    col: int
    value: Any = None
    formula: Optional[str] = None
    style_id: Optional[int] = None
    hyperlink: Optional[str] = None
    comment: Optional[str] = None

    @property
    def coordinate(self) -> str:
        return f"{self._col_to_letter(self.col)}{self.row}"

    @staticmethod
    def _col_to_letter(col: int) -> str:
        """Convert column number to Excel-style letters (1 → A)."""
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

    def get_or_create_cell(self, col: int) -> Cell:
        if col not in self.cells:
            self.cells[col] = Cell(row=self.index, col=col)
        return self.cells[col]


@dataclass
class Column(DocumentBaseModel):
    index: int
    width: Optional[float] = None
    hidden: bool = False


# ============================================================
# Ranges
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
    scope: Optional[str] = None  # workbook or sheet-level


# ============================================================
# Worksheet
# ============================================================

@dataclass
class Worksheet(DocumentBaseModel):
    name: str
    rows: Dict[int, Row] = field(default_factory=dict)
    columns: Dict[int, Column] = field(default_factory=dict)
    merged_cells: List[MergedCellRange] = field(default_factory=list)
    named_ranges: List[NamedRange] = field(default_factory=list)
    properties: WorksheetProperties = field(default_factory=WorksheetProperties)
    dimensions: SheetDimensions = field(default_factory=SheetDimensions)

    def get_row(self, index: int) -> Row:
        if index not in self.rows:
            self.rows[index] = Row(index=index)
        return self.rows[index]

    def get_cell(self, row: int, col: int) -> Cell:
        return self.get_row(row).get_or_create_cell(col)

    def merge_cells(self, min_row: int, min_col: int, max_row: int, max_col: int):
        self.merged_cells.append(
            MergedCellRange(
                min_row=min_row, max_row=max_row,
                min_col=min_col, max_col=max_col
            )
        )


# ============================================================
# Workbook
# ============================================================

@dataclass
class Workbook(BaseDocument):
    kind: DocumentStandard = DocumentStandard.GENERIC
    properties: WorkbookProperties = field(default_factory=WorkbookProperties)
    sheets: List[Worksheet] = field(default_factory=list)
    shared_strings: SharedStrings = field(default_factory=SharedStrings)
    relationships: RelationshipCollection = field(default_factory=RelationshipCollection)
    named_ranges: List[NamedRange] = field(default_factory=list)

    def add_sheet(self, name: str) -> Worksheet:
        sheet = Worksheet(name=name)
        self.sheets.append(sheet)
        return sheet









# ============================================================
# Stylesheet Models (Full Excel-Grade)
# ============================================================

# ------------------------------------------------------------
# Number Formats
# ------------------------------------------------------------

@dataclass
class NumberFormat(DocumentBaseModel):
    """
    Custom number format, e.g. "#,##0.00", "dd/mm/yyyy"
    Excel has built-in IDs 0–163; customs start at 164+.
    """
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
# Font
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
    color: Optional[str] = None         # hex
    charset: Optional[int] = None
    family: Optional[int] = None
    scheme: Optional[str] = None        # "minor", "major"


@dataclass
class FontCollection(DocumentBaseModel):
    fonts: List[Font] = field(default_factory=list)

    def register(self, font: Font) -> int:
        self.fonts.append(font)
        return len(self.fonts) - 1


# ------------------------------------------------------------
# Fill
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
    position: float      # 0.0 → 1.0
    color: str           # hex color


@dataclass
class GradientFill(DocumentBaseModel):
    degree: Optional[float] = None           # linear gradient
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
    color: Optional[str] = None  # hex color


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
    text_rotation: int = 0      # -90 to 90


# ------------------------------------------------------------
# Protection
# ------------------------------------------------------------

@dataclass
class Protection(DocumentBaseModel):
    locked: bool = True
    hidden: bool = False


# ------------------------------------------------------------
# Cell Format (xf)
# ------------------------------------------------------------

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
# Cell Styles (styleXfs)
# ------------------------------------------------------------

@dataclass
class CellStyle(DocumentBaseModel):
    name: str
    builtin_id: Optional[int] = None
    xf_id: Optional[int] = None


@dataclass
class CellStyleCollection(DocumentBaseModel):
    styles: List[CellStyle] = field(default_factory=list)

    def register(self, style: CellStyle) -> int:
        self.styles.append(style)
        return len(self.styles) - 1


# ------------------------------------------------------------
# DXF (differential formats)
# Used in Conditional Formatting & Table Styles
# ------------------------------------------------------------

@dataclass
class DifferentialFormat(DocumentBaseModel):
    font: Optional[Font] = None
    fill: Optional[Fill] = None
    border: Optional[Border] = None
    alignment: Optional[Alignment] = None
    number_format: Optional[NumberFormat] = None


@dataclass
class DifferentialFormatCollection(DocumentBaseModel):
    dxfs: List[DifferentialFormat] = field(default_factory=list)

    def register(self, dxf: DifferentialFormat) -> int:
        self.dxfs.append(dxf)
        return len(self.dxfs) - 1


# ------------------------------------------------------------
# Table Styles
# ------------------------------------------------------------

@dataclass
class TableStyleElement(DocumentBaseModel):
    type: str                  # e.g. "wholeTable", "headerRow", "totalRow", ...
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


@dataclass
class TableStyleCollection(DocumentBaseModel):
    styles: List[ExcelTableStyle] = field(default_factory=list)

    def register(self, style: ExcelTableStyle) -> int:
        self.styles.append(style)
        return len(self.styles) - 1


# ------------------------------------------------------------
# Master Stylesheet Object
# ------------------------------------------------------------

@dataclass
class Stylesheet(DocumentBaseModel):
    number_formats: NumberFormatCollection = field(default_factory=NumberFormatCollection)
    fonts: FontCollection = field(default_factory=FontCollection)
    fills: FillCollection = field(default_factory=FillCollection)
    borders: BorderCollection = field(default_factory=BorderCollection)
    cell_formats: CellFormatCollection = field(default_factory=CellFormatCollection)
    cell_styles: CellStyleCollection = field(default_factory=CellStyleCollection)
    dxfs: DifferentialFormatCollection = field(default_factory=DifferentialFormatCollection)
    table_styles: TableStyleCollection = field(default_factory=TableStyleCollection)







# ============================================================
# Tables, AutoFilter, and Structured References
# ============================================================

from enum import Enum


# ------------------------------------------------------------
# AutoFilter System
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
    ref: Optional[str] = None                # range string, e.g. "A1:D10"
    filter_columns: List[FilterColumn] = field(default_factory=list)
    sort_state: Optional[Any] = None         # placeholder for future use


# ------------------------------------------------------------
# Table Model
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

    def get_value(self, column_id: int) -> Any:
        return self.values.get(column_id)

    def set_value(self, column_id: int, value: Any):
        self.values[column_id] = value


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
    ref: Optional[str] = None                  # range reference
    header_row_count: int = 1
    totals_row_count: int = 0
    columns: List[TableColumn] = field(default_factory=list)
    rows: List[ExcelTableRow] = field(default_factory=list)
    auto_filter: Optional[AutoFilter] = None
    table_style_info: TableStyleInfo = field(default_factory=TableStyleInfo)

    def get_column_by_name(self, name: str) -> Optional[TableColumn]:
        for col in self.columns:
            if col.name == name:
                return col
        return None

    def add_column(self, name: str) -> TableColumn:
        next_id = len(self.columns) + 1
        col = TableColumn(id=next_id, name=name)
        self.columns.append(col)
        return col

    def add_row(self, values: Dict[str, Any]) -> ExcelTableRow:
        col_map = {c.name: c.id for c in self.columns}
        row = ExcelTableRow(index=len(self.rows) + 1)
        for cname, val in values.items():
            if cname in col_map:
                row.set_value(col_map[cname], val)
        self.rows.append(row)
        return row


# ------------------------------------------------------------
# Table Collection (per worksheet)
# ------------------------------------------------------------

@dataclass
class TableCollection(DocumentBaseModel):
    tables: List[Table] = field(default_factory=list)

    def add(self, table: Table):
        self.tables.append(table)

    def find(self, name: str) -> Optional[Table]:
        for t in self.tables:
            if t.name == name:
                return t
        return None



# ============================================================
# Conditional Formatting (CF)
# ============================================================

from enum import Enum


# ------------------------------------------------------------
# CF Base Components
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
    type: str                   # "num", "percentile", "formula", "min", "max"
    value: Optional[Any] = None


# ------------------------------------------------------------
# Color Scale
# ------------------------------------------------------------

@dataclass
class ColorScale(DocumentBaseModel):
    values: List[CFValueObject] = field(default_factory=list)   # min/mid/max
    colors: List[str] = field(default_factory=list)             # hex colors


# ------------------------------------------------------------
# Data Bar
# ------------------------------------------------------------

@dataclass
class DataBar(DocumentBaseModel):
    min_value: CFValueObject = field(default_factory=lambda: CFValueObject(type="min"))
    max_value: CFValueObject = field(default_factory=lambda: CFValueObject(type="max"))
    color: str = "#638EC6"
    show_value: bool = True
    border: bool = False
    gradient: bool = True


# ------------------------------------------------------------
# Icon Set
# ------------------------------------------------------------

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
    operator: Optional[str] = None     # >= or >
    icon_id: int = 0


@dataclass
class IconSet(DocumentBaseModel):
    icon_set_type: IconSetType = IconSetType.THREE_TRAFFIC_LIGHTS
    criteria: List[IconCriterion] = field(default_factory=list)
    show_value: bool = True
    reverse: bool = False


# ------------------------------------------------------------
# CF Rule
# ------------------------------------------------------------

@dataclass
class CFRule(DocumentBaseModel):
    type: CFType
    priority: int
    dxf_id: Optional[int] = None
    stop_if_true: bool = False

    operator: Optional[CFOperator] = None   # for cellIs
    formula: List[str] = field(default_factory=list)

    color_scale: Optional[ColorScale] = None
    data_bar: Optional[DataBar] = None
    icon_set: Optional[IconSet] = None


# ------------------------------------------------------------
# CF Region (range + rule list)
# ------------------------------------------------------------

@dataclass
class ConditionalFormatting(DocumentBaseModel):
    ref: str  # target range: "A1:D20"
    rules: List[CFRule] = field(default_factory=list)

    def add_rule(self, rule: CFRule):
        self.rules.append(rule)


# ------------------------------------------------------------
# CF Collection per Worksheet
# ------------------------------------------------------------

@dataclass
class ConditionalFormattingCollection(DocumentBaseModel):
    items: List[ConditionalFormatting] = field(default_factory=list)

    def add(self, cf: ConditionalFormatting):
        self.items.append(cf)

    def for_range(self, ref: str) -> Optional[ConditionalFormatting]:
        for c in self.items:
            if c.ref == ref:
                return c
        return None


# ============================================================
# Formulas, Defined Names, Shared Formulas, External Links
# ============================================================

from enum import Enum


# ------------------------------------------------------------
# Formula Token System (Simple AST-Lite Model)
# ------------------------------------------------------------

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
    def from_string(cls, formula: str):
        # NOTE: We do NOT parse formula here (not an interpreter)
        # We store the formula raw and let parser be external or pluggable.
        return cls(tokens=[FormulaToken(type=FormulaTokenType.OPERAND, value=formula)])

    def to_string(self) -> str:
        # For now: round‑trip raw formula
        if len(self.tokens) == 1 and self.tokens[0].type == FormulaTokenType.OPERAND:
            return str(self.tokens[0].value)
        # Otherwise join token values
        return "".join(t.value for t in self.tokens)


# ------------------------------------------------------------
# Shared Formula System
# ------------------------------------------------------------

@dataclass
class SharedFormula(DocumentBaseModel):
    shared_index: int                  # Excel's si attribute
    ref: str                           # Target area: "A1:C10"
    formula: FormulaAST                # Base formula


@dataclass
class SharedFormulaCollection(DocumentBaseModel):
    items: Dict[int, SharedFormula] = field(default_factory=dict)

    def add(self, shared_formula: SharedFormula):
        self.items[shared_formula.shared_index] = shared_formula

    def get(self, shared_index: int) -> Optional[SharedFormula]:
        return self.items.get(shared_index)


# ------------------------------------------------------------
# Defined Names (Workbook-Scoped or Worksheet-Scoped)
# ------------------------------------------------------------

@dataclass
class DefinedName(DocumentBaseModel):
    name: str
    formula: str                                # raw formula or reference
    local_sheet_id: Optional[int] = None        # None => workbook-scope
    comment: Optional[str] = None
    hidden: bool = False
    function: bool = False                      # is this a user-defined function?
    vb_procedure: bool = False                  # legacy VBA linkage

    @property
    def is_global(self) -> bool:
        return self.local_sheet_id is None


@dataclass
class DefinedNameCollection(DocumentBaseModel):
    items: List[DefinedName] = field(default_factory=list)

    def add(self, dn: DefinedName):
        self.items.append(dn)

    def find(self, name: str, sheet_id: Optional[int] = None) -> Optional[DefinedName]:
        """
        Spec-accurate name resolution:
        1) Look for worksheet-scope name if sheet_id provided
        2) Fallback to workbook-scope name
        """
        # sheet-scope
        if sheet_id is not None:
            for dn in self.items:
                if dn.name == name and dn.local_sheet_id == sheet_id:
                    return dn

        # workbook-scope
        for dn in self.items:
            if dn.name == name and dn.local_sheet_id is None:
                return dn
        return None


# ------------------------------------------------------------
# External Workbooks / Links
# ------------------------------------------------------------

@dataclass
class ExternalReference(DocumentBaseModel):
    workbook_name: str                       # "Book2.xlsx"
    sheet_name: str                          # "Sheet1"
    ref: str                                 # "A1" or "A1:B10"


@dataclass
class ExternalLink(DocumentBaseModel):
    id: int
    file_path: str
    references: List[ExternalReference] = field(default_factory=list)


@dataclass
class ExternalLinkCollection(DocumentBaseModel):
    items: List[ExternalLink] = field(default_factory=list)

    def add(self, link: ExternalLink):
        self.items.append(link)

    def get_by_id(self, id: int) -> Optional[ExternalLink]:
        for link in self.items:
            if link.id == id:
                return link
        return None


# ------------------------------------------------------------
# Formula Handling inside Cell
# ------------------------------------------------------------

@dataclass
class CellFormula(DocumentBaseModel):
    text: str
    ast: Optional[FormulaAST] = None
    shared_index: Optional[int] = None          # si attribute
    array: bool = False                         # array formula flag

    @classmethod
    def create(cls, formula_text: str, shared_index: Optional[int] = None):
        return cls(text=formula_text,
                   ast=FormulaAST.from_string(formula_text),
                   shared_index=shared_index)

    def get(self) -> str:
        if self.ast:
            return self.ast.to_string()
        return self.text


# ============================================================
# Phase 6 — Workbook/Worksheet Features
# ============================================================

from enum import Enum


# ------------------------------------------------------------
# Data Validation
# ------------------------------------------------------------

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
    ref: str                                      # "A1", "A1:A20"
    rule: DataValidationRule


@dataclass
class DataValidationCollection(DocumentBaseModel):
    items: List[DataValidation] = field(default_factory=list)

    def add(self, dv: DataValidation):
        self.items.append(dv)


# ------------------------------------------------------------
# Hyperlinks
# ------------------------------------------------------------

@dataclass
class Hyperlink(DocumentBaseModel):
    ref: str                                      # target cell(s)
    target: str                                   # URL or internal reference
    tooltip: Optional[str] = None
    display: Optional[str] = None


@dataclass
class HyperlinkCollection(DocumentBaseModel):
    items: List[Hyperlink] = field(default_factory=list)

    def add(self, hyperlink: Hyperlink):
        self.items.append(hyperlink)


# ------------------------------------------------------------
# Comments (Note: In Excel → Comments + Threaded Comments)
# ------------------------------------------------------------

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
    def from_string(cls, text: str):
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

    def add_author(self, name: str) -> int:
        index = len(self.authors)
        self.authors.append(Author(name=name))
        return index

    def add_comment(self, ref: str, author_id: int, text: CommentText):
        self.comments.append(Comment(ref=ref, author_id=author_id, text=text))


# ------------------------------------------------------------
# Threaded Comments (Excel Modern Comments)
# ------------------------------------------------------------

@dataclass
class ThreadedComment(DocumentBaseModel):
    ref: str
    text: str
    author: str
    date: Optional[str] = None


@dataclass
class ThreadedCommentCollection(DocumentBaseModel):
    items: List[ThreadedComment] = field(default_factory=list)

    def add(self, tc: ThreadedComment):
        self.items.append(tc)


# ------------------------------------------------------------
# Sheet Properties
# ------------------------------------------------------------

@dataclass
class SheetProperties(DocumentBaseModel):
    tab_color: Optional[str] = None
    filter_mode: bool = False
    published: bool = True


# ------------------------------------------------------------
# Sheet Protection
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# Page Setup
# ------------------------------------------------------------

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
    paper_size: int = 9                # A4
    fit_to_width: Optional[int] = None
    fit_to_height: Optional[int] = None


# ------------------------------------------------------------
# Calculation Chain (formula dependency order)
# ------------------------------------------------------------

@dataclass
class CalcChainEntry(DocumentBaseModel):
    sheet_id: int
    ref: str                 # "A1"
    array: bool = False


@dataclass
class CalculationChain(DocumentBaseModel):
    items: List[CalcChainEntry] = field(default_factory=list)

    def add(self, entry: CalcChainEntry):
        self.items.append(entry)


# ------------------------------------------------------------
# Rich Text (inline cell text)
# ------------------------------------------------------------

@dataclass
class RichTextRun(DocumentBaseModel):
    text: str
    bold: bool = False
    italic: bool = False
    underline: bool = False
    color: Optional[str] = None
    font_name: Optional[str] = None
    font_size: Optional[float] = None


@dataclass
class RichText(DocumentBaseModel):
    runs: List[RichTextRun] = field(default_factory=list)

    @classmethod
    def from_string(cls, text: str):
        return cls(runs=[RichTextRun(text=text)])


# ------------------------------------------------------------
# Pivot Tables (minimal yet complete)
# ------------------------------------------------------------

@dataclass
class PivotField(DocumentBaseModel):
    name: str
    orientation: str        # row, column, data, page
    subtotal: Optional[str] = None


@dataclass
class PivotCacheReference(DocumentBaseModel):
    sheet: str
    ref: str                # source range


@dataclass
class PivotCache(DocumentBaseModel):
    id: int
    source: PivotCacheReference


@dataclass
class PivotTable(DocumentBaseModel):
    name: str
    location: str           # top-left cell
    cache_id: int
    fields: List[PivotField] = field(default_factory=list)


@dataclass
class PivotCacheCollection(DocumentBaseModel):
    items: List[PivotCache] = field(default_factory=list)

    def add(self, cache: PivotCache):
        self.items.append(cache)


@dataclass
class PivotTableCollection(DocumentBaseModel):
    items: List[PivotTable] = field(default_factory=list)

    def add(self, pt: PivotTable):
        self.items.append(pt)
