# engines/document/parsers/spreadsheet_parser/xlsx/tables_builder.py
"""
Complete XML → ESDM builders for:
- Excel tables
- AutoFilters
- Conditional formatting
"""

from xml.etree.ElementTree import Element
from typing import List, Optional, Dict
from .namespaces import MAIN, REL
from .utils import (
    xml_find, xml_findall, xml_attr, xml_text, xml_bool, xml_int, xml_float,
    color_hex_from_xml, parse_range, col_letter_to_index,
)
from engines.document.models.esdm_models import (
    Table, TableColumn, TableStyleInfo,
    AutoFilter, FilterColumn, Filters, CustomFilter, DynamicFilterType, FilterOperator,
    ConditionalFormatting, CFRule, CFType, CFOperator, CFValueObject,
    ColorScale, DataBar, IconSet, IconSetType, IconCriterion,
)
from .constants import (
    DYNAMIC_FILTER_TYPE_MAP, FILTER_OPERATOR_MAP,
    CF_TYPE_MAP, CF_OPERATOR_MAP, ICON_SET_MAP,
)

NS = {"": MAIN, "r": REL}

# ────────────────────────────────────────
# TABLE
# ────────────────────────────────────────
def build_table(table_elem: Element) -> Table:
    _id = xml_int(table_elem, "id")
    name = xml_attr(table_elem, "name", "")
    display_name = xml_attr(table_elem, "displayName")
    ref = xml_attr(table_elem, "ref")
    header_count = xml_int(table_elem, "headerRowCount", 1)
    totals_count = xml_int(table_elem, "totalsRowCount", 0)

    table = Table(
        id=_id,
        name=name,
        display_name=display_name or name,
        ref=ref,
        header_row_count=header_count,
        totals_row_count=totals_count,
    )

    # Columns
    cols_elem = xml_find(table_elem, "tableColumns", NS)
    if cols_elem is not None:
        for tc in xml_findall(cols_elem, "tableColumn", NS):
            col = TableColumn(
                id=xml_int(tc, "id"),
                name=xml_attr(tc, "name", ""),
                totals_row_function=xml_attr(tc, "totalsRowFunction"),
                totals_row_label=xml_attr(tc, "totalsRowLabel"),
                calculated_column_formula=xml_attr(tc, "calculatedColumnFormula"),
            )
            table.columns.append(col)

    # AutoFilter inside table
    af_elem = xml_find(table_elem, "autoFilter", NS)
    if af_elem is not None:
        table.auto_filter = build_auto_filter(af_elem)

    # Table style info
    style_elem = xml_find(table_elem, "tableStyleInfo", NS)
    if style_elem is not None:
        table.table_style_info = TableStyleInfo(
            name=xml_attr(style_elem, "name", "TableStyleMedium9"),
            show_first_column=xml_bool(style_elem, "showFirstColumn"),
            show_last_column=xml_bool(style_elem, "showLastColumn"),
            show_row_stripes=xml_bool(style_elem, "showRowStripes", True),
            show_column_stripes=xml_bool(style_elem, "showColumnStripes"),
        )
    return table

def build_all_tables(tables_root: Element) -> List[Table]:
    """Build all <table> elements from a workbook's tables.xml part (if any)."""
    # Typically each table is in a separate file, but a "tables.xml" isn't standard.
    # In OOXML, each table is in xl/tables/tableN.xml. We'll handle it in the parser.
    # For now, if you pass the root of a tableN.xml, use build_table().
    return [build_table(tables_root)] if tables_root.tag.endswith("table") else []

# ────────────────────────────────────────
# AUTO FILTER
# ────────────────────────────────────────
def build_auto_filter(af_elem: Element) -> AutoFilter:
    ref = xml_attr(af_elem, "ref")
    af = AutoFilter(ref=ref)
    for fc in xml_findall(af_elem, "filterColumn", NS):
        col_id = xml_int(fc, "colId")
        filter_col = FilterColumn(col_id=col_id)

        filters_el = xml_find(fc, "filters", NS)
        if filters_el is not None:
            vals = [f.get("val", "") for f in xml_findall(filters_el, "filter", NS)]
            blank = xml_bool(filters_el, "blank")
            filter_col.filters = Filters(values=vals, blank=blank)

        custom_filters_el = xml_find(fc, "customFilters", NS)
        if custom_filters_el is not None:
            for cf in xml_findall(custom_filters_el, "customFilter", NS):
                op_str = xml_attr(cf, "operator", "equal")
                operator = FILTER_OPERATOR_MAP.get(op_str, FilterOperator.EQUAL)
                filter_col.custom_filters.append(
                    CustomFilter(operator=operator, value=xml_attr(cf, "val", ""))
                )

        dyn = xml_find(fc, "dynamicFilter", NS)
        if dyn is not None:
            dt = xml_attr(dyn, "type", "aboveAverage")
            filter_col.dynamic_filter = DYNAMIC_FILTER_TYPE_MAP.get(dt, DynamicFilterType.ABOVE_AVERAGE)

        af.filter_columns.append(filter_col)
    return af

