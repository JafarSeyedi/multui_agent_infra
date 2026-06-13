# engines/document/parsers/docx_parser/docx_parser.py
"""
Main DOCX Parser - Converts DOCX files to USDM format.
Orchestrates extraction and conversion from DOCX to USDMDocument.
"""
import hashlib
import json
import re
import uuid
from datetime import datetime
from typing import Any
from typing import BinaryIO
from typing import cast

from ....models.base import BinaryEncoding
from ....models.base import BinaryPayload
from ....models.base import CompressionMethod
from ....models.base import ElementType
from ....models.exceptions import DocumentParseError
from ....models.media_types import MEDIA_TYPES
from ....models.usdm_models import AnnotationObject
from ....models.usdm_models import BookmarkContent
from ....models.usdm_models import CharacterStyle
from ....models.usdm_models import ChartAxisContent
from ....models.usdm_models import ChartContent
from ....models.usdm_models import ChartSeriesContent
from ....models.usdm_models import ColumnBreakContent
from ....models.usdm_models import CommentContent
from ....models.usdm_models import CrossReference
from ....models.usdm_models import DataContent
from ....models.usdm_models import DocumentElement
from ....models.usdm_models import DrawingContent
from ....models.usdm_models import EndnoteContent
from ....models.usdm_models import FooterContent
from ....models.usdm_models import FootnoteContent
from ....models.usdm_models import FormFieldContent
from ....models.usdm_models import HeaderContent
from ....models.usdm_models import HeadingContent
from ....models.usdm_models import ImageContent
from ....models.usdm_models import ImageObject
from ....models.usdm_models import LineBreakContent
from ....models.usdm_models import LinkContent
from ....models.usdm_models import ListContent
from ....models.usdm_models import ListItemContent
from ....models.usdm_models import ListStyle
from ....models.usdm_models import LogicalElement
from ....models.usdm_models import Page
from ....models.usdm_models import PageBreakContent
from ....models.usdm_models import PageReferenceContent
from ....models.usdm_models import ParagraphContent
from ....models.usdm_models import ParagraphStyle
from ....models.usdm_models import QuoteContent
from ....models.usdm_models import RichTextContent
from ....models.usdm_models import RichTextSpan
from ....models.usdm_models import Section
from ....models.usdm_models import StyleSheet
from ....models.usdm_models import TableCell
from ....models.usdm_models import TableContent
from ....models.usdm_models import TableRow
from ....models.usdm_models import TableStyle
from ....models.usdm_models import TextRun
from ....models.usdm_models import TOCContent
from ....models.usdm_models import USDMDocument
from ....models.usdm_models import VectorPath
from ....models.usdm_models import WatermarkContent
from .docx_extractor import DOCXExtractor
from .docx_models import DOCXBreak
from .docx_models import DOCXChartData
from .docx_models import DOCXComment
from .docx_models import DOCXDocument
from .docx_models import DOCXDrawing
from .docx_models import DOCXField
from .docx_models import DOCXFootnoteEndnote
from .docx_models import DOCXHeaderFooter
from .docx_models import DOCXParagraph
from .docx_models import DOCXSection
from .docx_models import DOCXStyle
from .docx_models import DOCXTab
from .docx_models import DOCXTable
from .docx_models import DOCXTextRun
from .docx_models import DOCXTOCField
from .docx_models import DOCXWatermark
from .docx_models import ParagraphAlignment
from .docx_models import TextDirection
from .docx_models import VerticalAlignment
from .docx_models import DOCXMath

from .docx_annotation import DOCXAnnotation
from .docx_content import DOCXContent
from .docx_field_drawing import DOCXFieldDrawing

from .docx_parser_sections import DOCXParserSections
from .docx_parser_utils import DOCXParserUtils
from .docx_style import DOCXStyleConverter


