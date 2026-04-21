# engines/document/ingestion/ingestion_service.py

from __future__ import annotations

from typing import Optional, Dict, Any

from engines.document.models.media_types import MediaType, DocumentFormat

from engines.document.ingestion.ingestion_context import IngestionContext
from engines.document.ingestion.ingestion_pipeline import IngestionPipeline
from engines.document.ingestion.ingestion_runner import IngestionRunner

from engines.document.ingestion.ingestion_models import DocumentIngestionResult
from engines.document.ingestion.ingestion_validator import IngestionValidator
from engines.document.ingestion.ingestion_errors import IngestionError

# from engines.document.parsers.pdf_parser import PdfParser
# from engines.document.parsers.docx_parser import DocxParser
# from engines.document.parsers.html_parser import HTMLParser
# from engines.document.parsers.markdown_parser import MarkdownParser
# from engines.document.parsers.latex_parser import LaTeXParser
# from engines.document.parsers.excel_parser import ExcelParser
# from engines.document.parsers.csv_parser import USDMCSVParser
# from engines.document.parsers.json_parser import JSONParser
# from engines.document.parsers.xml_parser import XMLParser
# from engines.document.parsers.yaml_parser import YAMLParser
# from engines.document.parsers.binary_parser import BinaryParser
# from engines.document.parsers.cad_parser.csdm_parser import CSDMDocumentParser

# from engines.document.writers.pdf_writer import PDFWriter
# from engines.document.writers.docx_writer import DocxWriter
# from engines.document.writers.html_writer import HTMLWriter
# from engines.document.writers.markdown_writer import MarkdownWriter
# from engines.document.writers.latex_writer import LaTeXWriter
# from engines.document.writers.excel_writer import ExcelWriter
# from engines.document.writers.csv_writer import USDMCSVWriter
# from engines.document.writers.json_writer import JSONWriter
# from engines.document.writers.xml_writer import XMLWriter
# from engines.document.writers.yaml_writer import YAMLWriter
# from engines.document.writers.binary_writer import BinaryWriter
# from engines.document.writers.cad_writer import CADWriter

from engines.document.ingestion.workflow_registry import WorkflowRegistry
from engines.document.models.document_registry import DocumentRegistry

