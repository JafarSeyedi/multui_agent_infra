from __future__ import annotations

import uuid
from typing import Any

from ....models.usdm_models import (
    BookmarkContent,
    CodeContent,
    CommentContent,
    ElementType,
    FootnoteContent,
    HeadingContent,
    ImageContent,
    ListContent,
    ListItemContent,
    LogicalElement,
    MathContent,
    ParagraphContent,
    QuoteContent,
    RichTextContent,
    RichTextSpan,
    TableCell,
    TableContent,
    TableRow,
    USDMDocument,
)
from .docx_image_handler import build_drawing_xml, process_images
from .docx_math_writer import latex_to_omml
from .docx_style_builder import (
    character_style_to_ooxml,
    paragraph_style_to_ooxml,
    table_style_to_ooxml,
    _escape_text as esc,
)


def build_document_xml(document: USDMDocument) -> str:
    """
    Build word/document.xml from a USDMDocument.

    Produces the <w:document> element with <w:body> containing:
    - Sections with <w:sectPr> (page size, margins)
    - Paragraphs <w:p> with <w:pPr> and runs <w:r> with <w:rPr> and <w:t>
    - Tables <w:tbl> with <w:tblGrid>, <w:tr>, <w:tc>
    - Bookmarks, comments, footnote/endnote references
    - Fields, pictures, shapes, math
    """
    lines: list[str] = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"',
        '  xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"',
        '  xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"',
        '  xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"',
        '  xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"',
        '  xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"',
        '  xmlns:v="urn:schemas-microsoft-com:vml"',
        '  xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml"',
        '  xmlns:w15="http://schemas.microsoft.com/office/word/2012/wordml"',
        '  xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"',
        '  mc:Ignorable="w14 w15">',
        "  <w:body>",
    ]

    image_info = process_images(document)
    image_map = image_info.get("images", {})

    for elem in document.logical_elements:
        elem_xml = _element_to_xml(elem, document, image_map)
        if elem_xml:
            lines.append(elem_xml)

    sect_pr = _build_section_properties(document)
    lines.append(sect_pr)
    lines.append("  </w:body>")
    lines.append("</w:document>")

    return "\n".join(lines)


def build_styles_xml(document: USDMDocument) -> str:
    """
    Build word/styles.xml from a USDMDocument.

    Produces <w:styles> with:
    - <w:docDefaults> — default run/paragraph properties
    - <w:style w:type="character"> — character styles
    - <w:style w:type="paragraph"> — paragraph styles
    - <w:style w:type="table"> — table styles
    """
    lines: list[str] = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">',
        "  <w:docDefaults>",
        "    <w:rPrDefault>",
        "      <w:rPr>",
        '        <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Times New Roman"/>',
        '        <w:sz w:val="22"/>',
        '        <w:szCs w:val="22"/>',
        '        <w:lang w:val="en-US"/>',
        "      </w:rPr>",
        "    </w:rPrDefault>",
        "    <w:pPrDefault>",
        "      <w:pPr>",
        '        <w:spacing w:after="160" w:line="276" w:lineRule="auto"/>',
        "      </w:pPr>",
        "    </w:pPrDefault>",
        "  </w:docDefaults>",
    ]

    stylesheet = getattr(document, "stylesheet", None)
    if stylesheet:
        for name, cs in stylesheet.character_styles.items():
            style_id = getattr(cs, "style_id", name) or name
            rpr = character_style_to_ooxml(cs)
            lines.append(
                f'  <w:style w:type="character" w:styleId="{esc(style_id)}">'
                f'<w:name w:val="{esc(name)}"/>'
                f"{rpr}"
                "</w:style>"
            )

        for name, ps in stylesheet.paragraph_styles.items():
            style_id = getattr(ps, "style_id", name) or name
            ppr = paragraph_style_to_ooxml(ps)
            lines.append(
                f'  <w:style w:type="paragraph" w:styleId="{esc(style_id)}">'
                f'<w:name w:val="{esc(name)}"/>'
                f"{ppr}"
                "</w:style>"
            )

        for name, ts in stylesheet.table_styles.items():
            style_id = getattr(ts, "style_id", name) or name
            tblpr = table_style_to_ooxml(ts)
            lines.append(
                f'  <w:style w:type="table" w:styleId="{esc(style_id)}">'
                f'<w:name w:val="{esc(name)}"/>'
                f"{tblpr}"
                "</w:style>"
            )

    lines.append("</w:styles>")
    return "\n".join(lines)


