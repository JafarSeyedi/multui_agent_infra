import pytest

from engines.document.models.base import ElementType
from engines.document.models.media_types import MEDIA_TYPES
from engines.document.models.usdm_models import (
    CaptionContent,
    CharacterStyle,
    FooterContent,
    FormFieldContent,
    HeaderContent,
    HeadingContent,
    IndexContent,
    ListContent,
    ListItemContent,
    LogicalElement,
    MacroContent,
    ParagraphContent,
    ParagraphStyle,
    PageReferenceContent,
    RichTextContent,
    RichTextSpan,
    Section,
    SectionBreakContent,
    StructuredDocumentTagContent,
    StyleSheet,
    TableContent,
    TOCContent,
    USDMDocument,
    WatermarkContent,
)

pytestmark = pytest.mark.asyncio


def test_usdm_document_creation():
    doc = USDMDocument(
        document_id="test-001",
        title="Test Document",
        media_type=MEDIA_TYPES["html"],
    )
    assert doc.document_id == "test-001"
    assert doc.title == "Test Document"
    assert isinstance(doc.sections, list)
    assert isinstance(doc.elements, list)
    assert isinstance(doc.logical_elements, list)


def test_usdm_document_with_sections():
    section = Section(section_id="s1", section_type="body")
    doc = USDMDocument(
        document_id="test-002",
        title="Sections Doc",
        media_type=MEDIA_TYPES["html"],
        sections=[section],
    )
    assert len(doc.sections) == 1
    assert doc.sections[0].section_id == "s1"


def test_usdm_document_with_logical_elements():
    elem = HeadingContent(level=1, text=RichTextContent(spans=[RichTextSpan(text="Hi")]))
    logical = LogicalElement(element_id="h1", element_type=ElementType.HEADING, content=elem)
    doc = USDMDocument(
        document_id="test-003",
        title="Logical Doc",
        media_type=MEDIA_TYPES["html"],
        logical_elements=[logical],
    )
    assert len(doc.logical_elements) == 1
    assert doc.logical_elements[0].element_type == ElementType.HEADING


def test_paragraph_content():
    para = ParagraphContent(
        text=RichTextContent(spans=[RichTextSpan(text="Hello"), RichTextSpan(text=" World")])
    )
    assert len(para.text.spans) == 2
    assert para.text.spans[0].text == "Hello"


def test_heading_content():
    heading = HeadingContent(level=2, text=RichTextContent(spans=[RichTextSpan(text="Title")]))
    assert heading.level == 2
    assert heading.text.spans[0].text == "Title"


def test_rich_text_content():
    spans = [
        RichTextSpan(text="Normal "),
        RichTextSpan(text="Bold", bold=True),
        RichTextSpan(text=" Italic", italic=True),
    ]
    rt = RichTextContent(spans=spans)
    assert len(rt.spans) == 3


def test_table_content():
    from engines.document.models.usdm_models import TableCell, TableRow

    cell = TableCell(content=[], is_header=True)
    row = TableRow(cells=[cell], is_header=True)
    table = TableContent(rows=[row])
    assert len(table.rows) == 1


def test_list_content():
    item = ListItemContent(elements=[])
    lst = ListContent(ordered=True, items=[item])
    assert lst.ordered is True
    assert len(lst.items) == 1


def test_stylesheet():
    ss = StyleSheet(
        character_styles={"bold": CharacterStyle(name="bold", bold=True)},
        paragraph_styles={"normal": ParagraphStyle(name="normal")},
    )
    assert "bold" in ss.character_styles
    assert "normal" in ss.paragraph_styles


def test_element_type_enum():
    assert ElementType.PARAGRAPH.value == "paragraph"
    assert ElementType.HEADING.value == "heading"
    assert ElementType.TABLE.value == "table"
    assert ElementType.CODE.value == "code"
    assert ElementType.IMAGE.value == "image"
    assert ElementType.LIST.value == "list"
    assert ElementType.LIST_ITEM.value == "list_item"
    assert ElementType.BOOKMARK.value == "bookmark"
    assert ElementType.FOOTNOTE.value == "footnote"


def test_new_content_types():
    hc = HeaderContent(section_id="s1", elements=[])
    assert hc.section_id == "s1"

    fc = FooterContent(section_id="s1", elements=[])
    assert fc.section_id == "s1"

    toc = TOCContent(label="Table of Contents", level=1)
    assert toc.label == "Table of Contents"

    idx = IndexContent(term="test", page_refs=["1", "2"])
    assert idx.term == "test"

    ff = FormFieldContent(field_name="name", field_type="text")
    assert ff.field_name == "name"

    wm = WatermarkContent(text="DRAFT", opacity=0.5)
    assert wm.text == "DRAFT"

    mc = MacroContent(macro_language="vba", code="Sub Test()")
    assert mc.macro_language == "vba"

    sdt = StructuredDocumentTagContent(tag_type="richText", title="Field")
    assert sdt.title == "Field"

    cap = CaptionContent(label="Figure 1", text="A caption")
    assert cap.label == "Figure 1"

    pr = PageReferenceContent(target_id="page1")
    assert pr.target_id == "page1"

    sb = SectionBreakContent(break_type="nextPage")
    assert sb.break_type == "nextPage"


def test_logical_content_union_includes_new_types():
    hc = HeaderContent()
    fc = FooterContent()
    toc = TOCContent()
    idx = IndexContent()
    ff = FormFieldContent()
    wm = WatermarkContent()
    mc = MacroContent()
    cap = CaptionContent()
    pr = PageReferenceContent()
    sb = SectionBreakContent()
    assert hc is not None
    assert fc is not None
    assert toc is not None
    assert idx is not None
    assert ff is not None
    assert wm is not None
    assert mc is not None
    assert cap is not None
    assert pr is not None
    assert sb is not None
