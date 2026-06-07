# engines/document/parsers/spreadsheet_parser/xlsx/workbook_builder.py
"""
Assembles a full Workbook from the top-level parts:
- workbook.xml
- sharedStrings.xml
- styles.xml
- relationships (.rels)
- worksheets
- optional external links, pivot caches/tables, calc chain
"""
from __future__ import annotations

from xml.etree.ElementTree import Element

from ....models.esdm_models import DocumentMetadata
from ....models.esdm_models import ExternalLink
from ....models.esdm_models import RelationshipCollection
from ....models.esdm_models import SharedStrings
from ....models.esdm_models import Workbook
from ....models.esdm_models import WorkbookProperties
from ....models.usdm_models import RichTextContent, RichTextSpan, ChartContent
from .formulas_builder import build_calculation_chain
from .namespaces import MAIN
from .namespaces import REL
from .pivot_builder import build_pivot_cache_from_xml
from .pivot_builder import build_pivot_table_from_xml
from .relationships_builder import build_defined_names
from .relationships_builder import build_external_links_from_rels
from .styles_builder import build_stylesheet
from .utils import color_hex_from_xml
from .utils import xml_attr
from .utils import xml_bool
from .utils import xml_find
from .utils import xml_findall
from .utils import xml_int
from .utils import xml_text
from .worksheet_builder import build_worksheet

NS = {"": MAIN, "r": REL}


def build_workbook(
    workbook_xml: Element,
    shared_strings_xml: Element,
    styles_xml: Element,
    workbook_rels: RelationshipCollection,
    sheet_xmls: dict[str, Element],          # sheet name -> sheet XML root
    comments_xmls: dict[str, Element] | None = None,
    threaded_comments_xmls: dict[str, Element] | None = None,
    table_xmls: dict[str, list[Element]] | None = None,
    calc_chain_xml: Element | None = None,
    pivot_cache_xmls: list[Element] | None = None,
    pivot_table_xmls: list[Element] | None = None,
    external_links_xmls: dict[int, Element] | None = None,
    vba_bin: bytes | None = None,
    drawing_xmls: dict[str, Element] | None = None,
    image_map: dict[str, str] | None = None,
    chart_map: dict[str, ChartContent] | None = None
) -> Workbook:
    """
    Main entry point: creates a fully populated Workbook.

    Args:
        workbook_xml: root of xl/workbook.xml
        shared_strings_xml: root of xl/sharedStrings.xml
        styles_xml: root of xl/styles.xml
        workbook_rels: RelationshipCollection from xl/_rels/workbook.xml.rels
        sheet_xmls: map sheet name -> root of xl/worksheets/sheetN.xml
        comments_xmls: optional, map sheet name -> xl/commentsN.xml root
        threaded_comments_xmls: optional, map sheet name -> xl/threadedCommentsN.xml root
        table_xmls: optional, map sheet name -> list of xl/tables/tableN.xml roots
        calc_chain_xml: optional root of xl/calcChain.xml
        pivot_cache_xmls: optional list of xl/pivotCache/pivotCacheDefinitionN.xml roots
        pivot_table_xmls: optional list of xl/pivotTables/pivotTableN.xml roots
        external_links_xmls: optional map of link id -> xl/externalLinks/externalLinkN.xml root
        vba_bin: optional raw bytes of xl/vbaProject.bin

    Returns:
        Workbook
    """
    wb = Workbook()
    wb.properties = _build_workbook_properties(workbook_xml)
    wb.metadata = DocumentMetadata(title="")  # can be filled later

    # Shared strings
    wb.shared_strings = _build_shared_strings(shared_strings_xml)

    # Stylesheet
    wb.stylesheet = build_stylesheet(styles_xml)

    # Relationships
    wb.relationships = workbook_rels

    # Defined names
    wb.defined_names = build_defined_names(workbook_xml)

    # Named ranges (can be derived from defined names; we'll keep empty for now)
    # wb.named_ranges = ...

    # External links
    if external_links_xmls:
        for link_id, link_xml in external_links_xmls.items():
            # create ExternalLink with references
            from .relationships_builder import build_external_link_references
            refs = build_external_link_references(link_xml)
            wb.external_links.append(
                ExternalLink(id=link_id, file_path="", references=refs)
            )
    else:
        wb.external_links = build_external_links_from_rels(workbook_rels)

    # Worksheets
    sheets_info = _parse_sheets(workbook_xml, workbook_rels)
    for sheet_name, sheet_id, rel_id, rel_target in sheets_info:
        if sheet_name not in sheet_xmls:
            continue
        sheet_xml = sheet_xmls[sheet_name]
        comments_xml = comments_xmls.get(sheet_name) if comments_xmls else None
        threaded_comments_xml = threaded_comments_xmls.get(sheet_name) if threaded_comments_xmls else None
        table_xml_list = table_xmls.get(sheet_name) if table_xmls else []
        drawing_xml: Element | None = drawing_xmls.get(sheet_name) if drawing_xmls else None

        ws = build_worksheet(
            sheet_name=sheet_name,
            sheet_xml=sheet_xml,
            shared_strings=wb.shared_strings,
            stylesheet=wb.stylesheet,
            comments_xml=comments_xml,
            threaded_comments_xml=threaded_comments_xml,
            table_xmls=table_xml_list,
            drawing_xml=drawing_xml,
            image_map=image_map,
            chart_map=chart_map
        )

        # Sheet ID may be used for calc chain; store if needed
        wb.sheets.append(ws)

    # Pivot caches / tables
    if pivot_cache_xmls:
        for pc_xml in pivot_cache_xmls:
            wb.pivot_caches.append(build_pivot_cache_from_xml(pc_xml))
    if pivot_table_xmls:
        for pt_xml in pivot_table_xmls:
            wb.pivot_tables.append(build_pivot_table_from_xml(pt_xml))

    # Calc chain
    if calc_chain_xml is not None:
        wb.calculation_chain = build_calculation_chain(calc_chain_xml)

    # VBA
    wb.vba_project = vba_bin

    # Full calculation on load default
    wb.full_calculation_on_load = xml_bool(
        xml_find(workbook_xml, "calcPr", NS), "fullCalcOnLoad", True
    )

    return wb