def build_numbering_xml(document: USDMDocument) -> str:
    """
    Build word/numbering.xml from a USDMDocument.

    Produces <w:numbering> with:
    - <w:abstractNum> — abstract numbering definitions
    - <w:num> — numbering instances referencing abstract definitions
    - <w:lvl> — level definitions with format, alignment, text, indentation
    """
    from .docx_style_builder import list_style_to_ooxml

    lines: list[str] = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<w:numbering xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">',
    ]

    stylesheet = getattr(document, "stylesheet", None)
    if stylesheet:
        for name, ls in stylesheet.list_styles.items():
            num_xml = list_style_to_ooxml(ls)
            lines.append(f"  {num_xml}")

    lines.append("</w:numbering>")
    return "\n".join(lines)


def build_footnotes_xml(document: USDMDocument) -> str:
    """
    Build word/footnotes.xml from a USDMDocument.

    Produces <w:footnotes> with <w:footnote> elements for each footnote.
    Separators (id=-1 for separator, id=0 for continuation separator) are included.
    """
    lines: list[str] = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<w:footnotes xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">',
        '  <w:footnote w:type="separator" w:id="-1"><w:p><w:r><w:separator/></w:r></w:p></w:footnote>',
        '  <w:footnote w:type="continuationSeparator" w:id="0"><w:p><w:r><w:continuationSeparator/></w:r></w:p></w:footnote>',
    ]

    footnote_counter = 0
    for elem in document.logical_elements:
        if elem.element_type == ElementType.FOOTNOTE:
            footnote_counter += 1
            if isinstance(elem.content, FootnoteContent):
                note_id = elem.content.note_id or str(footnote_counter)
                lines.append(f'  <w:footnote w:id="{note_id}">')
                for sub_elem in elem.content.elements:
                    sub_xml = _element_to_xml(sub_elem, document, {}, in_footnote=True)
                    if sub_xml:
                        lines.append(sub_xml)
                lines.append("  </w:footnote>")

    lines.append("</w:footnotes>")
    return "\n".join(lines)


def build_endnotes_xml(document: USDMDocument) -> str:
    """
    Build word/endnotes.xml from a USDMDocument.

    Produces <w:endnotes> with <w:endnote> elements for each endnote.
    """
    lines: list[str] = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<w:endnotes xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">',
        '  <w:endnote w:type="separator" w:id="-1"><w:p><w:r><w:separator/></w:r></w:p></w:endnote>',
        '  <w:endnote w:type="continuationSeparator" w:id="0"><w:p><w:r><w:continuationSeparator/></w:r></w:p></w:endnote>',
    ]

    endnote_counter = 0
    for elem in document.logical_elements:
        if elem.element_type == ElementType.ENDNOTE:
            endnote_counter += 1
            endnote_id = str(endnote_counter)
            lines.append(f'  <w:endnote w:id="{endnote_id}">')
            content = elem.content
            if hasattr(content, "elements"):
                for sub_elem in content.elements:
                    sub_xml = _element_to_xml(sub_elem, document, {})
                    if sub_xml:
                        lines.append(sub_xml)
            lines.append("  </w:endnote>")

    lines.append("</w:endnotes>")
    return "\n".join(lines)


def build_comments_xml(document: USDMDocument) -> str:
    """
    Build word/comments.xml from a USDMDocument.

    Produces <w:comments> with <w:comment> elements for each comment,
    including author, date, and paragraph content.
    """
    lines: list[str] = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<w:comments xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">',
    ]

    comment_counter = 0
    for elem in document.logical_elements:
        if elem.element_type == ElementType.COMMENT:
            comment_counter += 1
            if isinstance(elem.content, CommentContent):
                c_id = elem.content.comment_id or str(comment_counter)
                author = esc(elem.content.author or "Unknown")
                date = elem.content.date or ""
                date_attr = f' w:date="{esc(date)}"' if date else ""
                lines.append(
                    f'  <w:comment w:id="{c_id}" w:author="{author}"{date_attr}>'
                )
                for sub_elem in elem.content.elements:
                    sub_xml = _element_to_xml(sub_elem, document, {})
                    if sub_xml:
                        lines.append(sub_xml)
                lines.append("  </w:comment>")

    lines.append("</w:comments>")
    return "\n".join(lines)


