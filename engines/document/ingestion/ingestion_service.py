# engines/document/ingestion/ingestion_service.py
from __future__ import annotations

from typing import Any

from ..models.document_registry import DocumentRegistry
from .ingestion_context import IngestionContext
from .ingestion_errors import IngestionError
from .ingestion_models import DocumentIngestionResult
from .ingestion_runner import IngestionRunner
from .workflow_registry import WorkflowRegistry
# from ..parsers.pdf_parser import PdfParser
# from ..parsers.docx_parser import DocxParser
# from ..parsers.html_parser import HTMLParser
# from ..parsers.markdown_parser import MarkdownParser
# from ..parsers.latex_parser import LaTeXParser
# from ..parsers.excel_parser import ExcelParser
# from ..parsers.csv_parser import USDMCSVParser
# from ..parsers.json_parser import JSONParser
# from ..parsers.xml_parser import XMLParser
# from ..parsers.yaml_parser import YAMLParser
# from ..parsers.binary_parser import BinaryParser
# from ..parsers.cad_parser.csdm_parser import CSDMDocumentParser
# from ..writers.pdf_writer import PDFWriter
# from ..writers.docx_writer import DocxWriter
# from ..writers.html_writer import HTMLWriter
# from ..writers.markdown_writer import MarkdownWriter
# from ..writers.latex_writer import LaTeXWriter
# from ..writers.excel_writer import ExcelWriter
# from ..writers.csv_writer import USDMCSVWriter
# from ..writers.json_writer import JSONWriter
# from ..writers.xml_writer import XMLWriter
# from ..writers.yaml_writer import YAMLWriter
# from ..writers.binary_writer import BinaryWriter
# from ..writers.cad_writer import CADWriter

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
        metadata: dict[str, Any] | None = None,
        context: IngestionContext | None = None,
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