# ── Internal helpers ──
def _build_workbook_properties(wb_xml: Element) -> WorkbookProperties:
    """Extract workbook properties like date1904, window size, active tab."""
    props = WorkbookProperties()
    wp = xml_find(wb_xml, "workbookPr", NS)
    if wp is not None:
        props.date_1904 = xml_bool(wp, "date1904")
        props.default_theme_version = xml_int(wp, "defaultThemeVersion", 0)
    # Workbook views for active tab and window size
    views = xml_find(wb_xml, "bookViews", NS)
    if views is not None:
        wbv = xml_find(views, "workbookView", NS)
        if wbv is not None:
            props.active_tab = xml_int(wbv, "activeTab", 0)
            props.window_width = xml_int(wbv, "windowWidth", 1920)
            props.window_height = xml_int(wbv, "windowHeight", 1080)
    return props

def _parse_rich_text_runs(r_eles: list[Element]) -> RichTextContent:
    spans = []
    for r in r_eles:
        rpr = xml_find(r, "rPr", NS)
        t = xml_find(r, "t", NS)
        text = xml_text(t) if t is not None else ""
        span = RichTextSpan(text=text)
        if rpr is not None:
            span.bold = xml_find(rpr, "b", NS) is not None
            span.italic = xml_find(rpr, "i", NS) is not None
            span.underline = xml_find(rpr, "u", NS) is not None
            color_el = xml_find(rpr, "color", NS)
            if color_el is not None:
                span.color = color_hex_from_xml(color_el, NS)
            latin = xml_find(rpr, "latin", NS)
            if latin is not None:
                span.font = xml_attr(latin, "typeface")
        spans.append(span)
    return RichTextContent(spans=spans)

def _build_shared_strings(ss_xml: Element) -> SharedStrings:
    """Parse sharedStrings.xml into SharedStrings object."""
    strings = []
    index_map = {}
    rich_text_map = {}
    for i, si in enumerate(xml_findall(ss_xml, "si", NS)):
        # A string can be either <t> directly or <r> rich text.
        r_eles = xml_findall(si, "r", NS)
        if r_eles:
            rich_text = _parse_rich_text_runs(r_eles)
            text = "".join(sp.text for sp in rich_text.spans)
            rich_text_map[i] = rich_text
        else:
            t = xml_find(si, "t", NS)
            text = xml_text(t) if t is not None else ""
        strings.append(text)
        index_map[text] = i
    ss = SharedStrings(strings=strings, index_map=index_map)
    ss.rich_text_map = rich_text_map  # attach extra attribute
    return ss

def _parse_sheets(wb_xml: Element, rels: RelationshipCollection) -> list[tuple[str, int, str, str]]:
    """
    Return list of (name, sheetId, rId, target) for each sheet in workbook.xml.
    """
    sheets: list[tuple[str, int, str, str]] = []
    sheets_elem = xml_find(wb_xml, "sheets", NS)
    if sheets_elem is None:
        return sheets
    for sh in xml_findall(sheets_elem, "sheet", NS):
        name = xml_attr(sh, "name", "")
        sheet_id = xml_int(sh, "sheetId", 0)
        r_id = xml_attr(sh, "r:id", "")
        # resolve target from relationships
        target = ""
        for rel in rels.relationships:
            if rel.id == r_id:
                target = rel.target
                break
        sheets.append((name, sheet_id, r_id, target))
    return sheets