def _element_to_xml(
    elem: LogicalElement,
    document: USDMDocument,
    image_map: dict[str, Any],
    in_footnote: bool = False,
) -> str:
    """Convert a single LogicalElement to OOXML XML string."""
    content = elem.content

    if elem.element_type == ElementType.PARAGRAPH and isinstance(content, ParagraphContent):
        return _paragraph_to_xml(content, elem)

    if elem.element_type == ElementType.HEADING and isinstance(content, HeadingContent):
        return _heading_to_xml(content, elem)

    if elem.element_type == ElementType.TABLE and isinstance(content, TableContent):
        return _table_to_xml(content, document)

    if elem.element_type == ElementType.LIST and isinstance(content, ListContent):
        return _list_to_xml(content, document)

    if elem.element_type == ElementType.LIST_ITEM and isinstance(content, ListItemContent):
        return _list_item_to_xml(content, document)

    if elem.element_type == ElementType.QUOTE and isinstance(content, QuoteContent):
        return _quote_to_xml(content, document)

    if elem.element_type == ElementType.CODE and isinstance(content, CodeContent):
        return _code_to_xml(content, elem)

    if elem.element_type == ElementType.IMAGE and isinstance(content, ImageContent):
        return _image_to_xml(content, image_map)

    if elem.element_type == ElementType.MATH and isinstance(content, MathContent):
        return _math_to_xml(content, elem)

    if elem.element_type == ElementType.PAGE_BREAK:
        return _page_break_to_xml()

    if elem.element_type == ElementType.LINE_BREAK:
        return _line_break_to_xml()

    if elem.element_type == ElementType.COLUMN_BREAK:
        return _column_break_to_xml()

    if elem.element_type == ElementType.BOOKMARK and isinstance(content, BookmarkContent):
        return _bookmark_to_xml(content)

    if elem.element_type == ElementType.COMMENT and isinstance(content, CommentContent):
        return _comment_reference_to_xml(content)

    return ""


def _paragraph_to_xml(content: ParagraphContent, elem: LogicalElement | None = None) -> str:
    """Convert a ParagraphContent to <w:p> XML."""
    p_id = elem.element_id if elem else str(uuid.uuid4())[:8]
    lines: list[str] = [f'<w:p w14:paraId="{p_id}">']

    style_id = getattr(content, "style", None)
    if style_id or elem:
        ppr_parts: list[str] = []
        if style_id:
            ppr_parts.append(f'<w:pStyle w:val="{esc(style_id)}"/>')
        if elem and elem.metadata:
            alignment = elem.metadata.get("alignment")
            if alignment:
                jc_map = {
                    "left": "left", "right": "right",
                    "center": "center", "justify": "both",
                }
                jc = jc_map.get(alignment, alignment)
                ppr_parts.append(f'<w:jc w:val="{esc(jc)}"/>')
        if ppr_parts:
            lines.append(f"  <w:pPr>{''.join(ppr_parts)}</w:pPr>")

    lines.append(_rich_text_to_runs(content.text))
    lines.append("</w:p>")
    return "\n".join(lines)


def _heading_to_xml(content: HeadingContent, elem: LogicalElement | None = None) -> str:
    """Convert a HeadingContent to <w:p> XML with heading style."""
    level = content.level
    style_name = f"Heading{level}" if 1 <= level <= 9 else "Heading1"
    p_id = elem.element_id if elem else str(uuid.uuid4())[:8]
    lines: list[str] = [f'<w:p w14:paraId="{p_id}">']

    lines.append(
        f"  <w:pPr>"
        f'<w:pStyle w:val="{esc(style_name)}"/>'
        f'<w:outlineLvl w:val="{level - 1}"/>'
        f"</w:pPr>"
    )

    lines.append(_rich_text_to_runs(content.text))
    lines.append("</w:p>")
    return "\n".join(lines)


