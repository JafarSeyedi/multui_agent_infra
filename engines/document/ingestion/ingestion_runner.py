# engines/document/ingestion/ingestion_runner.py

from __future__ import annotations
from typing import Optional, List, Dict, Any
from engines.document.ingestion.ingestion_context import IngestionContext
from engines.document.ingestion.ingestion_pipeline import IngestionPipeline
from engines.document.ingestion.workflow_registry import WorkflowRegistry
from engines.document.models.media_types import MediaType, DocumentFormat
from engines.document.ingestion.steps.step_extract import step_extract
from engines.document.ingestion.steps.step_parse import step_parse
from engines.document.ingestion.steps.step_chunk import step_chunk
from engines.document.ingestion.steps.step_embed import step_embed
from engines.document.ingestion.steps.step_store import step_store

from engines.document.ingestion.ingestion_models import (
    DocumentIngestionResult,
    DocumentRecord,
    ParsedDocument,
    ChunkRecord,
    EmbeddingRecord,
    IngestionStatus,
    IngestionEvent,
)


class IngestionRunner:

    def __init__(self, workflow_registry: WorkflowRegistry):
        self.workflow_registry = workflow_registry
        self.pipeline = IngestionPipeline()

    def route(self, media_type: MediaType, filename: Optional[str]=None) -> list[str]:
        """
        Returns step-list of selected workflow.
        """
        # 1) Direct PDF
        if media_type.format == DocumentFormat.PDF:
            wf = self.workflow_registry.get("pdf_workflow")
            if wf:
                return wf

        # 2) CAD / CSDM structured types
        if media_type.standard == "csdm":
            wf = self.workflow_registry.get("cad_workflow")
            if wf:
                return wf

        # 3) Word, Excel, PPT
        if media_type.format == DocumentFormat.DOCX:
            wf = self.workflow_registry.get("docx_workflow")
            if wf:
                return wf

        if media_type.format in [DocumentFormat.XLSX, DocumentFormat.CSV, DocumentFormat.TSV, DocumentFormat.PARQUET, DocumentFormat.ARROW, DocumentFormat.FEATHER]:
            wf = self.workflow_registry.get("xlsx_workflow")
            if wf:
                return wf

        if media_type.format == DocumentFormat.PPT:
            wf = self.workflow_registry.get("ppt_workflow")
            if wf:
                return wf

        # 4) Markdown, Latex
        if media_type.format in [DocumentFormat.MARKDOWN, DocumentFormat.LATEX]:
            wf = self.workflow_registry.get("markdown_workflow")
            if wf:
                return wf

        # 5) Plain text
        if media_type.format == DocumentFormat.TEXT:
            wf = self.workflow_registry.get("text/plain")
            if wf:
                return wf

        # 2) data / DSDM structured types
        if media_type.standard == "dsdm":
            wf = self.workflow_registry.get("data_workflow")
            if wf:
                return wf

        # 6) Fallback: try extension
        if filename:
            ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else None
            if ext:
                wf = self.workflow_registry.get(f"{ext}")
                if wf:
                    return wf

        return self.workflow_registry.default_workflow

    async def execute(
        self,
        *,
        filename: str,
        data: bytes,
        media_type: MediaType,
        metadata: Optional[Dict[str, Any]] = None,
        context: Optional[IngestionContext] = None,
    ) -> DocumentIngestionResult:
        """
        Main ingestion entry point. Builds or reuses context,
        resolves workflow, runs pipeline, returns DocumentIngestionResult.
        """

        # ------------------------------------------------------------
        # 1) Build context if needed
        # ------------------------------------------------------------
        if context is None:
            context = IngestionContext.create(
                filename=filename,
                data=data,
                media_type=media_type,
                metadata=metadata,
                registry=None,
                document_store=None,
                chunk_store=None,
                metadata_store=None,
                object_storage=None,
                chunker=None,
                embedding_service=None,
            )

        workflow_steps = self.route(media_type=media_type)

        # ------------------------------------------------------------
        # 3) Run pipeline
        # ------------------------------------------------------------
        await self.pipeline.run(context, workflow_steps)

        # ------------------------------------------------------------
        # 4) Validate that pipeline produced required artifacts
        # ------------------------------------------------------------
        if context.asset is None:
            raise RuntimeError("Pipeline completed but did not produce DocumentAsset.")

        if context.document_record is None:
            raise RuntimeError("Pipeline completed but did not produce DocumentRecord.")

        if context.parsed_document is None:
            raise RuntimeError("Pipeline completed but did not produce ParsedDocument.")

        # chunks / embeddings may be empty but must exist as lists
        chunks: List[ChunkRecord] = context.chunks or []
        embeddings: List[EmbeddingRecord] = context.embeddings or []

        # ------------------------------------------------------------
        # 5) Build final result
        # ------------------------------------------------------------
        result = DocumentIngestionResult(
            asset=context.asset,
            parsed_document=context.parsed_document,
            stored_document=context.document_record,
            chunks=chunks,
            embedded_chunk_ids=[e.chunk_id for e in embeddings] if embeddings else None,
            document_id=context.document_id,
            status=IngestionStatus.COMPLETED,
            events=context.events or [],
            embeddings=embeddings,
            metadata=context.request_metadata or {},
            storage={
                "object_key": context.asset.object_key,
                "document_store": context.document_record.metadata,
            },
        )

        # Mark final event
        result.add_event("finalize", IngestionStatus.COMPLETED, "Ingestion completed successfully.")

        return result
