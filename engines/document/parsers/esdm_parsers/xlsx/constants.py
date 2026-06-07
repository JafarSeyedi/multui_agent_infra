# engines/document/parsers/spreadsheet_parser/xlsx/constants.py
"""
Mapping constants between openpyxl and ESDM models.
"""
from ....models.esdm_models import BorderStyle
from ....models.esdm_models import CFOperator
from ....models.esdm_models import CFType
from ....models.esdm_models import DataValidationOperator
from ....models.esdm_models import DataValidationType
from ....models.esdm_models import DynamicFilterType
from ....models.esdm_models import FilterOperator
from ....models.esdm_models import FontUnderline
from ....models.esdm_models import HorizontalAlign
from ....models.esdm_models import IconSetType
from ....models.esdm_models import Orientation
from ....models.esdm_models import PatternType
from ....models.esdm_models import VerticalAlign

# ──────────────────────────────────────────────
# FONT UNDERLINE
# ──────────────────────────────────────────────
OPENPYXL_UNDERLINE_TO_ESDM = {
    "single": FontUnderline.SINGLE,
    "double": FontUnderline.DOUBLE,
    "singleAccounting": FontUnderline.SINGLE_ACCOUNTING,
    "doubleAccounting": FontUnderline.DOUBLE_ACCOUNTING,
    None: FontUnderline.NONE,
    "none": FontUnderline.NONE,
}

# ──────────────────────────────────────────────
# PATTERN FILL
# ──────────────────────────────────────────────
OPENPYXL_FILL_PATTERN_TO_ESDM = {
    "none": PatternType.NONE,
    "solid": PatternType.SOLID,
    "darkGray": PatternType.DARK_GRAY,
    "mediumGray": PatternType.MEDIUM_GRAY,
    "lightGray": PatternType.LIGHT_GRAY,
    "gray125": PatternType.GRAY_125,
    "gray0625": PatternType.GRAY_0625,
    "darkDown": PatternType.DARK_DOWN,
    "darkUp": PatternType.DARK_UP,
    "darkHorizontal": PatternType.DARK_HORIZ,
    "darkVertical": PatternType.DARK_VERT,
    "darkGrid": PatternType.DARK_GRID,
    "darkTrellis": PatternType.DARK_TRELLIS,
    "lightDown": PatternType.LIGHT_DOWN,
    "lightUp": PatternType.LIGHT_UP,
    "lightHorizontal": PatternType.LIGHT_HORIZ,
    "lightVertical": PatternType.LIGHT_VERT,
    "lightGrid": PatternType.LIGHT_GRID,
    "lightTrellis": PatternType.LIGHT_TRELLIS,
}

# ──────────────────────────────────────────────
# BORDER STYLES
# ──────────────────────────────────────────────
OPENPYXL_BORDER_STYLE_TO_ESDM = {
    "thin": BorderStyle.THIN,
    "medium": BorderStyle.MEDIUM,
    "thick": BorderStyle.THICK,
    "dotted": BorderStyle.DOTTED,
    "dashed": BorderStyle.DASHED,
    "double": BorderStyle.DOUBLE,
    "hair": BorderStyle.HAIR,
    "dashDot": BorderStyle.DASH_DOT,
    "dashDotDot": BorderStyle.DASH_DOT_DOT,
    "mediumDashed": BorderStyle.MEDIUM_DASH,
    "mediumDashDot": BorderStyle.MEDIUM_DASH_DOT,
    "mediumDashDotDot": BorderStyle.MEDIUM_DASH_DOT_DOT,
    "slantDashDot": BorderStyle.SLANT_DASH_DOT,
    None: BorderStyle.NONE,
    "none": BorderStyle.NONE,
}

# ──────────────────────────────────────────────
# ALIGNMENT
# ──────────────────────────────────────────────
OPENPYXL_HORIZONTAL_TO_ESDM = {
    "general": HorizontalAlign.GENERAL,
    "left": HorizontalAlign.LEFT,
    "right": HorizontalAlign.RIGHT,
    "center": HorizontalAlign.CENTER,
    "justify": HorizontalAlign.JUSTIFY,
    "fill": HorizontalAlign.FILL,
    "centerContinuous": HorizontalAlign.CENTER_CONTINUOUS,
    "distributed": HorizontalAlign.DISTRIBUTED,
}

OPENPYXL_VERTICAL_TO_ESDM = {
    "top": VerticalAlign.TOP,
    "center": VerticalAlign.CENTER,
    "bottom": VerticalAlign.BOTTOM,
    "justify": VerticalAlign.JUSTIFY,
    "distributed": VerticalAlign.DISTRIBUTED,
}

# ──────────────────────────────────────────────
# NUMBER FORMAT BUILT‑IN IDs (partial, common ones)
# ──────────────────────────────────────────────
BUILTIN_NUMBER_FORMATS = {
    0: "General",
    1: "0",
    2: "0.00",
    3: "#,##0",
    4: "#,##0.00",
    9: "0%",
    10: "0.00%",
    11: "0.00E+00",
    12: "# ?/?",
    13: "# ??/??",
    14: "mm-dd-yy",
    15: "d-mmm-yy",
    16: "d-mmm",
    17: "mmm-yy",
    18: "h:mm AM/PM",
    19: "h:mm:ss AM/PM",
    20: "h:mm",
    21: "h:mm:ss",
    22: "m/d/yy h:mm",
    37: "#,##0 ;(#,##0)",
    38: "#,##0 ;[Red](#,##0)",
    39: "#,##0.00;(#,##0.00)",
    40: "#,##0.00;[Red](#,##0.00)",
    45: "mm:ss",
    46: "[h]:mm:ss",
    47: "mmss.0",
    48: "##0.0E+0",
    49: "@",
}