def _table_to_xml(content: TableContent, document: USDMDocument) -> str:
    """Convert a TableContent to <w:tbl> XML."""
    lines: list[str] = ["<w:tbl>"]

    # Table properties
    tbl_pr = _build_table_properties(content)
    if tbl_pr:
        lines.append(f"  <w:tblPr>{tbl_pr}</w:tblPr>")

    # Table grid
    if content.grid and len(content.grid) > 0:
        lines.append("  <w:tblGrid>")
        for col_w in content.grid:
            lines.append(f'    <w:gridCol w:w="{col_w}"/>')
        lines.append("  </w:tblGrid>")
    else:
        num_cols = max(len(row.cells) for row in content.rows) if content.rows else 0
        lines.append("  <w:tblGrid>")
        for _ in range(num_cols):
            lines.append('    <w:gridCol w:w="2000"/>')
        lines.append("  </w:tblGrid>")

    # Rows
    for row in content.rows:
        lines.append(_table_row_to_xml(row, document))

    lines.append("</w:tbl>")
    return "\n".join(lines)


def _table_row_to_xml(row: TableRow, document: USDMDocument) -> str:
    """Convert a TableRow to <w:tr> XML."""
    tr_pr: list[str] = []
    if row.is_header:
        tr_pr.append('<w:tblHeader/>')
    tr_pr_str = f"<w:trPr>{''.join(tr_pr)}</w:trPr>" if tr_pr else ""

    lines: list[str] = [f"<w:tr>{tr_pr_str}"]
    for cell in row.cells:
        lines.append(_table_cell_to_xml(cell, document))
    lines.append("</w:tr>")
    return "\n".join(lines)


def _table_cell_to_xml(cell: TableCell, document: USDMDocument) -> str:
    """Convert a TableCell to <w:tc> XML."""
    lines: list[str] = ["  <w:tc>"]

    tc_pr: list[str] = []
    if cell.col_span and cell.col_span > 1:
        tc_pr.append(f'<w:gridSpan w:val="{cell.col_span}"/>')
    if cell.row_span and cell.row_span > 1:
        tc_pr.append('<w:vMerge w:val="restart"/>')
    if cell.metadata:
        val = cell.metadata.get("width")
        if val:
            tc_pr.append(f'<w:tcW w:w="{val}" w:type="dxa"/>')
    if tc_pr:
        lines.append(f"    <w:tcPr>{''.join(tc_pr)}</w:tcPr>")

    for sub_elem in cell.content:
        elem_xml = _element_to_xml(sub_elem, document, {})
        if elem_xml:
            lines.append(elem_xml)

    if not cell.content:
        lines.append("<w:p/>")

    lines.append("  </w:tc>")
    return "\n".join(lines)


def _build_table_properties(content: TableContent) -> str:
    """Build table properties XML from TableContent."""
    parts: list[str] = []
    meta = content.metadata or {}

    alignment = meta.get("alignment", "left")
    if alignment:
        parts.append(f'<w:jc w:val="{esc(alignment)}"/>')

    tbl_width = meta.get("width")
    if tbl_width:
        parts.append(f'<w:tblW w:w="{tbl_width}" w:type="dxa"/>')

    layout = meta.get("layout_type", "autofit")
    parts.append(f'<w:tblLayout w:type="{esc(layout)}"/>')

    borders = meta.get("borders")
    if borders:
        b_parts: list[str] = ["<w:tblBorders>"]
        for pos in ("top", "bottom", "left", "right", "insideH", "insideV"):
            b = borders.get(pos)
            if b:
                b_style = b.get("style", "single")
                b_color = b.get("color", "000000")
                b_size = b.get("size", 4)
                b_parts.append(
                    f'<w:{pos} w:val="{esc(b_style)}" w:sz="{b_size}" w:space="0" w:color="{b_color}"/>'
                )
        b_parts.append("</w:tblBorders>")
        parts.append("".join(b_parts))

    cell_margins = meta.get("cell_margins")
    if cell_margins:
        m_parts: list[str] = []
        for pos, val in cell_margins.items():
            m_parts.append(f'<w:{pos} w:w="{val}" w:type="dxa"/>')
        if m_parts:
            parts.append(f'<w:tblCellMar>{"".join(m_parts)}</w:tblCellMar>')

    return "".join(parts)