# ────────────────────────────────────────
# CONDITIONAL FORMATTING
# ────────────────────────────────────────
def build_conditional_formatting(ws_root: Element) -> List[ConditionalFormatting]:
    """Extract all conditional formatting from worksheet XML."""
    cf_list = []
    for cf_elem in xml_findall(ws_root, "conditionalFormatting", NS):
        ref = xml_attr(cf_elem, "sqref", "")
        cf_obj = ConditionalFormatting(ref=ref)
        for rule_elem in xml_findall(cf_elem, "cfRule", NS):
            rule = _build_cf_rule(rule_elem)
            cf_obj.rules.append(rule)
        cf_list.append(cf_obj)
    return cf_list

def _build_cf_rule(rule_elem: Element) -> CFRule:
    rule_type = CF_TYPE_MAP.get(xml_attr(rule_elem, "type", ""), CFType.CELL_IS)
    priority = xml_int(rule_elem, "priority", 1)
    stop = xml_bool(rule_elem, "stopIfTrue")
    dxf_id = xml_attr(rule_elem, "dxfId")
    dxf_id = int(dxf_id) if dxf_id else None

    rule = CFRule(
        type=rule_type,
        priority=priority,
        stop_if_true=stop,
        dxf_id=dxf_id,
    )

    op_str = xml_attr(rule_elem, "operator")
    if op_str:
        rule.operator = CF_OPERATOR_MAP.get(op_str)

    formulas = [xml_text(f) for f in xml_findall(rule_elem, "formula", NS)]
    rule.formula = formulas

    # Color scale
    cs = xml_find(rule_elem, "colorScale", NS)
    if cs is not None:
        rule.color_scale = _build_color_scale(cs)

    # Data bar
    db = xml_find(rule_elem, "dataBar", NS)
    if db is not None:
        rule.data_bar = _build_data_bar(db)

    # Icon set
    iset = xml_find(rule_elem, "iconSet", NS)
    if iset is not None:
        rule.icon_set = _build_icon_set(iset)

    return rule

def _build_color_scale(cs: Element) -> ColorScale:
    values = []
    colors = []
    for vo in xml_findall(cs, "cfvo", NS):
        values.append(CFValueObject(type=vo.get("type", ""), value=vo.get("val")))
    for col in xml_findall(cs, "color", NS):
        colors.append(color_hex_from_xml(col, NS) or "")
    return ColorScale(values=values, colors=colors)

def _build_data_bar(db: Element) -> DataBar:
    vos = xml_findall(db, "cfvo", NS)
    min_val = CFValueObject()
    max_val = CFValueObject()
    if len(vos) >= 1:
        min_val = CFValueObject(type=vos[0].get("type", ""), value=vos[0].get("val"))
    if len(vos) >= 2:
        max_val = CFValueObject(type=vos[1].get("type", ""), value=vos[1].get("val"))
    color_el = xml_find(db, "color", NS)
    return DataBar(
        min_value=min_val,
        max_value=max_val,
        color=color_hex_from_xml(color_el, NS) if color_el is not None else "#638EC6",
        show_value=xml_bool(db, "showValue", True),
    )

def _build_icon_set(iset: Element) -> IconSet:
    icon_type_str = xml_attr(iset, "iconSet", "3TrafficLights1")
    icon_type = ICON_SET_MAP.get(icon_type_str, IconSetType.THREE_TRAFFIC_LIGHTS)
    show_value = xml_bool(iset, "showValue", True)
    reverse = xml_bool(iset, "reverse")
    criteria = []
    for vo in xml_findall(iset, "cfvo", NS):
        criteria.append(IconCriterion(
            type=vo.get("type", ""),
            value=vo.get("val"),
            operator=vo.get("gte"),
            icon_id=int(vo.get("iconSet", "0")) if vo.get("iconSet") else 0,
        ))
    return IconSet(
        icon_set_type=icon_type,
        criteria=criteria,
        show_value=show_value,
        reverse=reverse,
    )