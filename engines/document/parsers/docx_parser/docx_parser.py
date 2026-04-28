# engines/document/parsers/docx_parser/docx_parser.py
"""
Main DOCX Parser - Converts DOCX files to USDM format.
Orchestrates extraction and conversion from DOCX to USDMDocument.
"""

from typing import Optional, List, Dict, Any, Union, BinaryIO, Tuple, cast
from datetime import datetime
import hashlib
import uuid
import re
import json
from .docx_extractor import DOCXExtractor
from .docx_models import (
    DOCXDocument,
    DOCXParagraph,
    DOCXTable,
    DOCXSection,
    DOCXTextRun,
    DOCXDrawing,
    DOCXField,
    DOCXBreak,
    DOCXTab,
    DOCXMath,
    DOCXMathElement,
    DOCXStyle,
    DOCXComment,
    DOCXFootnoteEndnote,
    DOCXHeaderFooter,
    DOCXNumberingDefinition,
    DOCXNumberingInstance,
    DOCXNumberingLevel,
    ParagraphAlignment,
)
from ...models.base import (
    BaseDocument,
    BinaryPayload,
    BinaryEncoding,
    CompressionMethod,
    ElementType,
)
from ...models.usdm_models import (
    USDMDocument,
    DocumentElement,
    LogicalElement,
    Section,
    Page,
    RichTextContent,
    RichTextSpan,
    ParagraphContent,
    HeadingContent,
    MathContent,
    ImageContent,
    ListContent,
    ListItemContent,
    TableContent,
    TableRow,
    TableCell,
    QuoteContent,
    StyleSheet,
    CharacterStyle,
    ParagraphStyle,
    TableStyle,
    ListStyle,
    DrawingContent,
    PageBreakContent,
    LineBreakContent,
    ColumnBreakContent,
    BookmarkContent,
    FootnoteContent,
    EndnoteContent,
    CommentContent,
    DataContent,
    EmbeddedObjectContent,
    ShapeContent,
    ChartContent,
    TextRun,
    ImageObject,
    VectorPath,
    AnnotationObject    
)
from ...models.media_types import MEDIA_TYPES
from ...models.exceptions import DocumentParseError


