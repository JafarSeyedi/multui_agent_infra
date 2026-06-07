# engines/document/parsers/spreadsheet_parser/xlsx/charts_builder.py
"""
Complete Chart XML parser → ChartContent with all explicit fields.
No XML leakage – every field is a clean Python type.
"""
from xml.etree.ElementTree import Element

from ....models.usdm_models import ChartAxisContent
from ....models.usdm_models import ChartContent
from ....models.usdm_models import ChartSeriesContent
from .utils import xml_attr
from .utils import xml_find
from .utils import xml_findall
from .utils import xml_float
from .utils import xml_int
from .utils import xml_text

C = "http://schemas.openxmlformats.org/drawingml/2006/chart"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
NS = {"c": C, "a": A}


def parse_chart(chart_xml: Element) -> ChartContent:
    """Return a fully described ChartContent from the chartSpace."""
    chart_el = xml_find(chart_xml, "c:chart", NS)
    if chart_el is None:
        return ChartContent(chart_type="unknown")

    chart_type, type_el = _identify_type(chart_el)
    chart = ChartContent(chart_type=chart_type)

    if type_el is not None:
        chart.grouping = xml_attr(type_el, "grouping")
        chart.direction = xml_attr(type_el, "barDir")

    chart.title = _extract_title(chart_el)

    # Series
    if type_el is not None:
        for ser in xml_findall(type_el, "c:ser", NS):
            chart.series.append(_parse_series(ser))

    # Axes
    cat_ax = xml_find(chart_el, "c:catAx", NS) or xml_find(chart_el, "c:dateAx", NS)
    val_ax = xml_find(chart_el, "c:valAx", NS)
    if cat_ax is not None:
        chart.category_axis = _parse_axis(cat_ax, "category")
    if val_ax is not None:
        chart.value_axis = _parse_axis(val_ax, "value")

    return chart


def _identify_type(chart_el: Element):
    for tag in [
        "barChart", "lineChart", "pieChart", "areaChart", "scatterChart",
        "radarChart", "surfaceChart", "bubbleChart", "stockChart",
        "doughnutChart", "ofPieChart",
    ]:
        el = xml_find(chart_el, f"c:{tag}", NS)
        if el is not None:
            return tag.replace("Chart", ""), el
    return "unknown", None


def _extract_title(chart_el: Element) -> str | None:
    title_el = xml_find(chart_el, "c:title", NS)
    if title_el is None:
        return None
    rich = xml_find(title_el, "c:tx/c:rich", NS)
    if rich is not None:
        parts = []
        for p in xml_findall(rich, "a:p", {"a": A}):
            for r in xml_findall(p, "a:r", {"a": A}):
                t = xml_find(r, "a:t", {"a": A})
                if t is not None:
                    parts.append(xml_text(t))
        return "".join(parts)
    ref = xml_find(title_el, "c:tx/c:strRef/c:f", NS)
    return xml_text(ref) if ref is not None else None


def _parse_series(ser: Element) -> ChartSeriesContent:
    series = ChartSeriesContent()
    name_el = xml_find(ser, "c:tx/c:strRef/c:f", NS) or xml_find(ser, "c:tx/c:v", NS)
    if name_el is not None:
        series.name = xml_text(name_el)

    cat_f = xml_find(ser, "c:cat/c:strRef/c:f", NS) or xml_find(ser, "c:cat/c:numRef/c:f", NS)
    if cat_f is not None:
        series.categories_ref = xml_text(cat_f)

    val_f = xml_find(ser, "c:val/c:numRef/c:f", NS) or xml_find(ser, "c:val/c:strRef/c:f", NS)
    if val_f is not None:
        series.values_ref = xml_text(val_f)

    # Formatting
    spPr = xml_find(ser, "c:spPr", NS)
    if spPr is not None:
        fill_el = xml_find(spPr, "a:solidFill/a:srgbClr", {"a": A})
        if fill_el is not None:
            series.fill_color = f"#{xml_attr(fill_el, 'val', '')}"
        ln_el = xml_find(spPr, "a:ln/a:solidFill/a:srgbClr", {"a": A})
        if ln_el is not None:
            series.line_color = f"#{xml_attr(ln_el, 'val', '')}"
    return series


def _parse_axis(axis_el: Element, axis_type: str) -> ChartAxisContent:
    axis = ChartAxisContent(axis_type=axis_type)
    title_el = xml_find(axis_el, "c:title", NS)
    if title_el is not None:
        axis.title = _extract_title(axis_el)
    scaling = xml_find(axis_el, "c:scaling", NS)
    if scaling is not None:
        axis.min_value = xml_float(scaling, "min", None)
        axis.max_value = xml_float(scaling, "max", None)
    num_fmt = xml_find(axis_el, "c:numFmt", NS)
    if num_fmt is not None:
        axis.format_code = xml_attr(num_fmt, "formatCode")
    axis.axis_id=xml_int(axis_el, "axId", 0)
    return axis
