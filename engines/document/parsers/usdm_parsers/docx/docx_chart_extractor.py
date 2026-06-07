# engines/document/parsers/docx_parser/docx_chart_extractor.py
"""
Extracts ChartContent from a DOCX chart XML part.
The XML namespace is the same as SpreadsheetML charts.
"""
from xml.etree.ElementTree import Element

from ....models.usdm_models import ChartAxisContent
from ....models.usdm_models import ChartContent
from ....models.usdm_models import ChartSeriesContent

C = "http://schemas.openxmlformats.org/drawingml/2006/chart"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
NS = {"c": C, "a": A}

def parse_docx_chart(chart_xml: Element) -> ChartContent:
    """Convert a chart XML root (c:chartSpace) into ChartContent."""
    chart_el = _find(chart_xml, "c:chart")
    if chart_el is None:
        return ChartContent(chart_type="unknown")

    chart_type, type_el = _identify_type(chart_el)
    chart = ChartContent(chart_type=chart_type)

    if type_el is not None:
        chart.grouping = type_el.get("grouping")
        chart.direction = type_el.get("barDir")

    chart.title = _extract_title(chart_el)

    if type_el is not None:
        for ser in _findall(type_el, "c:ser"):
            chart.series.append(_parse_series(ser))

    cat_ax = _find(chart_el, "c:catAx") or _find(chart_el, "c:dateAx")
    val_ax = _find(chart_el, "c:valAx")
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
        el = _find(chart_el, f"c:{tag}")
        if el is not None:
            return tag.replace("Chart", ""), el
    return "unknown", None


def _extract_title(chart_el: Element) -> str | None:
    title_el = _find(chart_el, "c:title")
    if title_el is None:
        return None
    rich = _find(title_el, "c:tx/c:rich")
    if rich is not None:
        parts = []
        for p in _findall(rich, "a:p"):
            for r in _findall(p, "a:r"):
                t = _find(r, "a:t")
                if t is not None and t.text:
                    parts.append(t.text)
        return "".join(parts)
    ref = _find(title_el, "c:tx/c:strRef/c:f")
    return ref.text if ref is not None else None


def _parse_series(ser: Element) -> ChartSeriesContent:
    series = ChartSeriesContent()
    name_el = _find(ser, "c:tx/c:strRef/c:f") or _find(ser, "c:tx/c:v")
    if name_el is not None:
        series.name = name_el.text or ""

    cat_f = _find(ser, "c:cat/c:strRef/c:f") or _find(ser, "c:cat/c:numRef/c:f")
    if cat_f is not None:
        series.categories_ref = cat_f.text

    val_f = _find(ser, "c:val/c:numRef/c:f") or _find(ser, "c:val/c:strRef/c:f")
    if val_f is not None:
        series.values_ref = val_f.text

    spPr = _find(ser, "c:spPr")
    if spPr is not None:
        fill_el = _find(spPr, "a:solidFill/a:srgbClr")
        if fill_el is not None:
            series.fill_color = f"#{fill_el.get('val', '')}"
        ln_el = _find(spPr, "a:ln/a:solidFill/a:srgbClr")
        if ln_el is not None:
            series.line_color = f"#{ln_el.get('val', '')}"
    return series


def _parse_axis(axis_el: Element, axis_type: str) -> ChartAxisContent:
    axis = ChartAxisContent(axis_type=axis_type)
    title_el = _find(axis_el, "c:title")
    if title_el is not None:
        axis.title = _extract_title(axis_el)
    scaling = _find(axis_el, "c:scaling")
    if scaling is not None:
        if scaling.get("min"):
            axis.min_value = float(scaling.get("min"))
        if scaling.get("max"):
            axis.max_value = float(scaling.get("max"))
    num_fmt = _find(axis_el, "c:numFmt")
    if num_fmt is not None:
        axis.format_code = num_fmt.get("formatCode")
    axis.axis_id = int(axis_el.get("axId", "0"))
    return axis


# Helper functions using the NS dict
def _find(parent, path):
    return parent.find(path, NS)

def _findall(parent, path):
    return parent.findall(path, NS)