def _list_to_xml(content: ListContent, document: USDMDocument) -> str:
    """Convert a ListContent to XML (delegates to items)."""
    parts: list[str] = []
    for item in content.items:
        if isinstance(item, ListItemContent):
            parts.append(_list_item_content_to_xml(item, document))
        elif isinstance(item, LogicalElement):
            parts.append(_element_to_xml(item, document, {}))
    return "\n".join(parts) if parts else ""


def _list_item_to_xml(content: ListItemContent, document: USDMDocument) -> str:
    """Convert a ListItemContent element to XML."""
    return _list_item_content_to_xml(content, document)


def _list_item_content_to_xml(content: ListItemContent, document: USDMDocument) -> str:
    """Convert ListItemContent (container) to XML paragraphs with numbering."""
    parts: list[str] = []
    for sub_elem in content.elements:
        parts.append(_element_to_xml(sub_elem, document, {}))
    return "\n".join(parts) if parts else ""


def _quote_to_xml(content: QuoteContent, document: USDMDocument) -> str:
    """Convert a QuoteContent to XML paragraphs."""
    parts: list[str] = []
    for sub_elem in content.elements:
        parts.append(_element_to_xml(sub_elem, document, {}))
    return "\n".join(parts) if parts else ""


def _code_to_xml(content: CodeContent, elem: LogicalElement | None = None) -> str:
    """Convert a CodeContent to a formatted paragraph."""
    p_id = elem.element_id if elem else str(uuid.uuid4())[:8]
    lines: list[str] = [f'<w:p w14:paraId="{p_id}">']
    lines.append(
        '  <w:pPr><w:pStyle w:val="CodeBlock"/></w:pPr>'
    )

    code_text = content.code or ""
    for code_line in code_text.split("\n"):
        lines.append(
            "  <w:r>"
            f'<w:t xml:space="preserve">{esc(code_line)}</w:t>'
            "</w:r>"
            '<w:r><w:br/></w:r>'
        )

    lines.append("</w:p>")
    return "\n".join(lines)


def _image_to_xml(content: ImageContent, image_map: dict[str, Any]) -> str:
    """Convert an ImageContent to a paragraph with embedded drawing."""
    src = content.src or ""
    rel_id = _find_rel_id_for_image(src, image_map)
    if not rel_id:
        return ""

    width_emu = int((content.width or 100) * 914400 / 96)
    height_emu = int((content.height or 100) * 914400 / 96)
    alt = content.alt or ""

    drawing_xml = build_drawing_xml(rel_id, width_emu, height_emu, alt)

    lines: list[str] = [
        "<w:p>",
        "  <w:r>",
        f"    {drawing_xml}",
        "  </w:r>",
        "</w:p>",
    ]
    return "\n".join(lines)


def _math_to_xml(content: MathContent, elem: LogicalElement | None = None) -> str:
    """Convert a MathContent to a paragraph with OMML."""
    latex = content.latex or ""
    if not latex:
        return ""

    omml = latex_to_omml(latex)

    if content.display:
        lines: list[str] = [
            "<w:p>",
            "  <w:r>",
            f"    {omml}",
            "  </w:r>",
            "</w:p>",
        ]
        return "\n".join(lines)
    else:
        return f"<w:r>{omml}</w:r>"


def _page_break_to_xml() -> str:
    """Generate a page break paragraph."""
    return (
        "<w:p>"
        '<w:r><w:br w:type="page"/></w:r>'
        "</w:p>"
    )


def _line_break_to_xml() -> str:
    """Generate a line break paragraph."""
    return (
        "<w:p>"
        "<w:r><w:br/></w:r>"
        "</w:p>"
    )


def _column_break_to_xml() -> str:
    """Generate a column break paragraph."""
    return (
        "<w:p>"
        '<w:r><w:br w:type="column"/></w:r>'
        "</w:p>"
    )


def _bookmark_to_xml(content: BookmarkContent) -> str:
    """Generate bookmark start/end XML."""
    name = esc(content.name or "bookmark")
    bmk_id = abs(hash(name)) % 100000
    return (
        f'<w:bookmarkStart w:id="{bmk_id}" w:name="{name}"/>'
        f'<w:bookmarkEnd w:id="{bmk_id}"/>'
    )


