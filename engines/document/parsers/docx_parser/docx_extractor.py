# engines/document/parsers/docx_parser/docx_extractor.py
"""
Main extractor for DOCX documents.
Coordinates extraction of all components from a DOCX file into intermediate DOCXDocument model.
"""

# engines/document/parsers/docx_parser/docx_extractor.py
"""
Main extractor for DOCX documents.
Coordinates extraction of all components from a DOCX file into intermediate DOCXDocument model.
"""

import os
import re
import zipfile
from typing import List, Dict, Optional, Any, Tuple, Union, BinaryIO, Literal, cast
from pathlib import Path
from xml.etree import ElementTree as ET
from datetime import datetime
from io import BytesIO

from .docx_models import (
    DOCXDocument,
    DOCXParagraph,
    DOCXParagraphProperties,
    DOCXRunContent,
    DOCXTextRun,
    DOCXRunProperties,
    DOCXDrawing,
    DOCXField,
    DOCXSymbol,
    DOCXBreak,
    DOCXTab,
    DOCXTable,
    DOCXTableProperties,
    DOCXTableGrid,
    DOCXTableRow,
    DOCXTableCell,
    DOCXTableCellProperties,
    DOCXSection,
    DOCXPageSize,
    DOCXPageMargins,
    DOCXColumns,
    DOCXHeaderFooter,
    DOCXStyle,
    DOCXNumberingDefinition,
    DOCXNumberingInstance,
    DOCXNumberingLevel,
    DOCXComment,
    DOCXFootnoteEndnote,
    DOCXCoreProperties,
    DOCXExtendedProperties,
    DOCXCustomProperties,
    ParagraphAlignment,
    SectionType,
    VerticalAlignment,
    TextDirection,
    NumberingLevelSuffix,
)
from .docx_utils import (
    NS,
    xml_to_text,
    get_element_text,
    safe_find,
    safe_findall,
    get_attribute,
    extract_text_from_run,
    parse_dxa_to_points,
    parse_emu_to_pixels,
    parse_border_element,
    parse_shading_element,
    DocxUtils,  # Add this for utility class access
)
from .docx_image_extractor import DOCXImageExtractor
from .docx_style_parser import DocxStyleParser
from .docx_table_parser import DocxTableParser
from .docx_math_parser import OMMLParser
from ...models.base import BinaryEncoding