class DOCXParser:
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
        
        self._extractor: Optional[DOCXExtractor] = None
        self._docx_doc: Optional[DOCXDocument] = None
        
        # Conversion state
        self._element_counter = 0
        self._style_sheet: Optional[StyleSheet] = None
        self._list_numbering_stack: List[Dict[str, Any]] = []
        
        # Bookmark tracking
        self._bookmarks: Dict[str, str] = {}  # bookmark_id -> element_id
        self._pending_bookmarks: List[Tuple[str, int]] = []  # (bookmark_id, position)
        
        # Footnote/endnote tracking
        self._footnote_counter = 0
        self._endnote_counter = 0
        self._footnote_elements: List[LogicalElement] = []
        self._endnote_elements: List[LogicalElement] = []


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
    
    def _convert_table(self, table: DOCXTable) -> Optional[LogicalElement]:
        rows: List[TableRow] = []
        for row in table.rows:
            cells: List[TableCell] = []
            for cell in row.cells:
                cell_elements: List[LogicalElement] = []
                for item in cell.content:
                    if isinstance(item, DOCXParagraph):
                        para: DOCXParagraph = item
                        elem = self._convert_paragraph(para)
                        if elem:
                            cell_elements.append(elem)
                    elif isinstance(item, DOCXTable):
                        sub_table: DOCXTable = item
                        elem = self._convert_table(sub_table)
                        if elem:
                            cell_elements.append(elem)
                cells.append(TableCell(content=cell_elements))
            rows.append(TableRow(cells=cells))
        content = TableContent(rows=rows)
        return LogicalElement(
            element_id=self._generate_element_id(),
            element_type=ElementType.TABLE,
            content=content,
            metadata={"style_id": table.properties.style_id if table.properties else None}
        )
        
    def _merge_consecutive_lists(self, elements: List[LogicalElement]) -> List[LogicalElement]:
        merged: List[LogicalElement] = []
        i = 0
        while i < len(elements):
            elem = elements[i]
            if elem.element_type == ElementType.LIST_ITEM:
                # Start a potential list group
                list_items: List[ListItemContent] = []
                # Determine if this is an ordered list from the first item's metadata
                numbering = elem.metadata.get('numbering', {})
                is_ordered = not numbering.get('format', '').startswith('bullet') if numbering else False

                while i < len(elements) and elements[i].element_type == ElementType.LIST_ITEM:
                    item = elements[i]
                    if isinstance(item.content, ListItemContent):
                        list_items.append(item.content)
                    i += 1

                # Create a single ListContent element
                list_elem = LogicalElement(
                    element_id=self._generate_element_id(),
                    element_type=ElementType.LIST,
                    content=ListContent(ordered=is_ordered, items=list_items),
                    metadata={"ordered": is_ordered}
                )
                merged.append(list_elem)
            else:
                merged.append(elem)
                i += 1

        return merged

    # ============================================================
    # PUBLIC API
    # ============================================================
    
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
        
        # Build logical elements
        logical_elements = self._convert_body_to_logical_elements()
        
        # Add footnotes and endnotes if extracted
        if self.extract_comments:
            footnote_elements = self._convert_footnotes()
            endnote_elements = self._convert_endnotes()
            comment_elements = self._convert_comments()
            
            # Append to logical elements or store separately
            self._footnote_elements = footnote_elements
            self._endnote_elements = endnote_elements
        
        # Build sections
        sections = self._convert_sections(logical_elements)
        
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

    def _convert_sections(self, logical_elements: List[LogicalElement]) -> List[Section]:
        sections: List[Section] = []
        current_section_elements: List[DocumentElement] = []
        current_title: Optional[HeadingContent] = None

        for elem in logical_elements:
            # Start new section on certain conditions
            if elem.element_type == ElementType.HEADING and getattr(elem.metadata, 'level', 0) == 1:
                # Save previous section if any
                if current_section_elements:
                    sections.append(Section(title=current_title, elements=current_section_elements))
                    current_section_elements = []
                current_title = cast(HeadingContent, elem.content) if isinstance(elem.content, HeadingContent) else None
            elif elem.element_type in (ElementType.PAGE_BREAK, ElementType.SECTION_BREAK):
                if current_section_elements:
                    sections.append(Section(title=current_title, elements=current_section_elements))
                    current_section_elements = []
                current_title = None
            else:
                current_section_elements.append(DocumentElement(element_id=elem.element_id,element_type=elem.element_type,metadata=elem.metadata))

        # Final section
        if current_section_elements:
            sections.append(Section(title=current_title, elements=current_section_elements))

        return sections

    def _build_pages(self, logical_elements: List[LogicalElement]) -> List[Page]:
        pages: List[Page] = []
        current_page_objects: List[Union[TextRun, ImageObject, VectorPath, AnnotationObject]] = []
        # For now, we only split by page breaks; TextRun objects could be created elsewhere.
        # This is a simple placeholder that groups elements per page.

        page_number = 0
        for elem in logical_elements:
            if elem.element_type == ElementType.PAGE_BREAK:
                pages.append(Page(page_number=page_number, width=0, height=0, elements=current_page_objects))
                page_number += 1
                current_page_objects = []
            else:
                # In a real PDF‑like output, you'd create TextRun etc. here.
                pass

        # Last page
        if current_page_objects or page_number == 0:   # at least one page even if no breaks
            pages.append(Page(page_number=page_number, width=0, height=0, elements=current_page_objects))

        return pages

    def _flatten_logical_elements(self, logical_elements: List[LogicalElement]) -> List[DocumentElement]:
        flat: List[DocumentElement] = []

        def flatten(elem: LogicalElement):
            flat.append(DocumentElement(
                element_id=elem.element_id,
                element_type=elem.element_type,
                metadata=elem.metadata
            ))
            # Recurse into nested elements if content contains a list of LogicalElements
            content = elem.content
            if isinstance(content, ListItemContent):
                for sub in content.elements:
                    flatten(sub)
            elif isinstance(content, QuoteContent):
                for sub in content.elements:
                    flatten(sub)
            # add other containers (FootnoteContent, EndnoteContent) if needed

        for le in logical_elements:
            flatten(le)

        return flat
    
    def _generate_document_id(self, source_name: str) -> str:
        """Generate a unique document ID."""
        if self._docx_doc:
            content = str(self._docx_doc.core_properties.__dict__)
            hash_val = hashlib.sha256(content.encode()).hexdigest()[:16]
            return f"docx_{hash_val}"
        
        return f"docx_{uuid.uuid4().hex[:16]}"
    
    def _get_document_title(self) -> str:
        """Get document title from metadata."""
        assert self._docx_doc is not None, "Document not extracted"
        if self._docx_doc.core_properties.title:
            return self._docx_doc.core_properties.title
        
        # Try to extract from first heading
        for elem in self._docx_doc.body:
            if isinstance(elem, DOCXParagraph):
                if elem.properties.outline_level == 0:
                    text = self._extract_paragraph_text(elem)
                    if text:
                        return text[:100]
        
        return "Untitled Document"
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse ISO date string to datetime."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except (ValueError, TypeError):
            return None
    

    def _build_metadata(self, source_name: str) -> Dict[str, Any]:
        """Build metadata dictionary for USDM document."""
        if self._docx_doc is None:
            raise DocumentParseError("No document extracted")
        metadata: Dict[str, Any] = {
            "source": source_name,
            "parser": "DOCXParser",
            "parser_version": "1.0",
        }
        
        cp = self._docx_doc.core_properties
        if cp.creator:
            metadata["author"] = cp.creator
        if cp.subject:
            metadata["subject"] = cp.subject
        if cp.keywords:
            metadata["keywords"] = ", ".join(cp.keywords) if isinstance(cp.keywords, list) else cp.keywords
        if cp.description:
            metadata["description"] = cp.description
        if cp.category:
            metadata["category"] = cp.category

        ep = self._docx_doc.extended_properties
        if ep.pages:
            metadata["page_count"] = str(ep.pages)
        if ep.words:
            metadata["word_count"] = str(ep.words)
        if ep.characters:
            metadata["character_count"] = str(ep.characters)
        if ep.paragraphs:
            metadata["paragraph_count"] = str(ep.paragraphs)
        if ep.company:
            metadata["company"] = ep.company
        if ep.manager:
            metadata["manager"] = ep.manager
        
        if self._docx_doc.custom_properties.properties:
            metadata["custom"] = self._docx_doc.custom_properties.properties
        
        return metadata
    
    def _extract_raw_binary(self) -> Optional[BinaryPayload]:
        """Extract raw DOCX as binary payload."""
        return None
    
    def _extract_raw_text(self, logical_elements: List[LogicalElement]) -> str:
        """Extract plain text from logical elements."""
        texts = []
        
        for elem in logical_elements:
            text = self._extract_text_from_logical_element(elem)
            if text:
                texts.append(text)
        
        return "\n\n".join(texts)
    
    def _extract_text_from_logical_element(self, elem: LogicalElement) -> str:
        """Recursively extract text from a logical element."""
        if elem.element_type == ElementType.PARAGRAPH:
            if isinstance(elem.content, ParagraphContent):
                return self._extract_text_from_rich_text(elem.content.text)
        elif elem.element_type == ElementType.HEADING:
            if isinstance(elem.content, HeadingContent):
                return self._extract_text_from_rich_text(elem.content.text)
        elif elem.element_type == ElementType.LIST_ITEM:
            if isinstance(elem.content, ListItemContent):
                texts = []
                for sub_elem in elem.content.elements:
                    text = self._extract_text_from_logical_element(sub_elem)
                    if text:
                        texts.append(text)
                return " ".join(texts)
        elif elem.element_type == ElementType.QUOTE:
            if isinstance(elem.content, QuoteContent):
                texts = []
                for sub_elem in elem.content.elements:
                    text = self._extract_text_from_logical_element(sub_elem)
                    if text:
                        texts.append(text)
                return " ".join(texts)
        elif elem.element_type == ElementType.FOOTNOTE:
            if isinstance(elem.content, FootnoteContent):
                texts = []
                for sub_elem in elem.content.elements:
                    text = self._extract_text_from_logical_element(sub_elem)
                    if text:
                        texts.append(text)
                return " ".join(texts)
        
        return ""
    
    def _extract_text_from_rich_text(self, rich_text: RichTextContent) -> str:
        """Extract plain text from rich text content."""
        return "".join(span.text for span in rich_text.spans)
    
    # ============================================================
    # STYLE CONVERSION
    # ============================================================
    
    def _convert_styles(self) -> StyleSheet:
        """Convert DOCX styles to USDM StyleSheet."""
        style_sheet = StyleSheet()
        assert self._docx_doc is not None, "Document not extracted"
        for style_id, docx_style in self._docx_doc.styles.items():
            if docx_style.style_type == "character":
                char_style = self._convert_character_style(docx_style)
                if char_style:
                    style_sheet.character_styles[docx_style.name or style_id] = char_style
            
            elif docx_style.style_type == "paragraph":
                para_style = self._convert_paragraph_style(docx_style)
                if para_style:
                    style_sheet.paragraph_styles[docx_style.name or style_id] = para_style
            
            elif docx_style.style_type == "table":
                table_style = self._convert_table_style(docx_style)
                if table_style:
                    style_sheet.table_styles[docx_style.name or style_id] = table_style
        
        # Convert list styles from numbering definitions
        list_styles = self._convert_list_styles()
        style_sheet.list_styles.update(list_styles)
        
        return style_sheet
    
    def _convert_character_style(self, docx_style: DOCXStyle) -> Optional[CharacterStyle]:
        """
        Convert DOCX character style to USDM CharacterStyle with all properties.
        
        Args:
            docx_style: DOCXStyle object
            
        Returns:
            CharacterStyle object or None
        """
        if not docx_style.run_properties:
            return None
        
        props = docx_style.run_properties.properties
        additional_properties=getattr(props, 'additional_properties', {})
        # Map theme colors if used
        color = self._resolve_theme_color(
            props.color, 
            additional_properties.get('theme_color'),
            additional_properties.get('theme_tint'),
            additional_properties.get('theme_shade')
        )
        
        highlight_color = self._resolve_theme_color(
            props.highlight,
            additional_properties.get('highlight_theme_color')
        )
        
        # Build comprehensive character style
        return CharacterStyle(
            name=docx_style.name or docx_style.style_id,
            
            # Basic font properties
            bold=props.bold,
            italic=props.italic,
            underline=props.underline is not None,
            underline_type=props.underline if isinstance(props.underline, str) else None,
            
            # Color properties
            color=color,
            highlight=highlight_color,
            background=additional_properties.get('shading_fill'),
            
            # Font properties
            font=props.font_name,
            font_family=additional_properties.get('font_family'),
            font_charset=additional_properties.get('font_charset'),
            font_pitch=additional_properties.get('font_pitch'),
            size=props.font_size,
            size_cs=props.font_size_cs,  # Complex script font size
            
            # Text effects
            strike=props.strike,
            double_strike=props.double_strike,
            superscript=props.superscript,
            subscript=props.subscript,
            small_caps=props.small_caps,
            all_caps=props.all_caps,
            
            # Advanced typography
            kerning=props.kerning,
            spacing=props.spacing,
            position=props.position,  # Raised/lowered text
            
            # Effects
            shadow=props.shadow,
            outline=props.outline,
            emboss=props.emboss,
            imprint=props.imprint,
            
            # Visibility
            vanished=props.vanished,  # Hidden text
            web_hidden=props.web_hidden,
            
            # Language and proofing
            language=props.language,
            no_proof=props.no_proof,
            
            # Additional metadata
            style_id=docx_style.style_id,
            based_on=docx_style.based_on,
            next_style=docx_style.next_style,
            linked_style=docx_style.linked_style_id,
        )
    
    def _convert_paragraph_style(self, docx_style: DOCXStyle) -> Optional[ParagraphStyle]:
        """
        Convert DOCX paragraph style to USDM ParagraphStyle with borders and shading.
        
        Args:
            docx_style: DOCXStyle object
            
        Returns:
            ParagraphStyle object or None
        """
        if not docx_style.paragraph_properties:
            return None
        
        props = docx_style.paragraph_properties.properties
        additional_properties=getattr(props, 'additional_properties', {})
        
        # Alignment mapping
        alignment_map = {
            ParagraphAlignment.LEFT: "left",
            ParagraphAlignment.CENTER: "center",
            ParagraphAlignment.RIGHT: "right",
            ParagraphAlignment.BOTH: "justify",
            ParagraphAlignment.DISTRIBUTE: "justify",
        }
        
        # Convert borders
        borders: Dict[str, Dict[str, Any]] = {}
        for border_pos in ['top', 'bottom', 'left', 'right']:
            border_attr = getattr(props, f'border_{border_pos}', None)
            if border_attr:
                border_info = self._convert_border_to_style(border_attr)
                if border_info:
                    borders[border_pos] = border_info
        
        # Convert shading
        shading = None
        if props.shading_fill or props.shading_pattern:
            shading = {
                'fill': self._resolve_theme_color(
                    props.shading_fill,
                    additional_properties.get('shading_theme_color'),
                    additional_properties.get('shading_theme_tint'),
                    additional_properties.get('shading_theme_shade')
                ),
                'pattern': props.shading_pattern,
                'color': self._resolve_theme_color(
                    additional_properties.get('shading_color'),
                    additional_properties.get('shading_color_theme')
                )
            }
            # Remove None values
            shading = {k: v for k, v in shading.items() if v is not None}
        
        # Convert tabs
        tabs = []
        for tab_info in props.tabs:
            tab_style = {
                'position': tab_info.get('position'),
                'alignment': tab_info.get('alignment', 'left'),
                'leader': tab_info.get('leader', 'none')
            }
            tabs.append(tab_style)
        
        # Build comprehensive paragraph style
        return ParagraphStyle(
            name=docx_style.name or docx_style.style_id,
            
            # Alignment and spacing
            alignment=alignment_map.get(props.alignment) if props.alignment else None,
            spacing_before=props.spacing_before,
            spacing_after=props.spacing_after,
            line_spacing=props.line_spacing,
            line_spacing_rule=props.line_spacing_rule,
            
            # Indentation
            indent_left=props.indent_left,
            indent_right=props.indent_right,
            first_line_indent=props.indent_first_line,
            indent_hanging=props.indent_hanging,
            
            # Pagination
            keep_lines_together=props.keep_lines_together,
            keep_with_next=props.keep_with_next,
            page_break_before=props.page_break_before,
            widow_control=props.widow_control,
            
            # Borders and shading
            borders=borders if borders else None,
            shading=shading if shading else None,
            
            # Outline level
            outline_level=props.outline_level,
            
            # Text direction
            text_direction=props.text_direction.value if props.text_direction else 'ltr',
            
            # Tabs
            tabs=tabs if tabs else None,
            
            # Frame properties
            frame_properties=props.frame_properties,
            
            # Style inheritance
            style_id=docx_style.style_id,
            based_on=docx_style.based_on,
            next_style=docx_style.next_style,
        )

    def _convert_border_to_style(self, border_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Convert DOCX border information to style dictionary.
        
        Args:
            border_info: Border information from DOCX
            
        Returns:
            Border style dictionary
        """
        style: Dict[str, Any] = {}
        
        if 'style' in border_info:
            style['style'] = border_info['style']
        
        if 'color' in border_info:
            color = self._resolve_theme_color(
                border_info.get('color'),
                border_info.get('theme_color'),
                border_info.get('theme_tint'),
                border_info.get('theme_shade')
            )
            style['color'] = color
        
        if 'width' in border_info:
            style['width'] = border_info['width']
        
        if 'space' in border_info:
            style['space'] = border_info['space']
        
        return style if style else None
    
    
    def _convert_table_style(self, docx_style: DOCXStyle) -> Optional[TableStyle]:
        """
        Convert DOCX table style to USDM TableStyle with borders and banding.
        
        Args:
            docx_style: DOCXStyle object
            
        Returns:
            TableStyle object or None
        """
        if not docx_style.table_properties:
            return None
        
        props = docx_style.table_properties.properties
        
        # Convert borders
        borders: Dict[str, Dict[str, Any]] = {}
        border_mapping = {
            'border_top': 'top',
            'border_bottom': 'bottom',
            'border_left': 'left',
            'border_right': 'right',
            'border_inside_horizontal': 'inside_horizontal',
            'border_inside_vertical': 'inside_vertical',
        }
        
        for attr_name, border_name in border_mapping.items():
            border_attr = getattr(props, attr_name, None)
            if border_attr:
                border_info = self._convert_border_to_style(border_attr)
                if border_info:
                    borders[border_name] = border_info
        
        # Convert cell margins
        cell_margins = {}
        if props.cell_margin_default:
            for margin_pos, margin_val in props.cell_margin_default.items():
                cell_margins[margin_pos] = margin_val
        
        # Convert shading
        shading = None
        additional_properties = getattr(props, 'additional_properties', {})
        shading_info = additional_properties.get('shading')
        if shading_info:
            shading = {
                'fill': self._resolve_theme_color(
                    shading_info.get('fill'),
                    shading_info.get('theme_color'),
                    shading_info.get('theme_tint'),
                    shading_info.get('theme_shade')
                ),
                'pattern': shading_info.get('pattern'),
            }
            shading = {k: v for k, v in shading.items() if v is not None}
        
        # Build comprehensive table style
        return TableStyle(
            name=docx_style.name or docx_style.style_id,
            
            # Positioning
            alignment=props.alignment.value if props.alignment else 'left',
            indent_left=props.indent_left,
            width=props.width,
            layout_type=props.layout_type,
            
            # Borders
            borders=borders if borders else None,
            
            # Cell properties
            cell_margins=cell_margins if cell_margins else None,
            cell_spacing=props.cell_spacing,
            
            # Shading
            shading=shading if shading else None,
            
            # Banding options
            header_row=props.header_row_repeat,
            banded_rows=additional_properties.get('banded_rows', True),
            banded_columns=additional_properties.get('banded_columns', False),
            first_row=additional_properties.get('first_row_formatting'),
            last_row=additional_properties.get('last_row_formatting'),
            first_column=additional_properties.get('first_column_formatting'),
            last_column=additional_properties.get('last_column_formatting'),
            
            # Style inheritance
            style_id=docx_style.style_id,
            based_on=docx_style.based_on,
        )
    
    def _convert_list_styles(self) -> Dict[str, ListStyle]:
        """
        Convert DOCX numbering definitions to USDM ListStyle objects.
        
        Returns:
            Dictionary mapping style name to ListStyle
        """
        list_styles: Dict[str, ListStyle] = {}
        assert self._docx_doc is not None, "Document not extracted"
        for abs_id, definition in self._docx_doc.numbering_definitions.items():
            style_name = definition.name or f"ListStyle_{abs_id}"
            
            level_styles: Dict[int, Dict[str, Any]] = {}
            for level_num, level_def in definition.levels.items():
                level_styles[level_num] = {
                    "format": level_def.format,
                    "start": level_def.start,
                    "text_template": level_def.text_template,
                    "alignment": level_def.alignment.value if level_def.alignment else "left",
                    "indent_left": level_def.indent_left,
                    "indent_hanging": level_def.indent_hanging,
                    "font_name": level_def.font_name,
                    "font_size": level_def.font_size,
                    "bold": level_def.bold,
                    "italic": level_def.italic,
                }
            
            list_style = ListStyle(
                name=style_name,
                level_styles=level_styles
            )
            list_styles[style_name] = list_style
        
        return list_styles
    
    # ============================================================
    # BODY CONVERSION
    # ============================================================
    
    def _convert_body_to_logical_elements(self) -> List[LogicalElement]:
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
    
    def _convert_paragraph(self, para: DOCXParagraph) -> Optional[LogicalElement]:
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
            }
        )
    
    def _convert_regular_paragraph(self, para: DOCXParagraph) -> LogicalElement:
        """Convert a regular paragraph."""
        rich_text = self._convert_run_content_to_rich_text(para.content)
        
        content = ParagraphContent(
            text=rich_text,
            style=para.properties.style_id
        )
        
        return LogicalElement(
            element_id=self._generate_element_id(),
            element_type=ElementType.PARAGRAPH,
            content=content,
            metadata={
                "style_id": para.properties.style_id,
                "style_name": para.properties.style_name,
                "alignment": para.properties.alignment.value if para.properties.alignment else None,
            }
        )
    
    def _convert_list_item(self, para: DOCXParagraph) -> LogicalElement:
        """Convert a list item paragraph."""
        assert self._docx_doc is not None, "Document not extracted"
        rich_text = self._convert_run_content_to_rich_text(para.content)
        
        para_elem = LogicalElement(
            element_id=self._generate_element_id(),
            element_type=ElementType.PARAGRAPH,
            content=ParagraphContent(text=rich_text, style=para.properties.style_id),
            metadata={}
        )
        
        content = ListItemContent(
            elements=[para_elem]
        )
        
        num_id = para.properties.numbering_id
        level = para.properties.numbering_level or 0
        
        numbering_info = {}
        if num_id and num_id in self._docx_doc.numbering_instances:
            instance = self._docx_doc.numbering_instances[num_id]
            abs_id = instance.abstract_definition_id
            if abs_id in self._docx_doc.numbering_definitions:
                definition = self._docx_doc.numbering_definitions[abs_id]
                if level in definition.levels:
                    lvl_def = definition.levels[level]
                    numbering_info = {
                        "num_id": num_id,
                        "level": level,
                        "format": lvl_def.format,
                        "start": lvl_def.start,
                    }
        
        return LogicalElement(
            element_id=self._generate_element_id(),
            element_type=ElementType.LIST_ITEM,
            content=content,
            metadata={
                "style_id": para.properties.style_id,
                "numbering": numbering_info,
                "level": level,
            }
        )
    
    def _convert_run_content_to_rich_text(self, content: Any) -> RichTextContent:
        """Convert DOCX run content to USDM RichTextContent."""
        from .docx_models import DOCXRunContent
        
        if not isinstance(content, DOCXRunContent):
            return RichTextContent(spans=[])
        
        spans: List[RichTextSpan] = []
        
        for item in content.items:
            if isinstance(item, DOCXTextRun):
                span = self._convert_text_run_to_span(item)
                if span:
                    spans.append(span)
            elif isinstance(item, DOCXField):
                # Convert field to data content or inline
                field_content = self._convert_field(item)
                if field_content:
                    if isinstance(field_content, DataContent):
                        # For fields like PAGE, DATE - add as text
                        if field_content.value and isinstance(field_content.value, str):
                            spans.append(RichTextSpan(
                                text=field_content.value,
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
    
    def _convert_text_run_to_span(self, run: DOCXTextRun) -> Optional[RichTextSpan]:
        """Convert a DOCX text run to a RichTextSpan."""
        if run.is_deletion and not self.extract_track_changes:
            return None
        
        if not run.text:
            return None
        
        style_props: List[str] = []
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
        footnote_ref = additional_properties.get('footnote_ref')
        endnote_ref = additional_properties.get('endnote_ref')
        
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
        texts: List[str] = []
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
    
    def _convert_line_break(self, break_obj: Optional[DOCXBreak] = None) -> LogicalElement:
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
    
    def _process_bookmarks_in_paragraph(self, para: DOCXParagraph) -> List[LogicalElement]:
        """
        Process bookmarks within a paragraph.
        
        Args:
            para: DOCX paragraph containing bookmarks
            
        Returns:
            List of bookmark logical elements
        """
        bookmarks: List[LogicalElement] = []
        
        # This would require tracking bookmarkStart and bookmarkEnd
        # in the DOCXExtractor. For now, return empty list.
        
        return bookmarks
    
    # ============================================================
    # FOOTNOTE CONVERSION
    # ============================================================
    
    def _convert_footnotes(self) -> List[LogicalElement]:
        """
        Convert all footnotes to FootnoteContent logical elements.
        
        Returns:
            List of LogicalElement with FootnoteContent
        """
        footnotes: List[LogicalElement] = []
        assert self._docx_doc is not None, "Document not extracted"
        for note_id, footnote in self._docx_doc.footnotes.items():
            footnote_elem = self._convert_single_footnote(footnote)
            if footnote_elem:
                footnotes.append(footnote_elem)
        
        return footnotes
    
    def _convert_single_footnote(self, footnote: DOCXFootnoteEndnote) -> Optional[LogicalElement]:
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
    
    def _convert_endnotes(self) -> List[LogicalElement]:
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
    
    def _convert_single_endnote(self, endnote: DOCXFootnoteEndnote) -> Optional[LogicalElement]:
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
    
    def _convert_comments(self) -> List[LogicalElement]:
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
    
    def _convert_single_comment(self, comment: DOCXComment) -> Optional[LogicalElement]:
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
        comment_elements: List[LogicalElement] = []
        comment_text_parts: List[str] = []
        
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
    # FIELD CONVERSION
    # ============================================================
    
    def _convert_field(self, field: DOCXField) -> Optional[Union[DataContent, LogicalElement]]:
        """
        Convert a DOCX field to DataContent or a logical element.
        
        Args:
            field: DOCX field object
            
        Returns:
            DataContent, LogicalElement, or None
        """
        if self._docx_doc is None:
            return None        
        field_type = field.field_type.upper() if field.field_type else ""
        field_value = field.result
        if isinstance(field_value, DOCXMath):
            if field_value.root and field_value.root.text:
                field_value = field_value.root.text
            else:
                field_value = ""
        # Handle different field types
        if field_type in ("PAGE", "NUMPAGES", "SECTIONPAGES"):
            return DataContent(
                field_type=field_type,
                value=str(field_value),
                format=field.instruction
            )
        
        elif field_type == "DATE":
            return DataContent(
                field_type="DATE",
                value=str(field_value),
                format=field.instruction
            )
        
        elif field_type == "TIME":
            return DataContent(
                field_type="TIME",
                value=str(field_value),
                format=field.instruction
            )
        
        elif field_type == "AUTHOR":
            return DataContent(
                field_type="AUTHOR",
                value=str(field_value or self._docx_doc.core_properties.creator or ""),
                format=None
            )
        
        elif field_type == "TITLE":
            return DataContent(
                field_type="TITLE",
                value=str(field_value or (self._docx_doc.core_properties.title if self._docx_doc else None) or "")
            )
        return None
                
                
    def _convert_drawing(self, drawing: DOCXDrawing) -> Optional[LogicalElement]:
        """
        Convert a DOCX drawing to appropriate USDM logical element.
        Handles images, charts, shapes, and diagrams.
        
        Args:
            drawing: DOCXDrawing object
            
        Returns:
            LogicalElement with appropriate content type
        """
        if drawing.drawing_type == "image":
            return self._convert_image_drawing(drawing)
        elif drawing.drawing_type == "chart":
            return self._convert_chart_drawing(drawing)
        elif drawing.drawing_type == "shape":
            return self._convert_shape_drawing(drawing)
        elif drawing.drawing_type == "diagram":
            return self._convert_diagram_drawing(drawing)
        else:
            # Fallback to image
            return self._convert_image_drawing(drawing)


    def _convert_image_drawing(self, drawing: DOCXDrawing) -> Optional[LogicalElement]:
        """
        Convert an image drawing to ImageContent.
        
        Args:
            drawing: DOCXDrawing object of type 'image'
            
        Returns:
            LogicalElement with ImageContent
        """
        # Get image data from binary parts
        image_data = None
        assert self._docx_doc is not None, "Document not extracted"
        if drawing.relationship_id in self._docx_doc.binary_parts:
            image_data = self._docx_doc.binary_parts[drawing.relationship_id]
        
        # Get image dimensions
        width = None
        height = None
        if drawing.width:
            width = self._convert_emu_to_pixels(drawing.width)
        if drawing.height:
            height = self._convert_emu_to_pixels(drawing.height)
        
        content = ImageContent(
            src=f"rel:{drawing.relationship_id}",  # Reference to binary part
            width=int(width) if width else None,
            height=int(height) if height else None,
            alt=drawing.alt_text or drawing.description or drawing.name
        )
        
        return LogicalElement(
            element_id=self._generate_element_id(),
            element_type=ElementType.IMAGE,
            content=content,
            metadata={
                "relationship_id": drawing.relationship_id,
                "name": drawing.name,
                "description": drawing.description,
                "alt_text": drawing.alt_text,
                "width_emu": drawing.width,
                "height_emu": drawing.height,
                "has_image_data": image_data is not None
            }
        )

    def _convert_chart_drawing(self, drawing: DOCXDrawing) -> Optional[LogicalElement]:
        chart_content = drawing.chart
        if chart_content is None:
            # Fallback if no chart data was resolved (should not happen after extraction)
            chart_content = ChartContent(chart_type='bar', title=drawing.name)

        if drawing.width:
            chart_content.width = self._convert_emu_to_pixels(drawing.width)
        if drawing.height:
            chart_content.height = self._convert_emu_to_pixels(drawing.height)

        metadata = {
            "relationship_id": drawing.relationship_id,
            "name": drawing.name,
            "description": drawing.description,
            "width_emu": drawing.width,
            "height_emu": drawing.height,
        }

        return LogicalElement(
            element_id=self._generate_element_id(),
            element_type=ElementType.CHART,
            content=chart_content,
            metadata=metadata
        )

    def _convert_shape_drawing(self, drawing: DOCXDrawing) -> Optional[LogicalElement]:
        # Extract shape data
        content = drawing.shape
        if content is None: return None

        if drawing.width:
            content.width = self._convert_emu_to_pixels(drawing.width)
        if drawing.height:
            content.height = self._convert_emu_to_pixels(drawing.height)
        
        return LogicalElement(
            element_id=self._generate_element_id(),
            element_type=ElementType.SHAPE,
            content=content,
            metadata={
                "relationship_id": drawing.relationship_id,
                "name": drawing.name,
                "description": drawing.description,
                "width_emu": drawing.width,
                "height_emu": drawing.height,
            }
        )

    def _convert_diagram_drawing(self, drawing: DOCXDrawing) -> Optional[LogicalElement]:
        """
        Convert a diagram drawing (SmartArt) to DrawingContent.
        
        Args:
            drawing: DOCXDrawing object of type 'diagram'
            
        Returns:
            LogicalElement with DrawingContent
        """
        diagram = drawing.diagram
        if diagram is None:
            return None

        width = self._convert_emu_to_pixels(drawing.width) if drawing.width else None
        height = self._convert_emu_to_pixels(drawing.height) if drawing.height else None

        # Build a structured representation of the diagram tree
        def node_to_dict(node):
            if node is None:
                return None
            return {
                "id": node.id,
                "text": node.text,
                "shape": node.shape_type,
                "fill": node.fill_color,
                "line": node.line_color,
                "children": [node_to_dict(child) for child in node.children] if node.children else []
            }

        tree_dict = node_to_dict(diagram.root)
        vector_data = json.dumps({
            "type": diagram.layout_type or "unknown",
            "name": diagram.name or drawing.name,
            "root": tree_dict
        }, ensure_ascii=False)

        from engines.document.models.usdm_models import DrawingContent
        content = DrawingContent(vector_data=vector_data, width=width, height=height)
        metadata = {
            "relationship_id": drawing.relationship_id,
            "name": drawing.name,
            "description": drawing.description,
            "diagram_type": diagram.layout_type,
            "width_emu": drawing.width,
            "height_emu": drawing.height,
        }
        return LogicalElement(
            element_id=self._generate_element_id(),
            element_type=ElementType.DRAWING,
            content=content,
            metadata=metadata
        )

    def _convert_emu_to_pixels(self, emu: float, dpi: int = 96) -> float:
        """
        Convert EMU (English Metric Units) to pixels.
        
        Args:
            emu: Value in EMU
            dpi: Dots per inch (default 96)
            
        Returns:
            Value in pixels
        """
        # 1 EMU = 1/914400 inch
        inches = emu / 914400.0
        return inches * dpi


    def _convert_plain_text_to_rich_text(self, text: str) -> RichTextContent:
        """
        Convert plain text to RichTextContent.
        
        Args:
            text: Plain text string
            
        Returns:
            RichTextContent object
        """
        return RichTextContent(
            spans=[RichTextSpan(text=text)]
        )

    def _resolve_theme_color(
        self, 
        color_value: Optional[str],
        theme_color: Optional[str] = None,
        theme_tint: Optional[float] = None,
        theme_shade: Optional[float] = None
    ) -> Optional[str]:
        """
        Resolve a color value using theme information.
        
        Args:
            color_value: Direct color value (hex, name, or auto)
            theme_color: Theme color reference (e.g., 'accent1', 'dark1')
            theme_tint: Tint percentage (0.0 to 1.0, lightens color)
            theme_shade: Shade percentage (0.0 to 1.0, darkens color)
            
        Returns:
            Resolved hex color string or None
        """
        assert self._docx_doc is not None, "Document not extracted"
        # If direct color value is provided and not 'auto'
        if color_value and color_value.lower() != 'auto':
            return self._normalize_color_value(color_value)
        
        # If theme color is provided
        if theme_color and self._docx_doc.theme:
            theme_colors = self._docx_doc.theme.get('colors', {})
            
            if theme_color in theme_colors:
                color_info = theme_colors[theme_color]
                
                if color_info.get('type') == 'srgb':
                    base_color = color_info.get('value', '')
                elif color_info.get('type') == 'system':
                    base_color = self._get_system_color(color_info.get('value', ''))
                else:
                    base_color = color_info.get('value', '')
                
                if base_color:
                    # Apply tint (lighten)
                    if theme_tint is not None and theme_tint > 0:
                        base_color = self._apply_tint(base_color, theme_tint)
                    
                    # Apply shade (darken)
                    if theme_shade is not None and theme_shade > 0:
                        base_color = self._apply_shade(base_color, theme_shade)
                    
                    return self._normalize_color_value(base_color)
        
        # Default fallback
        return None


    def _normalize_color_value(self, color: str) -> str:
        """
        Normalize a color value to hex format.
        
        Args:
            color: Color string (hex, name, or auto)
            
        Returns:
            Normalized hex color string
        """
        if not color:
            return "#000000"
        
        color = color.strip()
        
        # Already hex
        if color.startswith('#'):
            if len(color) == 4:  # #RGB
                return f"#{color[1]*2}{color[2]*2}{color[3]*2}"
            return color
        
        # Hex without #
        if re.match(r'^[0-9A-Fa-f]{6}$', color):
            return f"#{color.upper()}"
        
        if re.match(r'^[0-9A-Fa-f]{3}$', color):
            return f"#{color[0]*2}{color[1]*2}{color[2]*2}".upper()
        
        # Named colors
        named_colors = {
            'black': '#000000',
            'white': '#FFFFFF',
            'red': '#FF0000',
            'green': '#00FF00',
            'blue': '#0000FF',
            'yellow': '#FFFF00',
            'cyan': '#00FFFF',
            'magenta': '#FF00FF',
            'gray': '#808080',
            'grey': '#808080',
            'auto': '#000000',
            'window': '#000000',
            'windowtext': '#000000',
        }
        
        if color.lower() in named_colors:
            return named_colors[color.lower()]
        
        # Default
        return "#000000"


    def _get_system_color(self, system_color: str) -> str:
        """
        Get system color mapping.
        
        Args:
            system_color: System color name
            
        Returns:
            Hex color string
        """
        system_colors = {
            'windowText': '#000000',
            'window': '#FFFFFF',
            'btnFace': '#F0F0F0',
            'btnText': '#000000',
            'highlight': '#3399FF',
            'highlightText': '#FFFFFF',
            'menuText': '#000000',
            'menu': '#FFFFFF',
            'scrollbar': '#D3D3D3',
            'inactiveCaption': '#D3D3D3',
            'activeCaption': '#3399FF',
        }
        
        return system_colors.get(system_color, '#000000')


    def _apply_tint(self, hex_color: str, tint: float) -> str:
        """
        Apply tint (lighten) to a hex color.
        
        Args:
            hex_color: Hex color string (e.g., '#FF0000')
            tint: Tint percentage (0.0 to 1.0)
            
        Returns:
            Lightened hex color string
        """
        hex_color = self._normalize_color_value(hex_color)
        
        # Parse RGB
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        
        # Apply tint: new = color + (255 - color) * tint
        r = int(r + (255 - r) * tint)
        g = int(g + (255 - g) * tint)
        b = int(b + (255 - b) * tint)
        
        return f"#{r:02X}{g:02X}{b:02X}"


    def _apply_shade(self, hex_color: str, shade: float) -> str:
        """
        Apply shade (darken) to a hex color.
        
        Args:
            hex_color: Hex color string (e.g., '#FF0000')
            shade: Shade percentage (0.0 to 1.0)
            
        Returns:
            Darkened hex color string
        """
        hex_color = self._normalize_color_value(hex_color)
        
        # Parse RGB
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        
        # Apply shade: new = color * (1 - shade)
        r = int(r * (1 - shade))
        g = int(g * (1 - shade))
        b = int(b * (1 - shade))
        
        return f"#{r:02X}{g:02X}{b:02X}"


    def _extract_theme_colors_from_document(self) -> Dict[str, Dict[str, str]]:
        """
        Extract theme colors from the document theme.
        
        Returns:
            Dictionary mapping theme color names to their values
        """
        theme_colors: Dict[str, Dict[str, str]] = {}
        assert self._docx_doc is not None, "Document not extracted"
        if not self._docx_doc.theme:
            return theme_colors
        
        colors = self._docx_doc.theme.get('colors', {})
        
        for color_name, color_info in colors.items():
            theme_colors[color_name] = {
                'type': color_info.get('type', 'srgb'),
                'value': color_info.get('value', ''),
            }
        
        return theme_colors