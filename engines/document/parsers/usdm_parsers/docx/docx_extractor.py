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
import os  # noqa: E402
import re  # noqa: E402
from datetime import datetime  # noqa: E402
from io import BytesIO  # noqa: E402
from typing import Any  # noqa: E402
from typing import BinaryIO  # noqa: E402
from typing import cast  # noqa: E402
from typing import Literal  # noqa: E402
from xml.etree import ElementTree as ET  # noqa: E402
from zipfile import ZipFile, BadZipFile  # noqa: E402

from ....models.base import BinaryEncoding  # noqa: E402
from .docx_chart_extractor import parse_docx_chart  # noqa: E402
from .docx_diagram_extractor import parse_diagram  # noqa: E402
from .docx_image_extractor import DOCXImageExtractor  # noqa: E402
from .docx_math_parser import OMMLParser  # noqa: E402
from .docx_models import DOCXBreak  # noqa: E402
from .docx_models import DOCXChartData  # noqa: E402
from .docx_models import DOCXColumns  # noqa: E402
from .docx_models import DOCXComment  # noqa: E402
from .docx_models import DOCXComplexField  # noqa: E402
from .docx_models import DOCXCoreProperties  # noqa: E402
from .docx_models import DOCXCustomProperties  # noqa: E402
from .docx_models import DOCXDocument  # noqa: E402
from .docx_models import DOCXDrawing  # noqa: E402
from .docx_models import DOCXExtendedProperties  # noqa: E402
from .docx_models import DOCXField  # noqa: E402
from .docx_models import DOCXFootnoteEndnote  # noqa: E402
from .docx_models import DOCXHeaderFooter  # noqa: E402
from .docx_models import DOCXNumberingDefinition  # noqa: E402
from .docx_models import DOCXNumberingInstance  # noqa: E402
from .docx_models import DOCXNumberingLevel  # noqa: E402
from .docx_models import DOCXPageMargins  # noqa: E402
from .docx_models import DOCXPageSize  # noqa: E402
from .docx_models import DOCXParagraph  # noqa: E402
from .docx_models import DOCXParagraphProperties  # noqa: E402
from .docx_models import DOCXRTLProperties  # noqa: E402
from .docx_models import DOCXRunContent  # noqa: E402
from .docx_models import DOCXRunProperties  # noqa: E402
from .docx_models import DOCXSection  # noqa: E402
from .docx_models import DOCXStyle  # noqa: E402
from .docx_models import DOCXSymbol  # noqa: E402
from .docx_models import DOCXTab  # noqa: E402
from .docx_models import DOCXTable  # noqa: E402
from .docx_models import DOCXTableCell  # noqa: E402
from .docx_models import DOCXTableCellProperties  # noqa: E402
from .docx_models import DOCXTableGrid  # noqa: E402
from .docx_models import DOCXTableProperties  # noqa: E402
from .docx_models import DOCXTableRow  # noqa: E402
from .docx_models import DOCXTextRun  # noqa: E402
from .docx_models import DOCXTOCField  # noqa: E402
from .docx_models import DOCXWatermark  # noqa: E402
from .docx_models import NumberingLevelSuffix  # noqa: E402
from .docx_models import ParagraphAlignment  # noqa: E402
from .docx_models import SectionType  # noqa: E402
from .docx_models import TextDirection  # noqa: E402
from .docx_models import VerticalAlignment  # noqa: E402
from .docx_style_parser import DocxStyleParser  # noqa: E402
from .docx_table_parser import DocxTableParser  # noqa: E402
from .docx_utils import get_element_text  # noqa: E402
from .docx_utils import NS  # noqa: E402
from .docx_utils import parse_border_element  # noqa: E402
from .docx_utils import parse_dxa_to_points  # noqa: E402
from .docx_utils import parse_shading_element  # noqa: E402
from .docx_utils import safe_find  # noqa: E402
from .docx_utils import safe_findall  # noqa: E402


from .docx_extractor_xml import DOCXExtractorXML
from .docx_extractor_properties import DOCXExtractorProperties
from .docx_extractor_styles import DOCXExtractorStyles
from .docx_extractor_structural import DOCXExtractorStructural
from .docx_extractor_content import DOCXExtractorContent
from .docx_extractor_annotations import DOCXExtractorAnnotations
class DOCXExtractor(DOCXExtractorXML, DOCXExtractorProperties, DOCXExtractorStyles, DOCXExtractorStructural, DOCXExtractorContent, DOCXExtractorAnnotations):
    """
    Main extractor for DOCX documents.
    
    Extracts all content from a DOCX file and builds a DOCXDocument
    intermediate representation.
    """

    def __init__(
        self,
        file_path: str | None = None,
        file_bytes: bytes | None = None,
        file_obj: BinaryIO | None = None,
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

        self.zip_file: ZipFile | None = None

        # Sub-extractors
        self.image_extractor: DOCXImageExtractor | None = None
        self.style_parser: DocxStyleParser | None = None
        self.table_parser: DocxTableParser | None = None
        self.math_parser: OMMLParser | None = None

        # Cache for XML documents
        self._xml_cache: dict[str, ET.Element] = {}

        # Relationships
        self._relationships: dict[str, dict[str, str]] = {}

        # Numbering instances cache
        self._num_instances: dict[str, DOCXNumberingInstance] = {}
        self._num_definitions: dict[str, DOCXNumberingDefinition] = {}

        # Comments cache
        self._comments: dict[str, DOCXComment] = {}

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

            self._resolve_charts(doc)

            self._resolve_diagrams(doc)

            self._collect_watermarks(doc)

            self._collect_complex_fields(doc)

            self._collect_toc_fields(doc)

            self._extract_rtl_properties(doc)

            return doc

        finally:
            self._close_zip()

    def _open_zip(self):
        """Open the DOCX file as a ZIP archive."""
        if self.file_path:
            self.zip_file = ZipFile(self.file_path, 'r')
        elif self.file_bytes:
            self.zip_file = ZipFile(BytesIO(self.file_bytes), 'r')
        elif self.file_obj:
            self.zip_file = ZipFile(self.file_obj, 'r')
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

    def clear_cache(self):
        """Clear all internal caches."""
        self._xml_cache.clear()
        self._relationships.clear()
        self._num_instances.clear()
        self._num_definitions.clear()
        self._comments.clear()

        if self.image_extractor:
            self.image_extractor.clear_cache()