class DOCXExtractor:
    """
    Main extractor for DOCX documents.
    
    Extracts all content from a DOCX file and builds a DOCXDocument
    intermediate representation.
    """
    
    def __init__(
        self,
        file_path: Optional[str] = None,
        file_bytes: Optional[bytes] = None,
        file_obj: Optional[BinaryIO] = None,
        encoding: BinaryEncoding = BinaryEncoding.BASE64
    ):
        """
        Initialize the DOCX extractor.
        
        Args:
            file_path: Path to the DOCX file
            file_bytes: Raw bytes of the DOCX file
            file_obj: File-like object containing DOCX data
            encoding: Binary encoding method for extracted binaries
        """
        self.file_path = file_path
        self.file_bytes = file_bytes
        self.file_obj = file_obj
        self.encoding = encoding
        
        self.zip_file: Optional[zipfile.ZipFile] = None
        
        # Sub-extractors
        self.image_extractor: Optional[DOCXImageExtractor] = None
        self.style_parser: Optional[DocxStyleParser] = None
        self.table_parser: Optional[DocxTableParser] = None
        self.math_parser: Optional[OMMLParser] = None
        
        # Cache for XML documents
        self._xml_cache: Dict[str, ET.Element] = {}
        
        # Relationships
        self._relationships: Dict[str, Dict[str, str]] = {}
        
        # Numbering instances cache
        self._num_instances: Dict[str, DOCXNumberingInstance] = {}
        self._num_definitions: Dict[str, DOCXNumberingDefinition] = {}
        
        # Comments cache
        self._comments: Dict[str, DOCXComment] = {}
        
    # ============================================================
    # PUBLIC API
    # ============================================================
    
    def extract(self) -> DOCXDocument:
        """
        Extract the complete DOCX document.
        
        Returns:
            DOCXDocument object containing all extracted content
        """
        self._open_zip()
        
        try:
            # Initialize sub-parsers
            self._initialize_parsers()
            
            # Create document
            doc = DOCXDocument()
            
            # Extract metadata
            doc.core_properties = self._extract_core_properties()
            doc.extended_properties = self._extract_extended_properties()
            doc.custom_properties = self._extract_custom_properties()
            
            # Extract relationships
            self._extract_all_relationships()
            
            # Extract styles
            doc.styles = self._extract_styles()
            doc.default_paragraph_style_id, doc.default_character_style_id, doc.default_table_style_id = \
                self._extract_default_style_ids()
            
            # Extract numbering
            doc.numbering_definitions, doc.numbering_instances = self._extract_numbering()
            
            # Extract headers and footers
            doc.headers = self._extract_headers()
            doc.footers = self._extract_footers()
            
            # Extract comments and annotations
            doc.comments = self._extract_comments()
            doc.footnotes = self._extract_footnotes()
            doc.endnotes = self._extract_endnotes()
            
            # Extract main document body
            doc.body = self._extract_document_body()
            
            # Extract sections
            doc.sections = self._extract_sections()
            
            # Extract relationships (for images, hyperlinks, etc.)
            doc.relationships = self._relationships
            
            # Extract binary parts (images, embedded objects)
            doc.binary_parts = self._extract_binary_parts()
            
            # Extract settings
            doc.settings = self._extract_settings()
            
            # Extract theme and fonts
            doc.theme = self._extract_theme()
            doc.font_table = self._extract_font_table()
            
            # Extract web settings
            doc.web_settings = self._extract_web_settings()
            
            return doc
            
        finally:
            self._close_zip()
    
    def extract_document_xml(self) -> Optional[ET.Element]:
        """Extract the main document.xml as an ElementTree Element."""
        return self._get_xml_document('word/document.xml')
    
    def extract_styles_xml(self) -> Optional[ET.Element]:
        """Extract styles.xml as an ElementTree Element."""
        return self._get_xml_document('word/styles.xml')
    
    def extract_numbering_xml(self) -> Optional[ET.Element]:
        """Extract numbering.xml as an ElementTree Element."""
        return self._get_xml_document('word/numbering.xml')
    
    def get_relationship_target(self, rel_id: str, rel_type: str = 'document') -> Optional[str]:
        """
        Get the target path for a relationship ID.
        
        Args:
            rel_id: Relationship ID (e.g., 'rId4')
            rel_type: Relationship type ('document', 'header', 'footer', etc.)
            
        Returns:
            Target path or None
        """
        rels = self._relationships.get(rel_type, {})
        return rels.get(rel_id)
    
    # ============================================================
    # INITIALIZATION
    # ============================================================
    
    def _open_zip(self):
        """Open the DOCX file as a ZIP archive."""
        if self.file_path:
            self.zip_file = zipfile.ZipFile(self.file_path, 'r')
        elif self.file_bytes:
            self.zip_file = zipfile.ZipFile(BytesIO(self.file_bytes), 'r')
        elif self.file_obj:
            self.zip_file = zipfile.ZipFile(self.file_obj, 'r')
        else:
            raise ValueError("No file source provided")
    
    def _close_zip(self):
        """Close the ZIP archive."""
        if self.zip_file:
            self.zip_file.close()
            self.zip_file = None
    
    def _initialize_parsers(self):
        """Initialize sub-parsers."""
        self.image_extractor = DOCXImageExtractor(self.zip_file, self.encoding)
        self.style_parser = DocxStyleParser()
        self.table_parser = DocxTableParser()
        self.math_parser = OMMLParser()
    
    def _get_xml_document(self, path: str) -> Optional[ET.Element]:
        """
        Get an XML document from the ZIP archive.
        
        Args:
            path: Path inside the ZIP archive
            
        Returns:
            ElementTree Element or None
        """
        if path in self._xml_cache:
            return self._xml_cache[path]

        assert self.zip_file is not None, "ZIP file not opened"        
        try:
            xml_content = self.zip_file.read(path)
            root = ET.fromstring(xml_content)
            self._xml_cache[path] = root
            return root
        except (KeyError, ET.ParseError):
            return None
    
    # ============================================================
    # METADATA EXTRACTION
    # ============================================================
    
    def _extract_core_properties(self) -> DOCXCoreProperties:
        """Extract core properties from docProps/core.xml."""
        props = DOCXCoreProperties()
        
        core_xml = self._get_xml_document('docProps/core.xml')
        if core_xml is None:
            return props
        
        # Map Dublin Core elements
        ns_map = {
            'dc': 'http://purl.org/dc/elements/1.1/',
            'dcterms': 'http://purl.org/dc/terms/',
            'cp': 'http://schemas.openxmlformats.org/package/2006/metadata/core-properties',
        }
        
        props.title = get_element_text(core_xml, './/dc:title', ns_map)
        props.subject = get_element_text(core_xml, './/dc:subject', ns_map)
        props.creator = get_element_text(core_xml, './/dc:creator', ns_map)
        props.description = get_element_text(core_xml, './/dc:description', ns_map)
        props.last_modified_by = get_element_text(core_xml, './/cp:lastModifiedBy', ns_map)
        props.revision = self._parse_int(get_element_text(core_xml, './/cp:revision', ns_map))
        props.category = get_element_text(core_xml, './/cp:category', ns_map)
        props.content_status = get_element_text(core_xml, './/cp:contentStatus', ns_map)
        
        # Keywords (can be multiple)
        keywords_elem = safe_find(core_xml, './/cp:keywords', ns_map)
        if keywords_elem is not None and keywords_elem.text:
            props.keywords = [k.strip() for k in keywords_elem.text.split(',') if k.strip()]
        
        # Dates
        created_str = get_element_text(core_xml, './/dcterms:created', ns_map)
        if created_str:
            props.created = self._parse_w3c_datetime(created_str)
        
        modified_str = get_element_text(core_xml, './/dcterms:modified', ns_map)
        if modified_str:
            props.modified = self._parse_w3c_datetime(modified_str)
        
        return props
    
    def _extract_extended_properties(self) -> DOCXExtendedProperties:
        """Extract extended properties from docProps/app.xml."""
        props = DOCXExtendedProperties()
        
        app_xml = self._get_xml_document('docProps/app.xml')
        if app_xml is None:
            return props
        
        ns_map = {
            'ep': 'http://schemas.openxmlformats.org/officeDocument/2006/extended-properties',
            'vt': 'http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes',
        }
        
        props.template = get_element_text(app_xml, './/ep:Template', ns_map)
        props.manager = get_element_text(app_xml, './/ep:Manager', ns_map)
        props.company = get_element_text(app_xml, './/ep:Company', ns_map)
        props.presentation_format = get_element_text(app_xml, './/ep:PresentationFormat', ns_map)
        props.application = get_element_text(app_xml, './/ep:Application', ns_map)
        props.app_version = get_element_text(app_xml, './/ep:AppVersion', ns_map)
        
        # Numeric properties
        props.pages = self._parse_int(get_element_text(app_xml, './/ep:Pages', ns_map))
        props.words = self._parse_int(get_element_text(app_xml, './/ep:Words', ns_map))
        props.characters = self._parse_int(get_element_text(app_xml, './/ep:Characters', ns_map))
        props.characters_with_spaces = self._parse_int(get_element_text(app_xml, './/ep:CharactersWithSpaces', ns_map))
        props.lines = self._parse_int(get_element_text(app_xml, './/ep:Lines', ns_map))
        props.paragraphs = self._parse_int(get_element_text(app_xml, './/ep:Paragraphs', ns_map))
        props.total_time = self._parse_int(get_element_text(app_xml, './/ep:TotalTime', ns_map))
        
        # Boolean properties
        props.scale_crop = self._parse_bool(get_element_text(app_xml, './/ep:ScaleCrop', ns_map))
        props.links_up_to_date = self._parse_bool(get_element_text(app_xml, './/ep:LinksUpToDate', ns_map))
        props.shared_doc = self._parse_bool(get_element_text(app_xml, './/ep:SharedDoc', ns_map))
        props.hyperlinks_changed = self._parse_bool(get_element_text(app_xml, './/ep:HyperlinksChanged', ns_map))
        
        return props
    
    def _extract_custom_properties(self) -> DOCXCustomProperties:
        """Extract custom properties from docProps/custom.xml."""
        props = DOCXCustomProperties()
        
        custom_xml = self._get_xml_document('docProps/custom.xml')
        if custom_xml is None:
            return props
        
        ns_map = {
            'cp': 'http://schemas.openxmlformats.org/officeDocument/2006/custom-properties',
            'vt': 'http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes',
        }
        
        for prop_elem in safe_findall(custom_xml, './/cp:property', ns_map):
            name = prop_elem.get('name')
            if not name:
                continue
            
            # Determine value type
            value_elem = None
            for vt_type in ['vt:lpwstr', 'vt:lpstr', 'vt:i4', 'vt:r8', 'vt:bool', 'vt:filetime', 'vt:date']:
                value_elem = safe_find(prop_elem, f'.//{vt_type}', ns_map)
                if value_elem is not None:
                    break
            
            if value_elem is not None:
                value = self._parse_vt_value(value_elem)
                props.properties[name] = value
        
        return props
    
    def _parse_vt_value(self, elem: ET.Element) -> Any:
        """Parse a VT (Variant Type) value element."""
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        
        if tag in ('lpwstr', 'lpstr'):
            return elem.text or ''
        elif tag == 'i4':
            return self._parse_int(elem.text)
        elif tag == 'r8':
            return self._parse_float(elem.text)
        elif tag == 'bool':
            text = (elem.text or '').lower()
            return text == 'true' or text == '1'
        elif tag in ('filetime', 'date'):
            return elem.text
        else:
            return elem.text
    
    # ============================================================
    # RELATIONSHIPS EXTRACTION
    # ============================================================
    
    def _extract_all_relationships(self):
        """Extract all relationship files from the DOCX."""
        # Main document relationships
        self._relationships['document'] = self._extract_relationships('word/_rels/document.xml.rels')
        
        # Other parts (headers, footers, etc. will be extracted on demand)
    
    def _extract_relationships(self, rels_path: str) -> Dict[str, str]:
        """
        Extract relationships from a .rels file.
        
        Args:
            rels_path: Path to the .rels file in ZIP
            
        Returns:
            Dictionary mapping rel_id to target path
        """
        relationships: Dict[str, str] = {}
        
        rels_xml = self._get_xml_document(rels_path)
        if rels_xml is None:
            return relationships
        
        ns_map = {
            'rel': 'http://schemas.openxmlformats.org/package/2006/relationships'
        }
        
        for rel_elem in safe_findall(rels_xml, './/rel:Relationship', ns_map):
            rel_id = rel_elem.get('Id')
            target = rel_elem.get('Target')
            rel_type = rel_elem.get('Type', '')
            
            if rel_id and target:
                relationships[rel_id] = target
        
        return relationships
    
    def _get_relationships_for_part(self, part_path: str) -> Dict[str, str]:
        """
        Get relationships for a specific document part.
        
        Args:
            part_path: Path to the part (e.g., 'word/document.xml')
            
        Returns:
            Relationship dictionary
        """
        # Convert part path to rels path
        dir_name = os.path.dirname(part_path)
        base_name = os.path.basename(part_path)
        rels_path = f"{dir_name}/_rels/{base_name}.rels"
        
        if rels_path not in self._relationships:
            self._relationships[rels_path] = self._extract_relationships(rels_path)
        
        return self._relationships.get(rels_path, {})
    
    # ============================================================
    # STYLES EXTRACTION
    # ============================================================
    
    def _extract_styles(self) -> Dict[str, DOCXStyle]:
        """Extract styles from styles.xml."""
        styles_xml = self._get_xml_document('word/styles.xml')
        if styles_xml is None:
            return {}
        assert self.style_parser is not None
        return self.style_parser.parse_styles(styles_xml)
    
    def _extract_default_style_ids(self) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Extract default style IDs from styles.xml."""
        styles_xml = self._get_xml_document('word/styles.xml')
        if styles_xml is None:
            return None, None, None
        
        para_default = None
        char_default = None
        table_default = None
        
        doc_defaults = safe_find(styles_xml, './/w:docDefaults')
        if doc_defaults is not None:
            para_def = safe_find(doc_defaults, './/w:pPrDefault/w:pPr')
            if para_def is not None:
                style_elem = safe_find(para_def, './/w:pStyle')
                if style_elem is not None:
                    para_default = style_elem.get(f'{{{NS["w"]}}}val')
            
            char_def = safe_find(doc_defaults, './/w:rPrDefault/w:rPr')
            if char_def is not None:
                style_elem = safe_find(char_def, './/w:rStyle')
                if style_elem is not None:
                    char_default = style_elem.get(f'{{{NS["w"]}}}val')
        
        return para_default, char_default, table_default
    
    # ============================================================
    # NUMBERING EXTRACTION
    # ============================================================
    
    def _extract_numbering(self) -> Tuple[Dict[str, DOCXNumberingDefinition], Dict[str, DOCXNumberingInstance]]:
        """Extract numbering definitions and instances from numbering.xml."""
        num_xml = self._get_xml_document('word/numbering.xml')
        if num_xml is None:
            return {}, {}
        
        definitions: Dict[str, DOCXNumberingDefinition] = {}
        instances: Dict[str, DOCXNumberingInstance] = {}
        
        # Parse abstract numbering definitions
        for abs_num_elem in safe_findall(num_xml, './/w:abstractNum'):
            abs_id = abs_num_elem.get(f'{{{NS["w"]}}}abstractNumId')
            if abs_id:
                definition = self._parse_abstract_numbering(abs_num_elem)
                definitions[abs_id] = definition
        
        # Parse numbering instances
        for num_elem in safe_findall(num_xml, './/w:num'):
            num_id = num_elem.get(f'{{{NS["w"]}}}numId')
            if num_id:
                instance = self._parse_numbering_instance(num_elem, definitions)
                instances[num_id] = instance
        
        self._num_definitions = definitions
        self._num_instances = instances
        
        return definitions, instances
    
    def _parse_abstract_numbering(self, elem: ET.Element) -> DOCXNumberingDefinition:
        """Parse an abstract numbering definition."""
        abs_id = elem.get(f'{{{NS["w"]}}}abstractNumId', '')
        
        definition = DOCXNumberingDefinition(abstract_id=abs_id)
        
        # Name
        name_elem = safe_find(elem, './/w:name')
        if name_elem is not None:
            definition.name = name_elem.get(f'{{{NS["w"]}}}val')
        
        # Style link
        style_link_elem = safe_find(elem, './/w:styleLink')
        if style_link_elem is not None:
            definition.style_link = style_link_elem.get(f'{{{NS["w"]}}}val')
        
        # Multi-level type
        multi_level_elem = safe_find(elem, './/w:multiLevelType')
        if multi_level_elem is not None:
            val = multi_level_elem.get(f'{{{NS["w"]}}}val', '')
            definition.is_multi_level = val == 'multilevel' or val == 'hybridMultilevel'
        
        # Parse each level
        for lvl_elem in safe_findall(elem, './/w:lvl'):
            level_num = self._parse_int(lvl_elem.get(f'{{{NS["w"]}}}ilvl'))
            if level_num is not None:
                level = self._parse_numbering_level(lvl_elem, level_num)
                definition.levels[level_num] = level
        
        return definition
    
    def _parse_numbering_level(self, elem: ET.Element, level_num: int) -> DOCXNumberingLevel:
        """Parse a numbering level definition."""
        level = DOCXNumberingLevel(level=level_num)
        
        # Start value
        start_elem = safe_find(elem, './/w:start')
        if start_elem is not None:
            level.start = self._parse_int(start_elem.get(f'{{{NS["w"]}}}val')) or 1
        
        # Number format
        format_elem = safe_find(elem, './/w:numFmt')
        if format_elem is not None:
            level.format = format_elem.get(f'{{{NS["w"]}}}val', 'decimal')
        
        # Text template
        text_elem = safe_find(elem, './/w:lvlText')
        if text_elem is not None:
            level.text_template = text_elem.get(f'{{{NS["w"]}}}val', '%1.')
        
        # Alignment
        align_elem = safe_find(elem, './/w:lvlJc')
        if align_elem is not None:
            val = align_elem.get(f'{{{NS["w"]}}}val', 'left')
            level.alignment = ParagraphAlignment(val) if val in [e.value for e in ParagraphAlignment] else ParagraphAlignment.LEFT
        
        # Suffix
        suffix_elem = safe_find(elem, './/w:suff')
        if suffix_elem is not None:
            val = suffix_elem.get(f'{{{NS["w"]}}}val', 'tab')
            if val == 'space':
                level.suffix = NumberingLevelSuffix.SPACE
            elif val == 'nothing':
                level.suffix = NumberingLevelSuffix.NOTHING
            else:
                level.suffix = NumberingLevelSuffix.TAB
        
        # Indentation
        indent_elem = safe_find(elem, './/w:ind')
        if indent_elem is not None:
            level.indent_left = parse_dxa_to_points(indent_elem.get(f'{{{NS["w"]}}}left'))
            level.indent_hanging = parse_dxa_to_points(indent_elem.get(f'{{{NS["w"]}}}hanging'))
        
        # Font properties
        rpr_elem = safe_find(elem, './/w:rPr')
        if rpr_elem is not None:
            font_elem = safe_find(rpr_elem, './/w:rFonts')
            if font_elem is not None:
                level.font_name = font_elem.get(f'{{{NS["w"]}}}ascii') or font_elem.get(f'{{{NS["w"]}}}hAnsi')
            
            sz_elem = safe_find(rpr_elem, './/w:sz')
            if sz_elem is not None:
                level.font_size = parse_dxa_to_points(self._parse_int(sz_elem.get(f'{{{NS["w"]}}}val')))
            
            level.bold = safe_find(rpr_elem, './/w:b') is not None
            level.italic = safe_find(rpr_elem, './/w:i') is not None
        
        return level
    
    def _parse_numbering_instance(
        self, 
        elem: ET.Element, 
        definitions: Dict[str, DOCXNumberingDefinition]
    ) -> DOCXNumberingInstance:
        """Parse a numbering instance."""
        num_id = elem.get(f'{{{NS["w"]}}}numId', '')
        
        instance = DOCXNumberingInstance(instance_id=num_id)
        
        # Abstract numbering reference
        abs_ref_elem = safe_find(elem, './/w:abstractNumId')
        if abs_ref_elem is not None:
            instance.abstract_definition_id = abs_ref_elem.get(f'{{{NS["w"]}}}val', '')
        
        # Level overrides
        for ovr_elem in safe_findall(elem, './/w:lvlOverride'):
            level_num = self._parse_int(ovr_elem.get(f'{{{NS["w"]}}}ilvl'))
            if level_num is not None:
                # Get override level definition
                lvl_elem = safe_find(ovr_elem, './/w:lvl')
                if lvl_elem is not None:
                    level = self._parse_numbering_level(lvl_elem, level_num)
                    instance.levels_overrides[level_num] = level
                else:
                    # Just start override
                    start_ovr_elem = safe_find(ovr_elem, './/w:startOverride')
                    if start_ovr_elem is not None:
                        start_val = self._parse_int(start_ovr_elem.get(f'{{{NS["w"]}}}val'))
                        if start_val is not None and instance.abstract_definition_id:
                            # Create a level with just start override
                            base_def = definitions.get(instance.abstract_definition_id)
                            if base_def and level_num in base_def.levels:
                                level = DOCXNumberingLevel(
                                    level=level_num,
                                    start=start_val,
                                    format=base_def.levels[level_num].format,
                                    text_template=base_def.levels[level_num].text_template,
                                    alignment=base_def.levels[level_num].alignment,
                                    suffix=base_def.levels[level_num].suffix,
                                    indent_left=base_def.levels[level_num].indent_left,
                                    indent_hanging=base_def.levels[level_num].indent_hanging,
                                    font_name=base_def.levels[level_num].font_name,
                                    font_size=base_def.levels[level_num].font_size,
                                    bold=base_def.levels[level_num].bold,
                                    italic=base_def.levels[level_num].italic
                                )
                                instance.levels_overrides[level_num] = level
        
        return instance
    
    # ============================================================
    # HEADERS AND FOOTERS EXTRACTION
    # ============================================================
    
    def _extract_headers(self) -> Dict[str, DOCXHeaderFooter]:
        """Extract all headers from the document."""
        headers: Dict[str, DOCXHeaderFooter] = {}
        
        # Get header relationships from document relationships
        doc_rels = self._relationships.get('document', {})
        
        for rel_id, target in doc_rels.items():
            if 'header' in target.lower():
                header_path = f'word/{target}'
                header_xml = self._get_xml_document(header_path)
                
                if header_xml is not None:
                    header_type = self._get_header_footer_type(rel_id)
                    header = self._parse_header_footer(header_xml, rel_id, header_type)
                    headers[rel_id] = header
                    
                    # Also load relationships for this header
                    header_rels = self._get_relationships_for_part(header_path)
                    header.relationships = header_rels
        
        return headers
    
    def _extract_footers(self) -> Dict[str, DOCXHeaderFooter]:
        """Extract all footers from the document."""
        footers: Dict[str, DOCXHeaderFooter] = {}
        
        doc_rels = self._relationships.get('document', {})
        
        for rel_id, target in doc_rels.items():
            if 'footer' in target.lower():
                footer_path = f'word/{target}'
                footer_xml = self._get_xml_document(footer_path)
                
                if footer_xml is not None:
                    footer_type = self._get_header_footer_type(rel_id)
                    footer = self._parse_header_footer(footer_xml, rel_id, footer_type)
                    footers[rel_id] = footer
                    
                    # Load relationships
                    footer_rels = self._get_relationships_for_part(footer_path)
                    footer.relationships = footer_rels
        
        return footers
    
    def _get_header_footer_type(self, rel_id: str) -> Literal['default', 'first', 'even']:
        """Determine header/footer type from relationship ID."""
        if 'first' in rel_id.lower():
            return 'first'
        elif 'even' in rel_id.lower():
            return 'even'
        else:
            return 'default'
    
    def _parse_header_footer(
        self, 
        elem: ET.Element, 
        hf_id: str, 
        hf_type: Literal['default', 'first', 'even']
    ) -> DOCXHeaderFooter:
        """Parse a header or footer XML element."""
        hf = DOCXHeaderFooter(
            header_footer_id=hf_id,
            header_footer_type=hf_type
        )
        
        # Parse content (paragraphs and tables)
        content = self._parse_block_elements(elem)
        # Headers/footers should not contain DOCXSection; keep only paragraphs and tables
        hf.content = [item for item in content if isinstance(item, (DOCXParagraph, DOCXTable))]
        
        return hf
    
    # ============================================================
    # COMMENTS AND ANNOTATIONS EXTRACTION
    # ============================================================
    
    def _extract_comments(self) -> Dict[str, DOCXComment]:
        """Extract comments from comments.xml."""
        comments_xml = self._get_xml_document('word/comments.xml')
        if comments_xml is None:
            return {}
        
        comments: Dict[str, DOCXComment] = {}
        
        ns_map = {'w': NS['w']}
        
        for comment_elem in safe_findall(comments_xml, './/w:comment'):
            comment_id = comment_elem.get(f'{{{NS["w"]}}}id')
            if not comment_id:
                continue
            
            author = comment_elem.get(f'{{{NS["w"]}}}author', '')
            date = comment_elem.get(f'{{{NS["w"]}}}date', '')
            initials = comment_elem.get(f'{{{NS["w"]}}}initials')
            
            comment = DOCXComment(
                comment_id=comment_id,
                author=author,
                date=date,
                initials=initials
            )
            
            # Parse comment content (paragraphs)
            for para_elem in safe_findall(comment_elem, './/w:p'):
                para = self._parse_paragraph(para_elem)
                comment.content.append(para)
            
            comments[comment_id] = comment
        
        self._comments = comments
        return comments
    
    def _extract_footnotes(self) -> Dict[str, DOCXFootnoteEndnote]:
        """Extract footnotes from footnotes.xml."""
        return self._extract_notes('word/footnotes.xml', 'footnote')
    
    def _extract_endnotes(self) -> Dict[str, DOCXFootnoteEndnote]:
        """Extract endnotes from endnotes.xml."""
        return self._extract_notes('word/endnotes.xml', 'endnote')
    
    def _extract_notes(self, path: str, note_type: Literal['footnote', 'endnote']) -> Dict[str, DOCXFootnoteEndnote]:
        """Extract footnotes or endnotes."""
        notes_xml = self._get_xml_document(path)
        if notes_xml is None:
            return {}
        
        notes: Dict[str, DOCXFootnoteEndnote] = {}
        
        for note_elem in safe_findall(notes_xml, './/w:footnote') + safe_findall(notes_xml, './/w:endnote'):
            note_id = note_elem.get(f'{{{NS["w"]}}}id')
            if not note_id:
                continue
            
            note = DOCXFootnoteEndnote(
                note_id=note_id,
                note_type=note_type
            )
            
            # Parse note content
            for para_elem in safe_findall(note_elem, './/w:p'):
                para = self._parse_paragraph(para_elem)
                note.content.append(para)
            
            notes[note_id] = note
        
        return notes
    
    # ============================================================
    # DOCUMENT BODY EXTRACTION
    # ============================================================
    
    def _extract_document_body(self) -> List[Union[DOCXParagraph, DOCXTable, DOCXSection]]:
        """Extract the main document body content."""
        doc_xml = self._get_xml_document('word/document.xml')
        if doc_xml is None:
            return []
        
        body_elem = safe_find(doc_xml, './/w:body')
        if body_elem is None:
            return []
        
        return self._parse_block_elements(body_elem)
    
    def _parse_block_elements(self, parent_elem: ET.Element) -> List[Union[DOCXParagraph, DOCXTable, DOCXSection]]:
        """Parse block-level elements (paragraphs, tables, sections)."""
        elements: List[Union[DOCXParagraph, DOCXTable, DOCXSection]] = []
        
        for elem in parent_elem:
            tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            
            if tag == 'p':
                # Paragraph
                para = self._parse_paragraph(elem)
                elements.append(para)
                
            elif tag == 'tbl':
                # Table
                table = self._parse_table(elem)
                elements.append(table)
                
            elif tag == 'sectPr':
                # Section properties (section break)
                section = self._parse_section_properties(elem)
                section.break_type = SectionType.CONTINUOUS
                elements.append(section)
        
        return elements
    
# engines/document/parsers/docx_parser/docx_extractor.py (continued)

    def _parse_paragraph(self, elem: ET.Element) -> DOCXParagraph:
        """Parse a paragraph element."""
        para = DOCXParagraph()
        
        # Parse properties
        ppr_elem = safe_find(elem, './/w:pPr')
        if ppr_elem is not None:
            para.properties = self._parse_paragraph_properties(ppr_elem)
        
        # Parse runs and other content
        run_content = DOCXRunContent()
        
        for child in elem:
            tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
            
            if tag == 'r':
                # Text run
                text_run = self._parse_run(child)
                run_content.items.append(text_run)
                
            elif tag == 'drawing':
                # Drawing (image, chart, shape)
                drawing = self._parse_drawing(child)
                if drawing:
                    run_content.items.append(drawing)
                
            elif tag == 'fldSimple':
                # Simple field
                field = self._parse_simple_field(child)
                if field:
                    run_content.items.append(field)
                
            elif tag == 'hyperlink':
                # Hyperlink
                hyperlink_content = self._parse_hyperlink(child)
                run_content.items.extend(hyperlink_content.items)
                
            elif tag == 'oMath' or tag == 'oMathPara':
                # Math equation - store as special field for later conversion
                assert self.math_parser is not None
                math = self.math_parser.parse_math(child, is_display=(tag == 'oMathPara'))
                if math:
                    # Create a field to hold the math
                    math_field = DOCXField(
                        field_type='MATH',
                        result=math
                    )
                    run_content.items.append(math_field)
            
            elif tag == 'br':
                # Break (line, page, column)
                break_obj = self._parse_break(child)
                if break_obj:
                    run_content.items.append(break_obj)
            
            elif tag == 'tab':
                # Tab character
                run_content.items.append(DOCXTab())
            
            elif tag == 'sym':
                # Symbol
                symbol = self._parse_symbol(child)
                if symbol:
                    run_content.items.append(symbol)
        
        para.content = run_content
        
        # Check for revision tracking
        ppr_change = safe_find(elem, './/w:pPr/w:ins') or safe_find(elem, './/w:pPr/w:del')
        if ppr_change is not None:
            if ppr_change.tag.endswith('ins'):
                para.is_insertion = True
            else:
                para.is_deletion = True
            para.revision_author = ppr_change.get(f'{{{NS["w"]}}}author')
            para.revision_date = ppr_change.get(f'{{{NS["w"]}}}date')
        
        return para
    
    def _parse_paragraph_properties(self, elem: ET.Element) -> DOCXParagraphProperties:
        """Parse paragraph properties."""
        props = DOCXParagraphProperties()
        
        # Style
        style_elem = safe_find(elem, './/w:pStyle')
        if style_elem is not None:
            props.style_id = style_elem.get(f'{{{NS["w"]}}}val')
        
        # Alignment
        jc_elem = safe_find(elem, './/w:jc')
        if jc_elem is not None:
            val = jc_elem.get(f'{{{NS["w"]}}}val', 'left')
            try:
                props.alignment = ParagraphAlignment(val)
            except ValueError:
                props.alignment = ParagraphAlignment.LEFT
        
        # Indentation
        ind_elem = safe_find(elem, './/w:ind')
        if ind_elem is not None:
            props.indent_left = parse_dxa_to_points(ind_elem.get(f'{{{NS["w"]}}}left'))
            props.indent_right = parse_dxa_to_points(ind_elem.get(f'{{{NS["w"]}}}right'))
            props.indent_first_line = parse_dxa_to_points(ind_elem.get(f'{{{NS["w"]}}}firstLine'))
            props.indent_hanging = parse_dxa_to_points(ind_elem.get(f'{{{NS["w"]}}}hanging'))
        
        # Spacing
        spacing_elem = safe_find(elem, './/w:spacing')
        if spacing_elem is not None:
            props.spacing_before = parse_dxa_to_points(spacing_elem.get(f'{{{NS["w"]}}}before'))
            props.spacing_after = parse_dxa_to_points(spacing_elem.get(f'{{{NS["w"]}}}after'))
            props.line_spacing = parse_dxa_to_points(spacing_elem.get(f'{{{NS["w"]}}}line'))
            
            rule = spacing_elem.get(f'{{{NS["w"]}}}lineRule')
            if rule == 'auto':
                props.line_spacing_rule = 'auto'
            elif rule == 'exact':
                props.line_spacing_rule = 'exact'
            elif rule == 'atLeast':
                props.line_spacing_rule = 'at_least'
        
        # Pagination
        props.keep_lines_together = safe_find(elem, './/w:keepLines') is not None
        props.keep_with_next = safe_find(elem, './/w:keepNext') is not None
        props.page_break_before = safe_find(elem, './/w:pageBreakBefore') is not None
        props.widow_control = safe_find(elem, './/w:widowControl') is None  # Default is True, so False if element missing
        
        # Borders
        for border_type in ['top', 'bottom', 'left', 'right']:
            border_elem = safe_find(elem, f'.//w:{border_type[:1]}Bdr')
            if border_elem is not None:
                border_info = parse_border_element(border_elem)
                if border_info:
                    setattr(props, f'border_{border_type}', border_info)
        
        # Shading
        shading_elem = safe_find(elem, './/w:shd')
        if shading_elem is not None:
            shading_info = parse_shading_element(shading_elem)
            props.shading_fill = shading_info.get('fill')
            props.shading_pattern = shading_info.get('pattern')
        
        # Outline level (heading level)
        outline_elem = safe_find(elem, './/w:outlineLvl')
        if outline_elem is not None:
            props.outline_level = self._parse_int(outline_elem.get(f'{{{NS["w"]}}}val'))
        
        # Text direction
        text_dir_elem = safe_find(elem, './/w:textDirection')
        if text_dir_elem is not None:
            val = text_dir_elem.get(f'{{{NS["w"]}}}val', 'lrTb')
            if val == 'rl' or val == 'tbRl':
                props.text_direction = TextDirection.RTL
        
        # Numbering
        num_pr_elem = safe_find(elem, './/w:numPr')
        if num_pr_elem is not None:
            ilvl_elem = safe_find(num_pr_elem, './/w:ilvl')
            if ilvl_elem is not None:
                props.numbering_level = self._parse_int(ilvl_elem.get(f'{{{NS["w"]}}}val'))
            
            num_id_elem = safe_find(num_pr_elem, './/w:numId')
            if num_id_elem is not None:
                props.numbering_id = num_id_elem.get(f'{{{NS["w"]}}}val')
        
        # Tabs
        tabs_elem = safe_find(elem, './/w:tabs')
        if tabs_elem is not None:
            for tab_elem in safe_findall(tabs_elem, './/w:tab'):
                tab_info = {
                    'position': parse_dxa_to_points(tab_elem.get(f'{{{NS["w"]}}}pos')),
                    'alignment': tab_elem.get(f'{{{NS["w"]}}}val', 'left'),
                    'leader': tab_elem.get(f'{{{NS["w"]}}}leader', 'none')
                }
                props.tabs.append(tab_info)
        
        return props
    
    def _parse_run(self, elem: ET.Element) -> DOCXTextRun:
        """Parse a run element."""
        text_run = DOCXTextRun(text='')
        
        # Extract text
        text_parts: List[str] = []
        for t_elem in safe_findall(elem, './/w:t'):
            if t_elem.text:
                text_parts.append(t_elem.text)
        
        # Handle special characters
        for cr_elem in safe_findall(elem, './/w:cr'):
            text_parts.append('\n')
        for br_elem in safe_findall(elem, './/w:br'):
            text_parts.append('\n')
        for tab_elem in safe_findall(elem, './/w:tab'):
            text_parts.append('\t')
        
        text_run.text = ''.join(text_parts)
        
        # Parse run properties
        rpr_elem = safe_find(elem, './/w:rPr')
        if rpr_elem is not None:
            text_run.properties = self._parse_run_properties(rpr_elem)
        
        # Check for revision tracking
        if rpr_elem is not None:
            ins_elem = safe_find(rpr_elem, './/w:ins')
            if ins_elem is not None:
                text_run.is_insertion = True
                text_run.revision_author = ins_elem.get(f'{{{NS["w"]}}}author')
                text_run.revision_date = ins_elem.get(f'{{{NS["w"]}}}date')
                text_run.revision_id = self._parse_int(ins_elem.get(f'{{{NS["w"]}}}id'))
            
            del_elem = safe_find(rpr_elem, './/w:del')
            if del_elem is not None:
                text_run.is_deletion = True
                text_run.revision_author = del_elem.get(f'{{{NS["w"]}}}author')
                text_run.revision_date = del_elem.get(f'{{{NS["w"]}}}date')
                text_run.revision_id = self._parse_int(del_elem.get(f'{{{NS["w"]}}}id'))
        
        return text_run
    
    def _parse_run_properties(self, elem: ET.Element) -> DOCXRunProperties:
        """Parse run properties."""
        props = DOCXRunProperties()
        
        # Bold
        bold_elem = safe_find(elem, './/w:b')
        if bold_elem is not None:
            props.bold = bold_elem.get(f'{{{NS["w"]}}}val') != 'false'
        
        # Italic
        italic_elem = safe_find(elem, './/w:i')
        if italic_elem is not None:
            props.italic = italic_elem.get(f'{{{NS["w"]}}}val') != 'false'
        
        # Underline
        underline_elem = safe_find(elem, './/w:u')
        if underline_elem is not None:
            props.underline = underline_elem.get(f'{{{NS["w"]}}}val', 'single')
        
        # Strike through
        strike_elem = safe_find(elem, './/w:strike')
        if strike_elem is not None:
            props.strike = strike_elem.get(f'{{{NS["w"]}}}val') != 'false'
        
        # Double strike
        dstrike_elem = safe_find(elem, './/w:dstrike')
        if dstrike_elem is not None:
            props.double_strike = dstrike_elem.get(f'{{{NS["w"]}}}val') != 'false'
        
        # Superscript / Subscript
        vert_align_elem = safe_find(elem, './/w:vertAlign')
        if vert_align_elem is not None:
            val = vert_align_elem.get(f'{{{NS["w"]}}}val')
            if val == 'superscript':
                props.superscript = True
            elif val == 'subscript':
                props.subscript = True
        
        # Small caps / All caps
        small_caps_elem = safe_find(elem, './/w:smallCaps')
        if small_caps_elem is not None:
            props.small_caps = small_caps_elem.get(f'{{{NS["w"]}}}val') != 'false'
        
        caps_elem = safe_find(elem, './/w:caps')
        if caps_elem is not None:
            props.all_caps = caps_elem.get(f'{{{NS["w"]}}}val') != 'false'
        
        # Highlight
        highlight_elem = safe_find(elem, './/w:highlight')
        if highlight_elem is not None:
            props.highlight = highlight_elem.get(f'{{{NS["w"]}}}val')
        
        # Color
        color_elem = safe_find(elem, './/w:color')
        if color_elem is not None:
            props.color = color_elem.get(f'{{{NS["w"]}}}val')
        
        # Font name
        font_elem = safe_find(elem, './/w:rFonts')
        if font_elem is not None:
            props.font_name = font_elem.get(f'{{{NS["w"]}}}ascii') or font_elem.get(f'{{{NS["w"]}}}hAnsi')
        
        # Font size
        sz_elem = safe_find(elem, './/w:sz')
        if sz_elem is not None:
            sz_val = sz_elem.get(f'{{{NS["w"]}}}val')
            if sz_val is not None:
                val_int = self._parse_int(sz_val)
                if val_int is not None:
                    props.font_size = val_int / 2.0        
        
        sz_cs_elem = safe_find(elem, './/w:szCs')
        if sz_cs_elem is not None:
            sz_val = sz_cs_elem.get(f'{{{NS["w"]}}}val')
            if sz_val:
                val_int = self._parse_int(sz_val)
                if val_int is not None:
                    props.font_size_cs = val_int / 2.0        
        
        # Kerning
        kern_elem = safe_find(elem, './/w:kern')
        if kern_elem is not None:
            props.kerning = parse_dxa_to_points(kern_elem.get(f'{{{NS["w"]}}}val'))
        
        # Spacing
        spacing_elem = safe_find(elem, './/w:spacing')
        if spacing_elem is not None:
            props.spacing = parse_dxa_to_points(spacing_elem.get(f'{{{NS["w"]}}}val'))
        
        # Position (raised/lowered text)
        position_elem = safe_find(elem, './/w:position')
        if position_elem is not None:
            props.position = parse_dxa_to_points(position_elem.get(f'{{{NS["w"]}}}val'))
        
        # Language
        lang_elem = safe_find(elem, './/w:lang')
        if lang_elem is not None:
            props.language = lang_elem.get(f'{{{NS["w"]}}}val')
        
        # No proof (spell check)
        props.no_proof = safe_find(elem, './/w:noProof') is not None
        
        # Web hidden
        web_hidden_elem = safe_find(elem, './/w:webHidden')
        if web_hidden_elem is not None:
            props.web_hidden = web_hidden_elem.get(f'{{{NS["w"]}}}val') != 'false'
        
        # Shadow
        shadow_elem = safe_find(elem, './/w:shadow')
        if shadow_elem is not None:
            props.shadow = shadow_elem.get(f'{{{NS["w"]}}}val') != 'false'
        
        # Outline
        outline_elem = safe_find(elem, './/w:outline')
        if outline_elem is not None:
            props.outline = outline_elem.get(f'{{{NS["w"]}}}val') != 'false'
        
        # Emboss
        emboss_elem = safe_find(elem, './/w:emboss')
        if emboss_elem is not None:
            props.emboss = emboss_elem.get(f'{{{NS["w"]}}}val') != 'false'
        
        # Imprint
        imprint_elem = safe_find(elem, './/w:imprint')
        if imprint_elem is not None:
            props.imprint = imprint_elem.get(f'{{{NS["w"]}}}val') != 'false'
        
        # Vanished (hidden text)
        vanish_elem = safe_find(elem, './/w:vanish')
        if vanish_elem is not None:
            props.vanished = vanish_elem.get(f'{{{NS["w"]}}}val') != 'false'
        
        return props
    
    def _parse_drawing(self, elem: ET.Element) -> Optional[DOCXDrawing]:
        """Parse a drawing element (image, chart, shape)."""
        # Look for inline drawing
        inline_elem = safe_find(elem, './/wp:inline', {'wp': NS.get('wp', '')})
        if inline_elem is None:
            inline_elem = safe_find(elem, './/wp:anchor', {'wp': NS.get('wp', '')})
        
        if inline_elem is None:
            return None
        
        drawing = DOCXDrawing(relationship_id='')
        
        # Get relationship ID for image
        blip_elem = safe_find(inline_elem, './/a:blip', {'a': NS.get('a', '')})
        if blip_elem is not None:
            drawing.relationship_id = blip_elem.get(f'{{{NS.get("r", "")}}}embed', '')
        
        # Get dimensions
        extent_elem = safe_find(inline_elem, './/wp:extent', {'wp': NS.get('wp', '')})
        if extent_elem is not None:
            drawing.width = self._parse_int(extent_elem.get('cx'))
            drawing.height = self._parse_int(extent_elem.get('cy'))
        
        # Get name and description
        docpr_elem = safe_find(inline_elem, './/wp:docPr', {'wp': NS.get('wp', '')})
        if docpr_elem is not None:
            drawing.name = docpr_elem.get('name')
            drawing.description = docpr_elem.get('descr')
        
        # Get alternative text
        alt_text_elem = safe_find(inline_elem, './/a:extLst/a:ext//a16:altText', 
                                   {'a': NS.get('a', ''), 'a16': NS.get('a16', '')})
        if alt_text_elem is not None:
            drawing.alt_text = alt_text_elem.get('altText')
        
        # Determine drawing type
        graphic_elem = safe_find(inline_elem, './/a:graphic', {'a': NS.get('a', '')})
        if graphic_elem is not None:
            graphic_data = safe_find(graphic_elem, './/a:graphicData', {'a': NS.get('a', '')})
            if graphic_data is not None:
                uri = graphic_data.get('uri', '')
                if 'chart' in uri:
                    drawing.drawing_type = 'chart'
                elif 'diagram' in uri:
                    drawing.drawing_type = 'diagram'
                elif 'shape' in uri:
                    drawing.drawing_type = 'shape'
        
        return drawing
    
    def _parse_simple_field(self, elem: ET.Element) -> Optional[DOCXField]:
        """Parse a simple field element."""
        field = DOCXField(field_type='')
        
        instr = elem.get(f'{{{NS["w"]}}}instr', '')
        if instr:
            # Parse instruction (e.g., "PAGE", "DATE \@ \"MMMM d, yyyy\"")
            parts = instr.split(' ', 1)
            field.field_type = parts[0] if parts else ''
            field.instruction = parts[1] if len(parts) > 1 else None
        
        # Get field result (computed value)
        result_text: List[str] = []
        for child in elem:
            tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
            if tag == 'r':
                for t_elem in safe_findall(child, './/w:t'):
                    if t_elem.text:
                        result_text.append(t_elem.text)
        
        field.result = ''.join(result_text) if result_text else None
        
        return field
    
    def _parse_hyperlink(self, elem: ET.Element) -> DOCXRunContent:
        """Parse a hyperlink element."""
        content = DOCXRunContent()
        
        # Get hyperlink target
        rel_id = elem.get(f'{{{NS.get("r", "")}}}id')
        anchor = elem.get(f'{{{NS["w"]}}}anchor')
        
        # Parse runs inside hyperlink
        for child in elem:
            tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
            
            if tag == 'r':
                text_run = self._parse_run(child)
                # Add hyperlink info to run properties
                if rel_id:
                    text_run.properties.additional_properties['hyperlink_rel_id'] = rel_id
                if anchor:
                    text_run.properties.additional_properties['hyperlink_anchor'] = anchor
                content.items.append(text_run)
        
        return content
    
    def _parse_break(self, elem: ET.Element) -> Optional[DOCXBreak]:
        """Parse a break element."""
        break_obj = DOCXBreak(break_type='line')
        
        break_type = elem.get(f'{{{NS["w"]}}}type')
        if break_type == 'page':
            break_obj.break_type = 'page'
        elif break_type == 'column':
            break_obj.break_type = 'column'
        elif break_type == 'textWrapping':
            break_obj.break_type = 'text_wrapping'
        
        clear = elem.get(f'{{{NS["w"]}}}clear')
        if clear:
            break_obj.clear = clear
        
        return break_obj
    
    def _parse_symbol(self, elem: ET.Element) -> Optional[DOCXSymbol]:
        """Parse a symbol element."""
        char = elem.get(f'{{{NS["w"]}}}char')
        if not char:
            return None
        
        symbol = DOCXSymbol(char=char)
        
        font = elem.get(f'{{{NS["w"]}}}font')
        if font:
            symbol.font = font
        
        return symbol
    
    # ============================================================
    # TABLE PARSING
    # ============================================================
    
    def _parse_table(self, elem: ET.Element) -> DOCXTable:
        """Parse a table element."""
        table = DOCXTable()
        
        # Parse table properties
        tbl_pr_elem = safe_find(elem, './/w:tblPr')
        if tbl_pr_elem is not None:
            table.properties = self._parse_table_properties(tbl_pr_elem)
        
        # Parse table grid
        tbl_grid_elem = safe_find(elem, './/w:tblGrid')
        if tbl_grid_elem is not None:
            table.grid = self._parse_table_grid(tbl_grid_elem)
        
        # Parse rows
        row_index = 0
        for tr_elem in safe_findall(elem, './/w:tr'):
            row = self._parse_table_row(tr_elem, row_index)
            table.rows.append(row)
            row_index += 1
        
        return table
    
    def _parse_table_properties(self, elem: ET.Element) -> DOCXTableProperties:
        """Parse table properties."""
        props = DOCXTableProperties()
        
        # Style
        style_elem = safe_find(elem, './/w:tblStyle')
        if style_elem is not None:
            props.style_id = style_elem.get(f'{{{NS["w"]}}}val')
        
        # Alignment
        jc_elem = safe_find(elem, './/w:tblJc')
        if jc_elem is not None:
            val = jc_elem.get(f'{{{NS["w"]}}}val', 'left')
            try:
                props.alignment = ParagraphAlignment(val)
            except ValueError:
                props.alignment = ParagraphAlignment.LEFT
        
        # Indent
        ind_elem = safe_find(elem, './/w:tblInd')
        if ind_elem is not None:
            props.indent_left = parse_dxa_to_points(ind_elem.get(f'{{{NS["w"]}}}val'))
        
        # Borders
        for border_type in ['top', 'bottom', 'left', 'right', 'insideH', 'insideV']:
            border_elem = safe_find(elem, f'.//w:{border_type}')
            if border_elem is not None:
                border_info = parse_border_element(border_elem)
                if border_info:
                    attr_name = f'border_{border_type.lower()}'
                    if border_type == 'insideH':
                        attr_name = 'border_inside_horizontal'
                    elif border_type == 'insideV':
                        attr_name = 'border_inside_vertical'
                    setattr(props, attr_name, border_info)
        
        # Cell margins
        cell_mar_elem = safe_find(elem, './/w:tblCellMar')
        if cell_mar_elem is not None:
            margins: Dict[str, float] = {}
            for margin_type in ['top', 'bottom', 'left', 'right']:
                mar_elem = safe_find(cell_mar_elem, f'.//w:{margin_type}')
                if mar_elem is not None:
                    val1 = parse_dxa_to_points(mar_elem.get(f'{{{NS["w"]}}}val'))
                    if val1 is not None:
                        margins[margin_type] = val1 if val1 is not None else 0.0
            if margins:
                props.cell_margin_default = margins
                
        # Cell spacing
        spacing_elem = safe_find(elem, './/w:tblCellSpacing')
        if spacing_elem is not None:
            props.cell_spacing = parse_dxa_to_points(spacing_elem.get(f'{{{NS["w"]}}}val'))
        
        # Layout
        layout_elem = safe_find(elem, './/w:tblLayout')
        if layout_elem is not None:
            val = layout_elem.get(f'{{{NS["w"]}}}type', 'auto')
            props.layout_type = 'fixed' if val == 'fixed' else 'auto'
        
        # Width
        width_elem = safe_find(elem, './/w:tblW')
        if width_elem is not None:
            props.width = parse_dxa_to_points(width_elem.get(f'{{{NS["w"]}}}w'))
        
        # Header row repeat
        props.header_row_repeat = safe_find(elem, './/w:tblHeader') is not None
        
        return props
    
    def _parse_table_grid(self, elem: ET.Element) -> DOCXTableGrid:
        """Parse table grid columns."""
        grid = DOCXTableGrid()
        
        for col_elem in safe_findall(elem, './/w:gridCol'):
            width = parse_dxa_to_points(col_elem.get(f'{{{NS["w"]}}}w'))
            if width is not None:
                grid.column_widths.append(width)
        
        return grid
    
    def _parse_table_row(self, elem: ET.Element, row_index: int) -> DOCXTableRow:
        """Parse a table row."""
        row = DOCXTableRow(row_index=row_index)
        
        # Row properties
        tr_pr_elem = safe_find(elem, './/w:trPr')
        if tr_pr_elem is not None:
            # Header row
            row.is_header = safe_find(tr_pr_elem, './/w:tblHeader') is not None
            
            # Height
            height_elem = safe_find(tr_pr_elem, './/w:trHeight')
            if height_elem is not None:
                row.height = parse_dxa_to_points(height_elem.get(f'{{{NS["w"]}}}val'))
        
        # Parse cells
        for tc_elem in safe_findall(elem, './/w:tc'):
            cell = self._parse_table_cell(tc_elem)
            row.cells.append(cell)
        
        return row
    
    def _parse_table_cell(self, elem: ET.Element) -> DOCXTableCell:
        """Parse a table cell."""
        cell = DOCXTableCell()
        
        # Cell properties
        tc_pr_elem = safe_find(elem, './/w:tcPr')
        if tc_pr_elem is not None:
            cell.properties = self._parse_table_cell_properties(tc_pr_elem)
        
        # Parse cell content
        for child in elem:
            tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
            
            if tag == 'p':
                para = self._parse_paragraph(child)
                cell.content.append(para)
            elif tag == 'tbl':
                table = self._parse_table(child)
                cell.content.append(table)
        
        return cell
    
    def _parse_table_cell_properties(self, elem: ET.Element) -> DOCXTableCellProperties:
        """Parse table cell properties."""
        props = DOCXTableCellProperties()
        
        # Width
        width_elem = safe_find(elem, './/w:tcW')
        if width_elem is not None:
            props.width = parse_dxa_to_points(width_elem.get(f'{{{NS["w"]}}}w'))
        
        # Vertical alignment
        valign_elem = safe_find(elem, './/w:vAlign')
        if valign_elem is not None:
            val = valign_elem.get(f'{{{NS["w"]}}}val', 'top')
            if val == 'center':
                props.vertical_alignment = VerticalAlignment.CENTER
            elif val == 'bottom':
                props.vertical_alignment = VerticalAlignment.BOTTOM
            else:
                props.vertical_alignment = VerticalAlignment.TOP
        
        # Grid span (column merge)
        grid_span_elem = safe_find(elem, './/w:gridSpan')
        if grid_span_elem is not None:
            props.grid_span = self._parse_int(grid_span_elem.get(f'{{{NS["w"]}}}val')) or 1
        
        # Vertical merge
        vmerge_elem = safe_find(elem, './/w:vMerge')
        if vmerge_elem is not None:
            val = vmerge_elem.get(f'{{{NS["w"]}}}val', 'continue')
            if val == 'restart':
                props.is_vertically_merged_restart = True
                props.vertical_span = 1
            else:
                props.is_vertically_merged = True
        
        # Borders
        for border_type in ['top', 'bottom', 'left', 'right']:
            border_elem = safe_find(elem, f'.//w:{border_type}')
            if border_elem is not None:
                border_info = parse_border_element(border_elem)
                if border_info:
                    setattr(props, f'border_{border_type}', border_info)
        
        # Shading
        shading_elem = safe_find(elem, './/w:shd')
        if shading_elem is not None:
            shading_info = parse_shading_element(shading_elem)
            props.shading_fill = shading_info.get('fill')
        
        # Margins
        for margin_type in ['top', 'bottom', 'left', 'right']:
            mar_elem = safe_find(elem, f'.//w:{margin_type}')
            if mar_elem is not None:
                setattr(props, f'margin_{margin_type}', parse_dxa_to_points(mar_elem.get(f'{{{NS["w"]}}}val')))
        
        # Text direction
        text_dir_elem = safe_find(elem, './/w:textDirection')
        if text_dir_elem is not None:
            val = text_dir_elem.get(f'{{{NS["w"]}}}val', 'lrTb')
            if val == 'rl' or val == 'tbRl':
                props.text_direction = TextDirection.RTL
        
        return props
    
    # ============================================================
    # SECTION PARSING
    # ============================================================
    
    def _extract_sections(self) -> List[DOCXSection]:
        """Extract all sections from the document."""
        sections: List[DOCXSection] = []
        
        doc_xml = self._get_xml_document('word/document.xml')
        if doc_xml is None:
            return sections
        
        body_elem = safe_find(doc_xml, './/w:body')
        if body_elem is None:
            return sections
        
        # Find all section properties
        for sect_pr_elem in safe_findall(body_elem, './/w:sectPr'):
            section = self._parse_section_properties(sect_pr_elem)
            sections.append(section)
        
        return sections
    
    def _parse_section_properties(self, elem: ET.Element) -> DOCXSection:
        """Parse section properties."""
        section = DOCXSection()
        
        # Section type (break type)
        type_elem = safe_find(elem, './/w:type')
        if type_elem is not None:
            val = type_elem.get(f'{{{NS["w"]}}}val', 'nextPage')
            if val == 'continuous':
                section.break_type = SectionType.CONTINUOUS
            elif val == 'nextPage':
                section.break_type = SectionType.NEXT_PAGE
            elif val == 'evenPage':
                section.break_type = SectionType.EVEN_PAGE
            elif val == 'oddPage':
                section.break_type = SectionType.ODD_PAGE
        
        # Page size
        pg_sz_elem = safe_find(elem, './/w:pgSz')
        if pg_sz_elem is not None:
            width = parse_dxa_to_points(pg_sz_elem.get(f'{{{NS["w"]}}}w')) or 12240
            height = parse_dxa_to_points(pg_sz_elem.get(f'{{{NS["w"]}}}h')) or 15840
            orient = cast(Literal['portrait', 'landscape'],pg_sz_elem.get(f'{{{NS["w"]}}}orient', 'portrait'))
            section.page_size = DOCXPageSize(
                width=width,
                height=height,
                orientation=orient
            )
        
        # Page margins
        pg_mar_elem = safe_find(elem, './/w:pgMar')
        if pg_mar_elem is not None:
            section.margins = DOCXPageMargins(
                top=parse_dxa_to_points(pg_mar_elem.get(f'{{{NS["w"]}}}top')) or 1440,
                bottom=parse_dxa_to_points(pg_mar_elem.get(f'{{{NS["w"]}}}bottom')) or 1440,
                left=parse_dxa_to_points(pg_mar_elem.get(f'{{{NS["w"]}}}left')) or 1440,
                right=parse_dxa_to_points(pg_mar_elem.get(f'{{{NS["w"]}}}right')) or 1440,
                header=parse_dxa_to_points(pg_mar_elem.get(f'{{{NS["w"]}}}header')),
                footer=parse_dxa_to_points(pg_mar_elem.get(f'{{{NS["w"]}}}footer')),
                gutter=parse_dxa_to_points(pg_mar_elem.get(f'{{{NS["w"]}}}gutter'))
            )
        
        # Columns
        cols_elem = safe_find(elem, './/w:cols')
        if cols_elem is not None:
            count = self._parse_int(cols_elem.get(f'{{{NS["w"]}}}num')) or 1
            equal_width = cols_elem.get(f'{{{NS["w"]}}}equalWidth', '1') != '0'
            space = parse_dxa_to_points(cols_elem.get(f'{{{NS["w"]}}}space'))
            separator = cols_elem.get(f'{{{NS["w"]}}}sep', '0') == '1'
            
            section.columns = DOCXColumns(
                count=count,
                equal_width=equal_width,
                space_between=space,
                separator=separator
            )
            
            # Individual column widths
            if not equal_width:
                for col_elem in safe_findall(cols_elem, './/w:col'):
                    width1 = parse_dxa_to_points(col_elem.get(f'{{{NS["w"]}}}w'))
                    if width1:
                        section.columns.widths.append(width1)
        
# engines/document/parsers/docx_parser/docx_extractor.py (continued from _parse_section_properties)

        # Header/footer references
        for ref_elem in safe_findall(elem, './/w:headerReference'):
            ref_type = ref_elem.get(f'{{{NS["w"]}}}type', 'default')
            ref_id = ref_elem.get(f'{{{NS["r"]}}}id')
            if ref_id:
                if ref_type == 'first':
                    section.header_first_id = ref_id
                elif ref_type == 'even':
                    section.header_even_id = ref_id
                else:
                    section.header_default_id = ref_id
        
        for ref_elem in safe_findall(elem, './/w:footerReference'):
            ref_type = ref_elem.get(f'{{{NS["w"]}}}type', 'default')
            ref_id = ref_elem.get(f'{{{NS["r"]}}}id')
            if ref_id:
                if ref_type == 'first':
                    section.footer_first_id = ref_id
                elif ref_type == 'even':
                    section.footer_even_id = ref_id
                else:
                    section.footer_default_id = ref_id
        
        # Page numbering
        pg_num_elem = safe_find(elem, './/w:pgNumType')
        if pg_num_elem is not None:
            section.page_number_start = self._parse_int(pg_num_elem.get(f'{{{NS["w"]}}}start'))
            section.page_number_format = pg_num_elem.get(f'{{{NS["w"]}}}fmt')
        
        # Line numbering
        ln_num_elem = safe_find(elem, './/w:lnNumType')
        if ln_num_elem is not None:
            section.line_numbering = {
                'count_by': self._parse_int(ln_num_elem.get(f'{{{NS["w"]}}}countBy')),
                'start': self._parse_int(ln_num_elem.get(f'{{{NS["w"]}}}start')),
                'distance': parse_dxa_to_points(ln_num_elem.get(f'{{{NS["w"]}}}distance')),
                'restart': ln_num_elem.get(f'{{{NS["w"]}}}restart', 'newPage')
            }
        
        return section
    
    # ============================================================
    # BINARY PARTS EXTRACTION
    # ============================================================
    
    def _extract_binary_parts(self) -> Dict[str, bytes]:
        """Extract all binary parts (images, embedded objects)."""
        binary_parts: Dict[str, bytes] = {}
        
        if self.image_extractor is None:
            return binary_parts
        
        # Extract all images
        image_payloads = self.image_extractor.extract_all_images()
        
        # Convert payloads to bytes and store by relationship ID
        for rel_id, payload in image_payloads.items():
            if payload.bytes_content:
                binary_parts[rel_id] = payload.bytes_content
            elif payload.data:
                import base64
                binary_parts[rel_id] = base64.b64decode(payload.data)
        
        # Extract embedded objects (OLE objects, etc.)
        doc_rels = self._relationships.get('document', {})
        for rel_id, target in doc_rels.items():
            if target.startswith('embeddings/') or target.endswith('.bin') or target.endswith('.ole'):
                try:
                    obj_path = f'word/{target}'
                    assert self.zip_file is not None, "ZIP file not opened"
                    obj_data = self.zip_file.read(obj_path)
                    binary_parts[rel_id] = obj_data
                except (KeyError, zipfile.BadZipFile):
                    pass
        
        return binary_parts
    
    # ============================================================
    # SETTINGS, THEME, AND FONTS EXTRACTION
    # ============================================================
    
    def _extract_settings(self) -> Dict[str, Any]:
        """Extract document settings from settings.xml."""
        settings: Dict[str, Any] = {}
        
        settings_xml = self._get_xml_document('word/settings.xml')
        if settings_xml is None:
            return settings
        
        # Zoom
        zoom_elem = safe_find(settings_xml, './/w:zoom')
        if zoom_elem is not None:
            settings['zoom'] = {
                'percent': self._parse_int(zoom_elem.get(f'{{{NS["w"]}}}percent')),
                'type': zoom_elem.get(f'{{{NS["w"]}}}val')
            }
        
        # Default tab stop
        tab_elem = safe_find(settings_xml, './/w:defaultTabStop')
        if tab_elem is not None:
            settings['default_tab_stop'] = parse_dxa_to_points(tab_elem.get(f'{{{NS["w"]}}}val'))
        
        # Display background shape
        bg_shape_elem = safe_find(settings_xml, './/w:displayBackgroundShape')
        if bg_shape_elem is not None:
            settings['display_background_shape'] = True
        
        # Even and odd headers/footers
        even_odd_elem = safe_find(settings_xml, './/w:evenAndOddHeaders')
        if even_odd_elem is not None:
            settings['even_and_odd_headers'] = True
        
        # Track revisions
        track_rev_elem = safe_find(settings_xml, './/w:trackRevisions')
        if track_rev_elem is not None:
            settings['track_revisions'] = True
        
        # Proofing state
        proof_elem = safe_find(settings_xml, './/w:proofState')
        if proof_elem is not None:
            settings['proof_state'] = proof_elem.get(f'{{{NS["w"]}}}val')
        
        # Document protection
        protect_elem = safe_find(settings_xml, './/w:documentProtection')
        if protect_elem is not None:
            settings['document_protection'] = {
                'edit': protect_elem.get(f'{{{NS["w"]}}}edit'),
                'enforcement': protect_elem.get(f'{{{NS["w"]}}}enforcement') == '1'
            }
        
        # Compatibility settings
        compat_elem = safe_find(settings_xml, './/w:compat')
        if compat_elem is not None:
            compat_settings = {}
            for setting in compat_elem:
                tag = setting.tag.split('}')[-1] if '}' in setting.tag else setting.tag
                compat_settings[tag] = True
            settings['compatibility'] = compat_settings
        
        return settings
    
    def _extract_theme(self) -> Optional[Dict[str, Any]]:
        """Extract theme from theme1.xml."""
        theme: Dict[str, Any] = {}
        
        theme_xml = self._get_xml_document('word/theme/theme1.xml')
        if theme_xml is None:
            return None
        
        # Theme name
        name_elem = safe_find(theme_xml, './/a:themeName', {'a': NS.get('a', '')})
        if name_elem is not None:
            theme['name'] = name_elem.get('name')
        
        # Theme colors
        theme_colors_elem = safe_find(theme_xml, './/a:themeElements/a:clrScheme', {'a': NS.get('a', '')})
        if theme_colors_elem is not None:
            colors = {}
            color_mappings = {
                'dk1': 'dark1',
                'lt1': 'light1',
                'dk2': 'dark2',
                'lt2': 'light2',
                'accent1': 'accent1',
                'accent2': 'accent2',
                'accent3': 'accent3',
                'accent4': 'accent4',
                'accent5': 'accent5',
                'accent6': 'accent6',
                'hlink': 'hyperlink',
                'folHlink': 'followed_hyperlink'
            }
            
            for elem_name, key_name in color_mappings.items():
                color_elem = safe_find(theme_colors_elem, f'.//a:{elem_name}', {'a': NS.get('a', '')})
                if color_elem is not None:
                    sys_clr = safe_find(color_elem, './/a:sysClr', {'a': NS.get('a', '')})
                    srgb_clr = safe_find(color_elem, './/a:srgbClr', {'a': NS.get('a', '')})
                    
                    if sys_clr is not None:
                        colors[key_name] = {
                            'type': 'system',
                            'value': sys_clr.get('val')
                        }
                    elif srgb_clr is not None:
                        colors[key_name] = {
                            'type': 'srgb',
                            'value': srgb_clr.get('val')
                        }
            
            theme['colors'] = colors
        
        # Theme fonts
        font_scheme_elem = safe_find(theme_xml, './/a:themeElements/a:fontScheme', {'a': NS.get('a', '')})
        if font_scheme_elem is not None:
            fonts = {}
            
            major_font_elem = safe_find(font_scheme_elem, './/a:majorFont', {'a': NS.get('a', '')})
            if major_font_elem is not None:
                fonts['major'] = self._parse_theme_fonts(major_font_elem)
            
            minor_font_elem = safe_find(font_scheme_elem, './/a:minorFont', {'a': NS.get('a', '')})
            if minor_font_elem is not None:
                fonts['minor'] = self._parse_theme_fonts(minor_font_elem)
            
            theme['fonts'] = fonts
        
        # Theme format scheme
        fmt_scheme_elem = safe_find(theme_xml, './/a:themeElements/a:fmtScheme', {'a': NS.get('a', '')})
        if fmt_scheme_elem is not None:
            fmt_scheme = {}
            
            # Fill style list
            fill_list_elem = safe_find(fmt_scheme_elem, './/a:fillStyleLst', {'a': NS.get('a', '')})
            if fill_list_elem is not None:
                fmt_scheme['fill_styles'] = self._parse_theme_fill_styles(fill_list_elem)
            
            # Line style list
            ln_list_elem = safe_find(fmt_scheme_elem, './/a:lnStyleLst', {'a': NS.get('a', '')})
            if ln_list_elem is not None:
                fmt_scheme['line_styles'] = self._parse_theme_line_styles(ln_list_elem)
            
            # Effect style list
            effect_list_elem = safe_find(fmt_scheme_elem, './/a:effectStyleLst', {'a': NS.get('a', '')})
            if effect_list_elem is not None:
                fmt_scheme['effect_styles'] = self._parse_theme_effect_styles(effect_list_elem)
            
            # Background fill style list
            bg_fill_list_elem = safe_find(fmt_scheme_elem, './/a:bgFillStyleLst', {'a': NS.get('a', '')})
            if bg_fill_list_elem is not None:
                fmt_scheme['background_fill_styles'] = self._parse_theme_fill_styles(bg_fill_list_elem)
            
            theme['format_scheme'] = fmt_scheme
        
        return theme
    
    def _parse_theme_fonts(self, elem: ET.Element) -> Dict[str, str]:
        """Parse theme font definitions."""
        fonts: Dict[str, str] = {}
        ns_map = {'a': NS.get('a', '')}
        
        for script in ['latin', 'ea', 'cs']:
            font_elem = safe_find(elem, f'.//a:{script}', ns_map)
            if font_elem is not None:
                fonts[script] = font_elem.get('typeface', '')
        
        return fonts
    
    def _parse_theme_fill_styles(self, elem: ET.Element) -> List[Dict[str, Any]]:
        """Parse theme fill styles."""
        styles: List[Dict[str, Any]] = []
        ns_map = {'a': NS.get('a', '')}
        
        for fill_elem in elem:
            style: Dict[str, Any] = {}
            tag = fill_elem.tag.split('}')[-1] if '}' in fill_elem.tag else fill_elem.tag
            
            if tag == 'solidFill':
                style['type'] = 'solid'
                srgb_clr = safe_find(fill_elem, './/a:srgbClr', ns_map)
                if srgb_clr is not None:
                    style['color'] = srgb_clr.get('val')
                scheme_clr = safe_find(fill_elem, './/a:schemeClr', ns_map)
                if scheme_clr is not None:
                    style['scheme_color'] = scheme_clr.get('val')
            elif tag == 'gradFill':
                style['type'] = 'gradient'
            elif tag == 'pattFill':
                style['type'] = 'pattern'
            elif tag == 'noFill':
                style['type'] = 'none'
            
            styles.append(style)
        
        return styles
    
    def _parse_theme_line_styles(self, elem: ET.Element) -> List[Dict[str, Any]]:
        """Parse theme line styles."""
        styles: List[Dict[str, Any]] = []
        ns_map = {'a': NS.get('a', '')}
        
        for ln_elem in elem:
            style: Dict[str, Any] = {}
            tag = ln_elem.tag.split('}')[-1] if '}' in ln_elem.tag else ln_elem.tag
            
            if tag == 'ln':
                width = self._parse_int(ln_elem.get('w'))
                if width:
                    style['width'] = width / 12700  # EMU to points
                
                cap = ln_elem.get('cap')
                if cap:
                    style['cap'] = cap
                
                cmpd = ln_elem.get('cmpd')
                if cmpd:
                    style['compound'] = cmpd
                
                algn = ln_elem.get('algn')
                if algn:
                    style['alignment'] = algn
                
                # Fill
                solid_fill = safe_find(ln_elem, './/a:solidFill', ns_map)
                if solid_fill is not None:
                    style['fill_type'] = 'solid'
                    srgb_clr = safe_find(solid_fill, './/a:srgbClr', ns_map)
                    if srgb_clr is not None:
                        style['color'] = srgb_clr.get('val')
                
                # Dash
                prst_dash = safe_find(ln_elem, './/a:prstDash', ns_map)
                if prst_dash is not None:
                    style['dash'] = prst_dash.get('val')
            
            styles.append(style)
        
        return styles
    
    def _parse_theme_effect_styles(self, elem: ET.Element) -> List[Dict[str, Any]]:
        """Parse theme effect styles."""
        styles: List[Dict[str, Any]] = []
        ns_map = {'a': NS.get('a', '')}
        
        for effect_elem in elem:
            style: Dict[str, Any] = {}
            tag = effect_elem.tag.split('}')[-1] if '}' in effect_elem.tag else effect_elem.tag
            
            if tag == 'effectStyle':
                effect_list = safe_find(effect_elem, './/a:effectLst', ns_map)
                if effect_list is not None:
                    # Shadow
                    shadow = safe_find(effect_list, './/a:outerShdw', ns_map)
                    if shadow is not None:
                        style['shadow'] = {
                            'blur_rad': self._parse_int(shadow.get('blurRad')),
                            'dist': self._parse_int(shadow.get('dist')),
                            'dir': self._parse_int(shadow.get('dir')),
                            'algn': shadow.get('algn')
                        }
                    
                    # Reflection
                    reflection = safe_find(effect_list, './/a:reflection', ns_map)
                    if reflection is not None:
                        style['reflection'] = {
                            'blur_rad': self._parse_int(reflection.get('blurRad')),
                            'st_a': self._parse_int(reflection.get('stA')),
                            'st_pos': self._parse_int(reflection.get('stPos')),
                            'end_a': self._parse_int(reflection.get('endA')),
                            'end_pos': self._parse_int(reflection.get('endPos')),
                            'dist': self._parse_int(reflection.get('dist')),
                            'dir': self._parse_int(reflection.get('dir'))
                        }
                    
                    # Glow
                    glow = safe_find(effect_list, './/a:glow', ns_map)
                    if glow is not None:
                        style['glow'] = {
                            'rad': self._parse_int(glow.get('rad'))
                        }
            
            styles.append(style)
        
        return styles
    
    def _extract_font_table(self) -> Dict[str, Dict[str, Any]]:
        """Extract font table from fontTable.xml."""
        font_table: Dict[str, Dict[str, Any]] = {}
        
        fonts_xml = self._get_xml_document('word/fontTable.xml')
        if fonts_xml is None:
            return font_table
        
        for font_elem in safe_findall(fonts_xml, './/w:font'):
            font_name = font_elem.get(f'{{{NS["w"]}}}name', '')
            if font_name:
                # Get alternative names
                alt_name_elem = safe_find(font_elem, './/w:altName')
                alt_name = alt_name_elem.get(f'{{{NS["w"]}}}val') if alt_name_elem is not None else None
                
                # Get font family
                family_elem = safe_find(font_elem, './/w:family')
                family = family_elem.get(f'{{{NS["w"]}}}val') if family_elem is not None else None
                
                # Get pitch
                pitch_elem = safe_find(font_elem, './/w:pitch')
                pitch = pitch_elem.get(f'{{{NS["w"]}}}val') if pitch_elem is not None else None
                
                # Get charset
                charset_elem = safe_find(font_elem, './/w:charset')
                charset = charset_elem.get(f'{{{NS["w"]}}}val') if charset_elem is not None else None
                
                # Store font info
                font_info = {
                    'name': font_name,
                    'alt_name': alt_name,
                    'family': family,
                    'pitch': pitch,
                    'charset': charset
                }
                
                # Remove None values
                font_info = {k: v for k, v in font_info.items() if v is not None}
                
                if font_info:
                    font_table[font_name] = font_info
        
        return font_table
    
    def _extract_web_settings(self) -> Dict[str, Any]:
        """Extract web settings from webSettings.xml."""
        web_settings: Dict[str, Any] = {}
        
        web_xml = self._get_xml_document('word/webSettings.xml')
        if web_xml is None:
            return web_settings
        
        # Browser optimization
        optimize_elem = safe_find(web_xml, './/w:optimizeForBrowser')
        if optimize_elem is not None:
            web_settings['optimize_for_browser'] = optimize_elem.get(f'{{{NS["w"]}}}val') == 'true'
        
        # Target browser
        target_elem = safe_find(web_xml, './/w:targetScreenSz')
        if target_elem is not None:
            web_settings['target_screen_size'] = target_elem.get(f'{{{NS["w"]}}}val')
        
        # Save smart tags as XML
        smart_tags_elem = safe_find(web_xml, './/w:saveSmartTagsAsXml')
        if smart_tags_elem is not None:
            web_settings['save_smart_tags_as_xml'] = smart_tags_elem.get(f'{{{NS["w"]}}}val') == 'true'
        
        # PNG or JPEG for images
        png_elem = safe_find(web_xml, './/w:allowPNG')
        if png_elem is not None:
            web_settings['allow_png'] = png_elem.get(f'{{{NS["w"]}}}val') == 'true'
        
        # Rely on CSS for font formatting
        css_elem = safe_find(web_xml, './/w:relyOnCSS')
        if css_elem is not None:
            web_settings['rely_on_css'] = css_elem.get(f'{{{NS["w"]}}}val') == 'true'
        
        # Encoding
        encoding_elem = safe_find(web_xml, './/w:encoding')
        if encoding_elem is not None:
            web_settings['encoding'] = encoding_elem.get(f'{{{NS["w"]}}}val')
        
        return web_settings
    
    # ============================================================
    # UTILITY METHODS
    # ============================================================
    
    def _parse_int(self, value: Optional[str]) -> Optional[int]:
        """Parse string to integer."""
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
    
    def _parse_float(self, value: Optional[str]) -> Optional[float]:
        """Parse string to float."""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _parse_bool(self, value: Optional[str]) -> bool:
        """Parse string to boolean."""
        if value is None:
            return False
        return value.lower() in ('true', '1', 'yes', 'on')
    
    def _parse_w3c_datetime(self, datetime_str: str) -> Optional[str]:
        """Parse W3C datetime format to ISO 8601 string."""
        if not datetime_str:
            return None
        
        # Already in ISO format
        if 'T' in datetime_str:
            return datetime_str.replace('Z', '+00:00')
        
        # Try to parse and reformat
        try:
            dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            return dt.isoformat()
        except (ValueError, TypeError):
            return datetime_str
    
    def clear_cache(self):
        """Clear all internal caches."""
        self._xml_cache.clear()
        self._relationships.clear()
        self._num_instances.clear()
        self._num_definitions.clear()
        self._comments.clear()
        
        if self.image_extractor:
            self.image_extractor.clear_cache()