# ──────────────────────────────────────────────
# CONDITIONAL FORMATTING & FILTERS
# ──────────────────────────────────────────────
DYNAMIC_FILTER_TYPE_MAP = {
    "aboveAverage": DynamicFilterType.ABOVE_AVERAGE,
    "belowAverage": DynamicFilterType.BELOW_AVERAGE,
    "lastMonth": DynamicFilterType.LAST_MONTH,
    "lastQuarter": DynamicFilterType.LAST_QUARTER,
    "lastWeek": DynamicFilterType.LAST_WEEK,
    "lastYear": DynamicFilterType.LAST_YEAR,
    "nextMonth": DynamicFilterType.NEXT_MONTH,
    "nextQuarter": DynamicFilterType.NEXT_QUARTER,
    "nextWeek": DynamicFilterType.NEXT_WEEK,
    "nextYear": DynamicFilterType.NEXT_YEAR,
    "thisMonth": DynamicFilterType.THIS_MONTH,
    "thisQuarter": DynamicFilterType.THIS_QUARTER,
    "thisWeek": DynamicFilterType.THIS_WEEK,
    "thisYear": DynamicFilterType.THIS_YEAR,
    "today": DynamicFilterType.TODAY,
    "tomorrow": DynamicFilterType.TOMORROW,
    "yearToDate": DynamicFilterType.YEAR_TO_DATE,
    "yesterday": DynamicFilterType.YESTERDAY,
}

FILTER_OPERATOR_MAP = {
    "equal": FilterOperator.EQUAL,
    "notEqual": FilterOperator.NOT_EQUAL,
    "greaterThan": FilterOperator.GREATER_THAN,
    "lessThan": FilterOperator.LESS_THAN,
    "greaterThanOrEqual": FilterOperator.GREATER_OR_EQUAL,
    "lessThanOrEqual": FilterOperator.LESS_OR_EQUAL,
}

CF_TYPE_MAP = {
    "cellIs": CFType.CELL_IS,
    "expression": CFType.EXPRESSION,
    "colorScale": CFType.COLOR_SCALE,
    "dataBar": CFType.DATA_BAR,
    "iconSet": CFType.ICON_SET,
    "top10": CFType.TOP_10,
    "uniqueValues": CFType.UNIQUE_VALUES,
    "duplicateValues": CFType.DUPLICATE_VALUES,
    "containsText": CFType.CONTAINS_TEXT,
    "notContainsText": CFType.NOT_CONTAINS_TEXT,
    "beginsWith": CFType.BEGINS_WITH,
    "endsWith": CFType.ENDS_WITH,
    "containsBlanks": CFType.CONTAINS_BLANKS,
    "notContainsBlanks": CFType.NOT_CONTAINS_BLANKS,
    "containsErrors": CFType.CONTAINS_ERRORS,
    "notContainsErrors": CFType.NOT_CONTAINS_ERRORS,
    "timePeriod": CFType.TIME_PERIOD,
    "aboveAverage": CFType.ABOVE_AVERAGE,
}

CF_OPERATOR_MAP = {
    "lessThan": CFOperator.LESS_THAN,
    "lessThanOrEqual": CFOperator.LESS_OR_EQUAL,
    "greaterThan": CFOperator.GREATER_THAN,
    "greaterThanOrEqual": CFOperator.GREATER_OR_EQUAL,
    "equal": CFOperator.EQUAL,
    "notEqual": CFOperator.NOT_EQUAL,
    "between": CFOperator.BETWEEN,
    "notBetween": CFOperator.NOT_BETWEEN,
}

DATA_VALIDATION_TYPE_MAP = {
    "whole": DataValidationType.WHOLE,
    "decimal": DataValidationType.DECIMAL,
    "list": DataValidationType.LIST,
    "date": DataValidationType.DATE,
    "time": DataValidationType.TIME,
    "textLength": DataValidationType.TEXT_LENGTH,
    "custom": DataValidationType.CUSTOM,
}

DATA_VALIDATION_OPERATOR_MAP = {
    "between": DataValidationOperator.BETWEEN,
    "notBetween": DataValidationOperator.NOT_BETWEEN,
    "lessThan": DataValidationOperator.LESS_THAN,
    "greaterThan": DataValidationOperator.GREATER_THAN,
    "equal": DataValidationOperator.EQUAL,
    "notEqual": DataValidationOperator.NOT_EQUAL,
}

ICON_SET_MAP = {
    "3Arrows": IconSetType.THREE_ARROWS,
    "3ArrowsGray": IconSetType.THREE_ARROWS_GRAY,
    "3TrafficLights1": IconSetType.THREE_TRAFFIC_LIGHTS,
    "3TrafficLights2": IconSetType.THREE_TRAFFIC_LIGHTS2,
    "3Symbols": IconSetType.THREE_SYMBOLS,
    "3Symbols2": IconSetType.THREE_SYMBOLS2,
    "4Rating": IconSetType.FOUR_RATINGS,
    "5Arrows": IconSetType.FIVE_ARROWS,
    "5ArrowsGray": IconSetType.FIVE_ARROWS_GRAY,
    "5Rating": IconSetType.FIVE_RATINGS,
}

PAGE_ORIENTATION_MAP = {
    "portrait": Orientation.PORTRAIT,
    "landscape": Orientation.LANDSCAPE,
}