class IngestionService:
    """
    Main public ingestion orchestrator.
    UploadService, Scheduler and Async Workers call this service.
    """

    def __init__(self):
        self.workflow_registry = self.initialize_workflow_registry()
        self.document_registry = self.initialize_document_registry()


    def initialize_workflow_registry(self) -> WorkflowRegistry:
        registry = WorkflowRegistry()

        # Example custom workflow registrations (extendable)
        registry.register(".txt", ["extract", "parse", "chunk", "embed", "store"])
        registry.register(".md",  ["extract", "parse", "chunk", "embed", "store"])
        registry.register("text/plain", ["extract", "parse", "chunk", "embed", "store"])
        registry.register("pdf_workflow", ["extract", "parse", "chunk", "embed", "store"])
        registry.register("cad_workflow", ["extract", "parse", "chunk", "embed", "store"])
        registry.register("xlsx_workflow", ["extract", "parse", "chunk", "embed", "store"])
        registry.register("ppt_workflow", ["extract", "parse", "chunk", "embed", "store"])
        registry.register("markdown_workflow", ["extract", "parse", "chunk", "embed", "store"])
        registry.register("data_workflow", ["extract", "parse", "chunk", "embed", "store"])

        return registry

    def initialize_document_registry(self) -> DocumentRegistry:
        registry = DocumentRegistry()
        # # USDM
        # registry.register_parser_plugin(DocumentFormat.PDF, PdfParser)
        # registry.register_parser_plugin(DocumentFormat.DOCX, DocxParser)
        # registry.register_parser_plugin(DocumentFormat.HTML, HTMLParser)
        # registry.register_parser_plugin(DocumentFormat.MARKDOWN, MarkdownParser)
        # registry.register_parser_plugin(DocumentFormat.LATEX, LaTeXParser)
        # # registry.register_parser_plugin(DocumentFormat.PPT, PptParser)

        # # ESDM
        # registry.register_parser_plugin(DocumentFormat.XLSX, ExcelParser)
        # # registry.register_parser_plugin(DocumentFormat.CSV, USDMCSVParser)
        # # registry.register_parser_plugin(DocumentFormat.TSV, USDMCSVParser)
        # # registry.register_parser_plugin(DocumentFormat.PARQUET, USDMCSVParser)
        # # registry.register_parser_plugin(DocumentFormat.ARROW, USDMCSVParser)
        # # registry.register_parser_plugin(DocumentFormat.FEATHER, USDMCSVParser)

        # # DSDM
        # registry.register_parser_plugin(DocumentFormat.JSON, JSONParser)
        # registry.register_parser_plugin(DocumentFormat.XML, XMLParser)
        # registry.register_parser_plugin(DocumentFormat.YAML, YAMLParser)
        # registry.register_parser_plugin(DocumentFormat.BSON, BinaryParser)
        # registry.register_parser_plugin(DocumentFormat.CBOR, BinaryParser)
        # registry.register_parser_plugin(DocumentFormat.MESSAGEPACK, BinaryParser)

        # # CSDM
        # registry.register_parser_plugin(DocumentFormat.DXF, CSDMDocumentParser)
        # registry.register_parser_plugin(DocumentFormat.DWG, CSDMDocumentParser)
        # registry.register_parser_plugin(DocumentFormat.IFC, CSDMDocumentParser)





        # # USDM
        # registry.register_writer_plugin(DocumentFormat.PDF, PDFWriter)
        # registry.register_writer_plugin(DocumentFormat.DOCX, DocxWriter)
        # registry.register_writer_plugin(DocumentFormat.HTML, HTMLWriter)
        # registry.register_writer_plugin(DocumentFormat.MARKDOWN, MarkdownWriter)
        # registry.register_writer_plugin(DocumentFormat.LATEX, LaTeXWriter)
        # # registry.register_writer_plugin(DocumentFormat.PPT, PptWriter)

        # # ESDM
        # registry.register_writer_plugin(DocumentFormat.XLSX, ExcelWriter)
        # registry.register_writer_plugin(DocumentFormat.CSV, USDMCSVWriter)
        # # registry.register_writer_plugin(DocumentFormat.TSV, USDMCSVWriter)
        # # registry.register_writer_plugin(DocumentFormat.PARQUET, USDMCSVWriter)
        # # registry.register_writer_plugin(DocumentFormat.ARROW, USDMCSVWriter)
        # # registry.register_writer_plugin(DocumentFormat.FEATHER, USDMCSVWriter)

        # # DSDM
        # registry.register_writer_plugin(DocumentFormat.JSON, JSONWriter)
        # registry.register_writer_plugin(DocumentFormat.XML, XMLWriter)
        # registry.register_writer_plugin(DocumentFormat.YAML, YAMLWriter)
        # registry.register_writer_plugin(DocumentFormat.BSON, BinaryWriter)
        # registry.register_writer_plugin(DocumentFormat.CBOR, BinaryWriter)
        # registry.register_parser_plugin(DocumentFormat.MESSAGEPACK, BinaryParser)

        # # CSDM
        # registry.register_writer_plugin(DocumentFormat.DXF, CADWriter)
        # registry.register_writer_plugin(DocumentFormat.DWG, CADWriter)
        # registry.register_writer_plugin(DocumentFormat.IFC, CADWriter)

        return registry


    # ---------------------------------------------------------------------
    async def ingest(
        self,
        *,
        filename: str,
        media_type,
        data: bytes,
        metadata: Optional[Dict[str, Any]] = None,
        context: Optional[IngestionContext] = None,
    ) -> DocumentIngestionResult:
        """
        Runs full ingestion pipeline.
        Context may be None → runner will construct the IngestionContext.
        """

        runner = IngestionRunner(workflow_registry=self.workflow_registry)

        try:
            # Runner is responsible for context creation if context=None
            return await runner.execute(
                filename=filename,
                media_type=media_type,
                data=data,
                metadata=metadata,
                context=context,
            )

        except IngestionError:
            # bubble ingestion errors as-is
            raise

        except Exception as exc:
            raise IngestionError(f"Ingestion failed: {exc}") from exc
