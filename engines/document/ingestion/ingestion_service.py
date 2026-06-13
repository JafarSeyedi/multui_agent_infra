# engines/document/ingestion/ingestion_service.py
from __future__ import annotations

from typing import Any

from ..models.document_registry import DocumentRegistry
from .ingestion_context import IngestionContext
from .ingestion_errors import IngestionError
from .ingestion_models import DocumentIngestionResult
from .ingestion_runner import IngestionRunner
from .workflow_registry import WorkflowRegistry


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
        return registry

    async def ingest(
        self,
        *,
        filename: str,
        media_type,
        data: bytes,
        metadata: dict[str, Any] | None = None,
        context: IngestionContext | None = None,
    ) -> DocumentIngestionResult:
        runner = IngestionRunner(workflow_registry=self.workflow_registry)

        try:
            return await runner.execute(
                filename=filename,
                media_type=media_type,
                data=data,
                metadata=metadata,
                context=context,
            )

        except IngestionError:
            raise

        except Exception as exc:
            raise IngestionError(f"Ingestion failed: {exc}") from exc
