# engines/document/ingestion/services/upload_service.py
from __future__ import annotations

from typing import Any, Dict, Optional, cast

from engines.document.ingestion.ingestion_context import IngestionContext
from engines.document.ingestion.ingestion_service import IngestionService
from engines.document.ingestion.ingestion_errors import IngestionError
from engines.document.models.media_types import MediaType
from engines.document.ingestion.ingestion_models import DocumentIngestionResult


class UploadService:
    """
    API-facing upload ingestion service.

    Scheduler, BatchService, AsyncQueue all call this method with
    raw inputs (document_id, filename, data, metadata).
    Only API endpoints may pre-construct context.
    """

    def __init__(self, ingestion_service: IngestionService):
        self.ingestion_service = ingestion_service

    # ------------------------------------------------------------------
    async def ingest(
        self,
        *,
        filename: str,
        media_type: MediaType,
        data: bytes,
        metadata: Optional[Dict[str, Any]] = None,
        context: Optional[IngestionContext] = None,
    ) -> DocumentIngestionResult:

        # If context is provided, use it. Otherwise pipeline will create new one.
        if context is not None:
            context = cast(IngestionContext, context)

        try:
            return await self.ingestion_service.ingest(
                filename=filename,
                media_type=media_type,
                data=data,
                metadata=metadata,
                context=context,   # may be None → ingestion_service will create
            )
        except Exception as exc:
            raise IngestionError(f"Ingestion failed: {exc}", step="service") from exc