def _comment_reference_to_xml(content: CommentContent) -> str:
    """Generate comment range reference XML."""
    c_id = content.comment_id or "0"
    return (
        f'<w:commentRangeStart w:id="{c_id}"/>'
        '<w:r><w:commentReference w:id="{c_id}"/></w:r>'
        f'<w:commentRangeEnd w:id="{c_id}"/>'
    ).format(c_id=c_id)


def _rich_text_to_runs(rich_text: RichTextContent) -> str:
    """Convert RichTextContent to a series of <w:r> elements."""
    if not rich_text or not rich_text.spans:
        return "<w:r><w:t/></w:r>"

    parts: list[str] = []
    for span in rich_text.spans:
        if span.math:
            omml = latex_to_omml(span.math)
            if span.display_math:
                parts.append(
                    "<w:p>"
                    f"  <w:r>{omml}</w:r>"
                    "</w:p>"
                )
            else:
                parts.append(f"<w:r>{omml}</w:r>")
            continue

        span_text = span.text if span.text else ""
        if not span_text and not span.math:
            continue

        r_parts: list[str] = ["  <w:r>"]
        rpr = _build_span_rpr(span)
        if rpr:
            r_parts.append(f"    <w:rPr>{rpr}</w:rPr>")

        for seg in span_text.split("\n"):
            r_parts.append(f"    <w:t xml:space=\"preserve\">{esc(seg)}</w:t>")
            if seg != span_text:
                r_parts.append("    <w:br/>")

        r_parts.append("  </w:r>")
        parts.append("\n".join(r_parts))

    return "\n".join(parts) if parts else "<w:r><w:t/></w:r>"


def _build_span_rpr(span: RichTextSpan) -> str:
    """Build run properties XML for a RichTextSpan."""
    parts: list[str] = []

    if span.bold:
        parts.append("<w:b/>")
    if span.italic:
        parts.append("<w:i/>")
    if span.underline:
        parts.append('<w:u w:val="single"/>')
    if span.code:
        parts.append('<w:rFonts w:ascii="Consolas" w:hAnsi="Consolas"/>')
    if span.color and span.color.lower() != "auto":
        c = _normalize_color(span.color)
        parts.append(f'<w:color w:val="{c}"/>')
    if span.font:
        parts.append(f'<w:rFonts w:ascii="{esc(span.font)}" w:hAnsi="{esc(span.font)}"/>')
    if span.background and span.background.lower() != "auto":
        parts.append(f'<w:shd w:fill="{_normalize_color(span.background)}" w:val="clear"/>')

    if span.character_style:
        parts.append(f'<w:rStyle w:val="{esc(span.character_style)}"/>')

    return "".join(parts)


def _normalize_color(color: str) -> str:
    """Normalize color to 6-char hex without #."""
    if not color or color.lower() in ("auto", "none", "transparent"):
        return "auto"
    c = color.strip().lstrip("#")
    if len(c) == 8:
        c = c[2:]
    if len(c) == 6 and all(ch in "0123456789ABCDEFabcdef" for ch in c):
        return c.upper()
    color_map = {
        "black": "000000", "white": "FFFFFF", "red": "FF0000",
        "green": "008000", "blue": "0000FF", "yellow": "FFFF00",
        "cyan": "00FFFF", "magenta": "FF00FF", "gray": "808080",
    }
    return color_map.get(color.lower(), c[:6].upper())


def _build_section_properties(document: USDMDocument) -> str:
    """Build <w:sectPr> for the document."""
    getattr(document, "metadata", {}) or {}
    lines: list[str] = ["<w:sectPr>"]

    if document.pages:
        first_page = document.pages[0]
        pg_w = int(first_page.width * 1440 / 96) if first_page.width else 12240
        pg_h = int(first_page.height * 1440 / 96) if first_page.height else 15840
    else:
        pg_w = 12240
        pg_h = 15840

    lines.append(f'  <w:sz w:w="{pg_w}" w:h="{pg_h}"/>')
    lines.append('  <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="720" w:footer="720" w:gutter="0"/>')
    lines.append("</w:sectPr>")
    return "\n".join(lines)


def _find_rel_id_for_image(src: str, image_map: dict[str, Any]) -> str:
    """Find the relationship ID for an image source."""
    for rel_id, info in image_map.items():
        if info.get("filename") == src or src in info.get("filename", ""):
            return rel_id
    if image_map:
        first_key = next(iter(image_map))
        return first_key
    return ""