class DOCXParser(
    DOCXParserSections,
    DOCXParserUtils,
    DOCXStyleConverter,
    DOCXContent,
    DOCXAnnotation,
    DOCXFieldDrawing,
):
    """
    Parser for DOCX files that produces USDMDocument objects.
    
    The parser uses a two-phase approach:
    1. Extraction: DOCX → DOCXDocument (intermediate model)
    2. Conversion: DOCXDocument → USDMDocument (target model)
    """

    def __init__(
        self,
        encoding: BinaryEncoding = BinaryEncoding.BASE64,
        compression: CompressionMethod = CompressionMethod.NONE,
        extract_track_changes: bool = False,
        extract_comments: bool = True,
        extract_hidden_text: bool = False,
    ):
        """
        Initialize the DOCX parser.
        
        Args:
            encoding: Binary encoding method for extracted binaries
            compression: Compression method for binary data
            extract_track_changes: Whether to include revision tracking content
            extract_comments: Whether to extract comments
            extract_hidden_text: Whether to include hidden text
        """
        self.encoding = encoding
        self.compression = compression
        self.extract_track_changes = extract_track_changes
        self.extract_comments = extract_comments
        self.extract_hidden_text = extract_hidden_text

        self._extractor: DOCXExtractor | None = None
        self._docx_doc: DOCXDocument | None = None

        # Conversion state
        self._element_counter = 0
        self._style_sheet: StyleSheet | None = None
        self._list_numbering_stack: list[dict[str, Any]] = []

        # Bookmark tracking
        self._bookmarks: dict[str, str] = {}  # bookmark_id -> element_id
        self._pending_bookmarks: list[tuple[str, int]] = []  # (bookmark_id, position)

        # Footnote/endnote tracking
        self._footnote_counter = 0
        self._endnote_counter = 0
        self._footnote_elements: list[LogicalElement] = []
        self._endnote_elements: list[LogicalElement] = []


    def _reset(self) -> None:
        """Reset internal state after parsing."""
        self._extractor = None
        self._docx_doc = None
        self._element_counter = 0
        self._style_sheet = None
        self._list_numbering_stack = []
        self._bookmarks = {}
        self._pending_bookmarks = []
        self._footnote_counter = 0
        self._endnote_counter = 0
        self._footnote_elements = []
        self._endnote_elements = []

    def _generate_element_id(self) -> str:
        """Generate a unique element ID."""
        self._element_counter += 1
        return f"elem_{self._element_counter}"

    def parse(self, file_path: str) -> USDMDocument:
        """
        Parse a DOCX file from a file path.
        
        Args:
            file_path: Path to the DOCX file
            
        Returns:
            USDMDocument object
            
        Raises:
            DocumentParseError: If parsing fails
        """
        try:
            self._extractor = DOCXExtractor(
                file_path=file_path,
                encoding=self.encoding
            )
            self._docx_doc = self._extractor.extract()
            return self._convert_to_usdm(file_path)
        except Exception as e:
            raise DocumentParseError(f"Failed to parse DOCX file: {e}") from e
        finally:
            self._reset()

    def parse_bytes(self, data: bytes, filename: str = "document.docx") -> USDMDocument:
        """
        Parse a DOCX file from bytes.
        
        Args:
            data: Raw bytes of the DOCX file
            filename: Original filename for metadata
            
        Returns:
            USDMDocument object
            
        Raises:
            DocumentParseError: If parsing fails
        """
        try:
            self._extractor = DOCXExtractor(
                file_bytes=data,
                encoding=self.encoding
            )
            self._docx_doc = self._extractor.extract()
            return self._convert_to_usdm(filename)
        except Exception as e:
            raise DocumentParseError(f"Failed to parse DOCX bytes: {e}") from e
        finally:
            self._reset()

    def parse_fileobj(self, file_obj: BinaryIO, filename: str = "document.docx") -> USDMDocument:
        """
        Parse a DOCX file from a file-like object.
        
        Args:
            file_obj: File-like object containing DOCX data
            filename: Original filename for metadata
            
        Returns:
            USDMDocument object
            
        Raises:
            DocumentParseError: If parsing fails
        """
        try:
            self._extractor = DOCXExtractor(
                file_obj=file_obj,
                encoding=self.encoding
            )
            self._docx_doc = self._extractor.extract()
            return self._convert_to_usdm(filename)
        except Exception as e:
            raise DocumentParseError(f"Failed to parse DOCX file object: {e}") from e
        finally:
            self._reset()

    # ============================================================
    # CONVERSION TO USDM
    # ============================================================

    def _convert_to_usdm(self, source_name: str) -> USDMDocument:
        """Convert the intermediate DOCXDocument to USDMDocument."""
        if self._docx_doc is None:
            raise DocumentParseError("No document has been extracted")

        # Generate document ID
        doc_id = self._generate_document_id(source_name)

        # Build style sheet
        self._style_sheet = self._convert_styles()

        # Add list styles with override support (replaces basic list styles)
        list_styles = self._convert_list_styles_with_overrides()
        self._style_sheet.list_styles.clear()
        self._style_sheet.list_styles.update(list_styles)

        # Build logical elements
        logical_elements = self._convert_body_to_logical_elements()

        # Add headers and footers
        if self._docx_doc and self._docx_doc.headers:
            header_elements = self._convert_headers()
            logical_elements.extend(header_elements)

        if self._docx_doc and self._docx_doc.footers:
            footer_elements = self._convert_footers()
            logical_elements.extend(footer_elements)

        # Add TOC fields
        if self._docx_doc and self._docx_doc.toc_fields:
            toc_elements = self._convert_toc_fields()
            logical_elements.extend(toc_elements)

        # Add watermarks
        if self._docx_doc and self._docx_doc.watermarks:
            watermark_elements = self._convert_watermarks()
            logical_elements.extend(watermark_elements)

        # Add chart XML parts
        if self._docx_doc and self._docx_doc.chart_data:
            chart_elements = self._convert_chart_xml_parts()
            logical_elements.extend(chart_elements)

        # Add footnotes and endnotes if extracted
        if self.extract_comments:
            footnote_elements = self._convert_footnotes()
            endnote_elements = self._convert_endnotes()
            self._convert_comments()

            # Append to logical elements or store separately
            self._footnote_elements = footnote_elements
            self._endnote_elements = endnote_elements

        # Build sections
        sections = self._convert_sections(logical_elements)

        # Link headers/footers to sections
        sections = self._link_headers_footers_to_sections(sections)

        # Build pages (if page layout information is available)
        pages = self._build_pages(logical_elements)

        # Build document elements (flat list for compatibility)
        elements = self._flatten_logical_elements(logical_elements)

        # Extract raw binary content if needed
        raw_binary = self._extract_raw_binary()

        # Extract raw text
        raw_text = self._extract_raw_text(logical_elements)

        # Build metadata
        metadata = self._build_metadata(source_name)

        # Create USDM document
        usdm_doc = USDMDocument(
            title=self._get_document_title(),
            document_id=doc_id,
            version="1.0",
            metadata=metadata,
            created_at=self._parse_date(self._docx_doc.core_properties.created) or datetime.now(),
            modified_at=self._parse_date(self._docx_doc.core_properties.modified) or datetime.now(),
            raw_binary=raw_binary,
            raw_text=raw_text,
            binary_encoding=self.encoding,
            compression_method=self.compression,
            media_type=MEDIA_TYPES["docx"],
            file_extension=".docx",
            sections=sections,
            pages=pages,
            elements=elements,
            logical_elements=logical_elements,
            stylesheet=self._style_sheet or StyleSheet(),
            is_valid=True,
        )

        return usdm_doc

    def _convert_body_to_logical_elements(self) -> list[LogicalElement]:
        """Convert document body to logical elements."""
        elements = []
        assert self._docx_doc is not None, "Document not extracted"
        for item in self._docx_doc.body:
            if isinstance(item, DOCXParagraph):
                para: DOCXParagraph = item
                elem = self._convert_paragraph(para)
                if elem:
                    elements.append(elem)
            elif isinstance(item, DOCXTable):
                table: DOCXTable = item
                elem = self._convert_table(table)
                if elem:
                    elements.append(elem)
            elif isinstance(item, DOCXSection):
                elements.append(self._convert_page_break())

        # Post-process to merge consecutive lists
        elements = self._merge_consecutive_lists(elements)

        return elements

    def _convert_paragraph(self, para: DOCXParagraph) -> LogicalElement | None:
        """Convert a DOCX paragraph to a USDM logical element."""
        if not para.content.items and not para.properties.numbering_id:
            return None

        if para.is_deletion and not self.extract_track_changes:
            return None

        # Check for breaks first
        for item in para.content.items:
            if isinstance(item, DOCXBreak):
                if item.break_type == "page":
                    return self._convert_page_break()
                elif item.break_type == "column":
                    return self._convert_column_break()

        # Check for bookmark start/end
        # (Handled separately in a real implementation)

        if para.properties.outline_level is not None:
            return self._convert_heading(para)

        if para.properties.numbering_id:
            return self._convert_list_item(para)

        return self._convert_regular_paragraph(para)

    def _convert_heading(self, para: DOCXParagraph) -> LogicalElement:
        """Convert a heading paragraph."""
        level = para.properties.outline_level or 0
        rich_text = self._convert_run_content_to_rich_text(para.content)

        text_dir = "rtl" if para.properties.text_direction == TextDirection.RTL else "ltr"

        content = HeadingContent(
            level=level + 1,
            text=rich_text
        )

        return LogicalElement(
            element_id=self._generate_element_id(),
            element_type=ElementType.HEADING,
            content=content,
            metadata={
                "style_id": para.properties.style_id,
                "style_name": para.properties.style_name,
                "level": level + 1,
                "text_direction": text_dir,
            }
        )

    def _convert_regular_paragraph(self, para: DOCXParagraph) -> LogicalElement:
        """Convert a regular paragraph."""
        rich_text = self._convert_run_content_to_rich_text(para.content)

        content = ParagraphContent(
            text=rich_text,
            style=para.properties.style_id
        )

        text_dir = "rtl" if para.properties.text_direction == TextDirection.RTL else "ltr"

        return LogicalElement(
            element_id=self._generate_element_id(),
            element_type=ElementType.PARAGRAPH,
            content=content,
            metadata={
                "style_id": para.properties.style_id,
                "style_name": para.properties.style_name,
                "alignment": para.properties.alignment.value if para.properties.alignment else None,
                "text_direction": text_dir,
            }
        )

    def _convert_list_item(self, para: DOCXParagraph) -> LogicalElement:
        """Convert a list item paragraph with override-aware numbering."""
        assert self._docx_doc is not None, "Document not extracted"
        rich_text = self._convert_run_content_to_rich_text(para.content)

        text_dir = "rtl" if para.properties.text_direction == TextDirection.RTL else "ltr"

        para_elem = LogicalElement(
            element_id=self._generate_element_id(),
            element_type=ElementType.PARAGRAPH,
            content=ParagraphContent(text=rich_text, style=para.properties.style_id),
            metadata={"text_direction": text_dir}
        )

        content = ListItemContent(
            elements=[para_elem]
        )

        num_id = para.properties.numbering_id
        level = para.properties.numbering_level or 0

        numbering_info: dict[str, Any] = {}
        override_info: dict[str, Any] = {}
        if num_id and num_id in self._docx_doc.numbering_instances:
            instance = self._docx_doc.numbering_instances[num_id]
            abs_id = instance.abstract_definition_id

            # Check for overrides first
            if level in instance.levels_overrides:
                override_lvl = instance.levels_overrides[level]
                override_info = {
                    "is_override": True,
                    "format": override_lvl.format,
                    "start": override_lvl.start,
                    "text_template": override_lvl.text_template,
                }
                numbering_info["override"] = override_info

            if level in instance.start_overrides:
                numbering_info["start_override"] = instance.start_overrides[level]

            if abs_id in self._docx_doc.numbering_definitions:
                definition = self._docx_doc.numbering_definitions[abs_id]
                if level in definition.levels:
                    lvl_def = definition.levels[level]
                    numbering_info.update({
                        "num_id": num_id,
                        "level": level,
                        "format": lvl_def.format,
                        "start": lvl_def.start,
                        "text_template": lvl_def.text_template,
                        "alignment": lvl_def.alignment.value if lvl_def.alignment else "left",
                        "indent_left": lvl_def.indent_left,
                        "indent_hanging": lvl_def.indent_hanging,
                        "font_name": lvl_def.font_name,
                        "font_size": lvl_def.font_size,
                        "bold": lvl_def.bold,
                        "italic": lvl_def.italic,
                        "is_legal": lvl_def.is_legal,
                    })

        return LogicalElement(
            element_id=self._generate_element_id(),
            element_type=ElementType.LIST_ITEM,
            content=content,
            metadata={
                "style_id": para.properties.style_id,
                "numbering": numbering_info,
                "level": level,
                "text_direction": text_dir,
            }
        )

    def _convert_run_content_to_rich_text(self, content: Any) -> RichTextContent:
        """Convert DOCX run content to USDM RichTextContent."""
        from .docx_models import DOCXRunContent

        if not isinstance(content, DOCXRunContent):
            return RichTextContent(spans=[])

        spans: list[RichTextSpan] = []

        for item in content.items:
            if isinstance(item, DOCXTextRun):
                span = self._convert_text_run_to_span(item)
                if span:
                    spans.append(span)
            elif isinstance(item, DOCXField):
                # Convert field to data content or inline
                field_result = self._convert_advanced_field(item)
                if field_result:
                    if isinstance(field_result, (DataContent, TOCContent)):
                        value = getattr(field_result, 'value', None)
                        label = getattr(field_result, 'label', None)
                        text_value = str(value if value else label if label else "")
                        if text_value:
                            spans.append(RichTextSpan(
                                text=text_value,
                                character_style=None
                            ))
                        else:
                            spans.append(RichTextSpan(
                                text="",
                                character_style=None
                            ))
                    elif isinstance(field_result, LinkContent):
                        spans.append(RichTextSpan(
                            text=self._extract_text_from_rich_text(field_result.text),
                            character_style=None,
                            href=field_result.url
                        ))
                    elif isinstance(field_result, PageReferenceContent):
                        spans.append(RichTextSpan(
                            text=field_result.display_text or "",
                            character_style=None,
                            metadata={"page_ref": field_result.target_id}
                        ))
                    elif isinstance(field_result, FormFieldContent):
                        spans.append(RichTextSpan(
                            text=field_result.value or field_result.placeholder or "",
                            character_style=None
                        ))
                    elif isinstance(field_result, CrossReference):
                        spans.append(RichTextSpan(
                            text=field_result.context or "",
                            character_style=None
                        ))
                    elif hasattr(field_result, 'value'):
                        spans.append(RichTextSpan(
                            text=str(field_result.value),
                            character_style=None
                        ))
                elif item.result and isinstance(item.result, str):
                    spans.append(RichTextSpan(
                        text=item.result,
                        character_style=None
                    ))
            elif isinstance(item, DOCXTab):
                spans.append(RichTextSpan(text="\t"))
            elif isinstance(item, DOCXBreak):
                if item.break_type == "line":
                    spans.append(RichTextSpan(text="\n"))

        return RichTextContent(spans=spans)

    def _convert_text_run_to_span(self, run: DOCXTextRun) -> RichTextSpan | None:
        """Convert a DOCX text run to a RichTextSpan."""
        if run.is_deletion and not self.extract_track_changes:
            return None

        if not run.text:
            return None

        style_props: list[str] = []
        if run.properties.bold:
            style_props.append("bold")
        if run.properties.italic:
            style_props.append("italic")
        if run.properties.underline:
            style_props.append("underline")

        char_style = "_".join(style_props) if style_props else None

        # Check for math content
        math_content = None
        additional_properties=getattr(run.properties, 'additional_properties', {})
        if 'math' in additional_properties:
            math_content = additional_properties.get('math')

        # Check for footnote/endnote reference
        additional_properties.get('footnote_ref')
        additional_properties.get('endnote_ref')

        href = additional_properties.get('hyperlink_rel_id')
        if not href:
            href = additional_properties.get('hyperlink_anchor')

        return RichTextSpan(
            text=run.text,
            character_style=char_style,
            code=False,
            background=run.properties.highlight,
            href=href,
            math=math_content,
        )

    def _extract_paragraph_text(self, para: DOCXParagraph) -> str:
        """Extract plain text from a paragraph."""
        texts: list[str] = []
        for item in para.content.items:
            if isinstance(item, DOCXTextRun):
                if item.text:
                    texts.append(item.text)
            elif isinstance(item, DOCXField) and item.result and isinstance(item.result, str):
                texts.append(item.result)
            elif isinstance(item, DOCXTab):
                texts.append("\t")
            elif isinstance(item, DOCXBreak) and item.break_type == "line":
                texts.append("\n")
        return "".join(texts)

    # ============================================================
    # PAGE BREAK CONVERSION
    # ============================================================

    def _convert_page_break(self) -> LogicalElement:
        """
        Convert a page break to a PageBreakContent logical element.
        
        Returns:
            LogicalElement with PageBreakContent
        """
        return LogicalElement(
            element_id=self._generate_element_id(),
            element_type=ElementType.PAGE_BREAK,
            content=PageBreakContent(),
            metadata={
                "break_type": "page"
            }
        )

    # ============================================================
    # LINE BREAK CONVERSION
    # ============================================================

    def _convert_line_break(self, break_obj: DOCXBreak | None = None) -> LogicalElement:
        """
        Convert a line break to a LineBreakContent logical element.
        
        Args:
            break_obj: Optional DOCXBreak object with additional properties
            
        Returns:
            LogicalElement with LineBreakContent
        """
        metadata = {"break_type": "line"}

        if break_obj:
            if break_obj.clear:
                metadata["clear"] = break_obj.clear

        return LogicalElement(
            element_id=self._generate_element_id(),
            element_type=ElementType.LINE_BREAK,
            content=LineBreakContent(),
            metadata=metadata
        )

    # ============================================================
    # COLUMN BREAK CONVERSION
    # ============================================================

    def _convert_column_break(self) -> LogicalElement:
        """
        Convert a column break to a ColumnBreakContent logical element.
        
        Returns:
            LogicalElement with ColumnBreakContent
        """
        return LogicalElement(
            element_id=self._generate_element_id(),
            element_type=ElementType.COLUMN_BREAK,
            content=ColumnBreakContent(),
            metadata={
                "break_type": "column"
            }
        )

    # ============================================================
    # BOOKMARK CONVERSION
    # ============================================================

    def _convert_bookmark(self, bookmark_id: str, bookmark_name: str,
                          position: int) -> LogicalElement:
        """
        Convert a bookmark to a BookmarkContent logical element.
        
        Args:
            bookmark_id: Internal bookmark ID
            bookmark_name: User-defined bookmark name
            position: Position in document (for ordering)
            
        Returns:
            LogicalElement with BookmarkContent
        """
        # Store bookmark reference for cross-references
        element_id = self._generate_element_id()
        self._bookmarks[bookmark_name] = element_id

        content = BookmarkContent(
            name=bookmark_name,
            text=None  # Could be populated with surrounding text
        )

        return LogicalElement(
            element_id=element_id,
            element_type=ElementType.BOOKMARK,
            content=content,
            metadata={
                "bookmark_id": bookmark_id,
                "bookmark_name": bookmark_name,
                "position": position
            }
        )

    def _process_bookmarks_in_paragraph(self, para: DOCXParagraph) -> list[LogicalElement]:
        """
        Process bookmarks within a paragraph.
        
        Args:
            para: DOCX paragraph containing bookmarks
            
        Returns:
            List of bookmark logical elements
        """
        bookmarks: list[LogicalElement] = []

        # This would require tracking bookmarkStart and bookmarkEnd
        # in the DOCXExtractor. For now, return empty list.

        return bookmarks

    # ============================================================
    # FOOTNOTE CONVERSION
    # ============================================================

    def _convert_footnotes(self) -> list[LogicalElement]:
        """
        Convert all footnotes to FootnoteContent logical elements.
        
        Returns:
            List of LogicalElement with FootnoteContent
        """
        footnotes: list[LogicalElement] = []
        assert self._docx_doc is not None, "Document not extracted"
        for note_id, footnote in self._docx_doc.footnotes.items():
            footnote_elem = self._convert_single_footnote(footnote)
            if footnote_elem:
                footnotes.append(footnote_elem)

        return footnotes

    def _convert_single_footnote(self, footnote: DOCXFootnoteEndnote) -> LogicalElement | None:
        """
        Convert a single footnote to a FootnoteContent logical element.
        
        Args:
            footnote: DOCX footnote object
            
        Returns:
            LogicalElement with FootnoteContent or None
        """
        if not footnote.content:
            return None

        self._footnote_counter += 1

        # Convert footnote paragraphs to logical elements
        note_elements = []
        reference_text = None

        for para in footnote.content:
            # Check for reference mark
            for item in para.content.items:
                if isinstance(item, DOCXTextRun):
                    if item.text and item.text.strip().isdigit():
                        reference_text = item.text.strip()
                        break

            elem = self._convert_paragraph(para)
            if elem:
                note_elements.append(elem)

        content = FootnoteContent(
            note_id=footnote.note_id,
            elements=note_elements,
            reference_text=reference_text or str(self._footnote_counter)
        )

        return LogicalElement(
            element_id=self._generate_element_id(),
            element_type=ElementType.FOOTNOTE,
            content=content,
            metadata={
                "note_id": footnote.note_id,
                "note_type": footnote.note_type,
                "reference": reference_text or str(self._footnote_counter)
            }
        )

    # ============================================================
    # ENDNOTE CONVERSION
    # ============================================================

    def _convert_endnotes(self) -> list[LogicalElement]:
        """
        Convert all endnotes to EndnoteContent logical elements.
        
        Returns:
            List of LogicalElement with EndnoteContent
        """
        endnotes = []
        assert self._docx_doc is not None, "Document not extracted"
        for note_id, endnote in self._docx_doc.endnotes.items():
            endnote_elem = self._convert_single_endnote(endnote)
            if endnote_elem:
                endnotes.append(endnote_elem)

        return endnotes

    def _convert_single_endnote(self, endnote: DOCXFootnoteEndnote) -> LogicalElement | None:
        """
        Convert a single endnote to an EndnoteContent logical element.
        
        Args:
            endnote: DOCX endnote object
            
        Returns:
            LogicalElement with EndnoteContent or None
        """
        if not endnote.content:
            return None

        self._endnote_counter += 1

        # Convert endnote paragraphs to logical elements
        note_elements = []
        reference_text = None

        for para in endnote.content:
            # Check for reference mark
            for item in para.content.items:
                if isinstance(item, DOCXTextRun):
                    if item.text and item.text.strip().isdigit():
                        reference_text = item.text.strip()
                        break

            elem = self._convert_paragraph(para)
            if elem:
                note_elements.append(elem)

        content = EndnoteContent(
            note_id=endnote.note_id,
            elements=note_elements,
            reference_text=reference_text or str(self._endnote_counter)
        )

        return LogicalElement(
            element_id=self._generate_element_id(),
            element_type=ElementType.ENDNOTE,
            content=content,
            metadata={
                "note_id": endnote.note_id,
                "note_type": endnote.note_type,
                "reference": reference_text or str(self._endnote_counter)
            }
        )

    # ============================================================
    # COMMENT CONVERSION
    # ============================================================

    def _convert_comments(self) -> list[LogicalElement]:
        """
        Convert all comments to CommentContent logical elements.
        
        Returns:
            List of LogicalElement with CommentContent
        """
        if not self.extract_comments:
            return []

        comments = []
        assert self._docx_doc is not None, "Document not extracted"
        for comment_id, comment in self._docx_doc.comments.items():
            comment_elem = self._convert_single_comment(comment)
            if comment_elem:
                comments.append(comment_elem)

        return comments

    def _convert_single_comment(self, comment: DOCXComment) -> LogicalElement | None:
        """
        Convert a single comment to a CommentContent logical element.
        
        Args:
            comment: DOCX comment object
            
        Returns:
            LogicalElement with CommentContent or None
        """
        if not comment.content:
            return None

        # Convert comment paragraphs to logical elements
        comment_elements: list[LogicalElement] = []
        comment_text_parts: list[str] = []

        for para in comment.content:
            elem = self._convert_paragraph(para)
            if elem:
                comment_elements.append(elem)
                text = self._extract_paragraph_text(para)
                if text:
                    comment_text_parts.append(text)

        comment_text = "\n".join(comment_text_parts)

        content = CommentContent(
            comment_id=comment.comment_id,
            author=comment.author,
            date=comment.date,
            text=comment_text,
            elements=comment_elements,
            parent_id=None,
            resolved=False
        )

        return LogicalElement(
            element_id=self._generate_element_id(),
            element_type=ElementType.COMMENT,
            content=content,
            metadata={
                "comment_id": comment.comment_id,
                "author": comment.author,
                "date": comment.date,
                "initials": comment.initials
            }
        )

    # ============================================================
    # HEADER/FOOTER CONVERSION
    # ============================================================

    def _convert_headers(self) -> list[LogicalElement]:
        """Convert all headers to HeaderContent logical elements."""
        headers: list[LogicalElement] = []
        assert self._docx_doc is not None, "Document not extracted"
        for rel_id, header in self._docx_doc.headers.items():
            header_elem = self._convert_single_header(rel_id, header)
            if header_elem:
                headers.append(header_elem)
        return headers

    def _convert_single_header(self, rel_id: str, header: DOCXHeaderFooter) -> LogicalElement | None:
        """Convert a single header to HeaderContent logical element."""
        if not header.content and not header.watermarks:
            return None

        elements: list[LogicalElement] = []
        for item in header.content:
            if isinstance(item, DOCXParagraph):
                elem = self._convert_paragraph(item)
                if elem:
                    elements.append(elem)
            elif isinstance(item, DOCXTable):
                elem = self._convert_table(item)
                if elem:
                    elements.append(elem)

        page_type = header.header_footer_type

        content = HeaderContent(
            section_id=rel_id,
            page_type=page_type,
            elements=elements
        )

        return LogicalElement(
            element_id=self._generate_element_id(),
            element_type=ElementType.HEADER,
            content=content,
            metadata={
                "header_footer_id": rel_id,
                "page_type": page_type,
                "relationships": header.relationships,
            }
        )

    def _convert_footers(self) -> list[LogicalElement]:
        """Convert all footers to FooterContent logical elements."""
        footers: list[LogicalElement] = []
        assert self._docx_doc is not None, "Document not extracted"
        for rel_id, footer in self._docx_doc.footers.items():
            footer_elem = self._convert_single_footer(rel_id, footer)
            if footer_elem:
                footers.append(footer_elem)
        return footers

    def _convert_single_footer(self, rel_id: str, footer: DOCXHeaderFooter) -> LogicalElement | None:
        """Convert a single footer to FooterContent logical element."""
        if not footer.content:
            return None

        elements: list[LogicalElement] = []
        for item in footer.content:
            if isinstance(item, DOCXParagraph):
                elem = self._convert_paragraph(item)
                if elem:
                    elements.append(elem)
            elif isinstance(item, DOCXTable):
                elem = self._convert_table(item)
                if elem:
                    elements.append(elem)

        page_type = footer.header_footer_type

        content = FooterContent(
            section_id=rel_id,
            page_type=page_type,
            elements=elements
        )

        return LogicalElement(
            element_id=self._generate_element_id(),
            element_type=ElementType.FOOTER,
            content=content,
            metadata={
                "header_footer_id": rel_id,
                "page_type": page_type,
                "relationships": footer.relationships,
            }
        )

    def _link_headers_footers_to_sections(self, sections: list[Section]) -> list[Section]:
        """Link headers and footers to their corresponding sections."""
        assert self._docx_doc is not None, "Document not extracted"
        for i, section in enumerate(sections):
            if i < len(self._docx_doc.sections):
                docx_section = self._docx_doc.sections[i]
                section.metadata["header_default_id"] = docx_section.header_default_id
                section.metadata["header_first_id"] = docx_section.header_first_id
                section.metadata["header_even_id"] = docx_section.header_even_id
                section.metadata["footer_default_id"] = docx_section.footer_default_id
                section.metadata["footer_first_id"] = docx_section.footer_first_id
                section.metadata["footer_even_id"] = docx_section.footer_even_id
                if docx_section.text_direction.value == 'rtl':
                    section.metadata["text_direction"] = "rtl"
                elif docx_section.text_direction.value == 'ltr':
                    section.metadata["text_direction"] = "ltr"
                if docx_section.bidi_enabled:
                    section.metadata["bidi"] = True
                section.metadata["column_count"] = docx_section.columns.count
                if docx_section.page_borders:
                    section.metadata["page_borders"] = docx_section.page_borders
        return sections

    # ============================================================
    # TOC FIELD CONVERSION
    # ============================================================

    def _convert_toc_fields(self) -> list[LogicalElement]:
        """Convert all TOC fields to TOCContent logical elements."""
        toc_elements: list[LogicalElement] = []
        assert self._docx_doc is not None, "Document not extracted"
        for toc_field in self._docx_doc.toc_fields:
            toc_elem = self._convert_single_toc_field(toc_field)
            if toc_elem:
                toc_elements.append(toc_elem)
        return toc_elements

    def _convert_single_toc_field(self, toc_field: DOCXTOCField) -> LogicalElement | None:
        """Convert a single TOC field to TOCContent logical element."""
        level = toc_field.heading_range[1] if toc_field.heading_range else 3

        content = TOCContent(
            label="Table of Contents",
            level=level,
            anchor_id=""
        )

        metadata: dict[str, Any] = {
            "instruction": toc_field.instruction,
            "hyperlinks": toc_field.hyperlinks,
            "hide_web_layout": toc_field.hide_web_layout,
            "use_paragraph_levels": toc_field.use_paragraph_levels,
            "preserve_tabs": toc_field.preserve_tabs,
            "preserve_newlines": toc_field.preserve_newlines,
        }

        if toc_field.heading_range:
            metadata["heading_range"] = list(toc_field.heading_range)
        if toc_field.styles_included:
            metadata["styles_included"] = toc_field.styles_included
        if toc_field.level_range:
            metadata["level_range"] = toc_field.level_range
        if toc_field.switches:
            metadata["switches"] = toc_field.switches

        return LogicalElement(
            element_id=self._generate_element_id(),
            element_type=ElementType.TOC,
            content=content,
            metadata=metadata
        )

    # ============================================================
    # ADVANCED FIELD MODES CONVERSION
    # ============================================================

    def _convert_advanced_field(self, field: DOCXField) -> DataContent | TOCContent | LinkContent | PageReferenceContent | CrossReference | FormFieldContent | None:
        """Convert a DOCX field with comprehensive field type support."""
        if self._docx_doc is None:
            return None

        field_type = field.field_type.upper() if field.field_type else ""
        field_value = field.result

        if isinstance(field_value, DOCXMath):
            if field_value.root and field_value.root.text:
                field_value = field_value.root.text
            else:
                field_value = ""

        field_value_str = str(field_value) if field_value else ""

        if field_type in ("PAGE", "NUMPAGES", "SECTIONPAGES"):
            return DataContent(
                field_type=field_type,
                value=field_value_str,
                format=field.instruction
            )

        elif field_type in ("DATE", "TIME"):
            return DataContent(
                field_type=field_type,
                value=field_value_str,
                format=field.instruction
            )

        elif field_type == "SECTION":
            return DataContent(
                field_type="SECTION",
                value=field_value_str,
                format=field.instruction
            )

        elif field_type == "AUTHOR":
            return DataContent(
                field_type="AUTHOR",
                value=field_value_str or self._docx_doc.core_properties.creator or "",
                format=None
            )

        elif field_type == "TITLE":
            return DataContent(
                field_type="TITLE",
                value=field_value_str or (self._docx_doc.core_properties.title if self._docx_doc else None) or ""
            )

        elif field_type == "TOC":
            content = TOCContent(
                label="Table of Contents",
                level=3,
                anchor_id=""
            )
            return content

        elif field_type == "HYPERLINK":
            target = field.hyperlink_target or ""
            text_content = RichTextContent(
                spans=[RichTextSpan(text=field_value_str)]
            )
            return LinkContent(url=target, text=text_content)

        elif field_type in ("REF", "PAGEREF"):
            target_id = field.target_bookmark or field_value_str
            if field_type == "PAGEREF":
                return PageReferenceContent(
                    target_id=target_id,
                    display_text=field_value_str
                )
            return DataContent(
                field_type=field_type,
                value=field_value_str,
                format=field.instruction
            )

        elif field_type in ("NOTEREF", "FOOTNOTEREF"):
            target_id = field.target_bookmark or field_value_str
            return CrossReference(
                source_id="",
                target_id=target_id,
                reference_type="footnote",
                context=field_value_str
            )

        elif field_type in ("SEQ", "STYLEREF"):
            return DataContent(
                field_type=field_type,
                value=field_value_str,
                format=field.instruction
            )

        elif field_type in ("INCLUDETEXT", "LINK"):
            return DataContent(
                field_type=field_type,
                value=field_value_str,
                format=field.instruction
            )

        elif field_type in ("FORMTEXT", "FORMCHECKBOX", "FORMDD"):
            return FormFieldContent(
                field_name=field.form_field_name or "",
                field_type=field.form_field_type or field_type.lower(),
                value=field_value_str,
                default_value=field.form_field_default or ""
            )

        elif field_type == "MERGEFIELD":
            return DataContent(
                field_type="MERGEFIELD",
                value=field_value_str,
                format=field.instruction,
                metadata={"merge_field": True}
            )

        elif field_type in ("CITATION", "BIBLIOGRAPHY"):
            return DataContent(
                field_type=field_type,
                value=field_value_str,
                format=field.instruction
            )

        return DataContent(
            field_type=field_type,
            value=field_value_str,
            format=field.instruction
        )

    # ============================================================
    # WATERMARK CONVERSION
    # ============================================================

    def _convert_watermarks(self) -> list[LogicalElement]:
        """Convert all watermarks to WatermarkContent logical elements."""
        watermark_elements: list[LogicalElement] = []
        assert self._docx_doc is not None, "Document not extracted"
        for idx, watermark in enumerate(self._docx_doc.watermarks):
            wm_elem = self._convert_single_watermark(watermark, idx)
            if wm_elem:
                watermark_elements.append(wm_elem)
        return watermark_elements

    def _convert_single_watermark(self, watermark: DOCXWatermark, idx: int) -> LogicalElement | None:
        """Convert a single watermark to WatermarkContent logical element."""
        content = WatermarkContent(
            text=watermark.text or "",
            image_src=watermark.image_src,
            opacity=watermark.opacity,
            angle=watermark.angle,
            font=watermark.font or "Arial",
            font_size=watermark.font_size or 48.0,
            color=watermark.color or "#808080"
        )

        return LogicalElement(
            element_id=self._generate_element_id(),
            element_type=ElementType.WATERMARK,
            content=content,
            metadata={
                "watermark_id": watermark.watermark_id or f"wm_{idx}",
                "header_rel_id": watermark.header_rel_id,
                "layout": watermark.layout,
            }
        )

    # ============================================================
    # RTL (RIGHT-TO-LEFT) SUPPORT
    # ============================================================

