# engines/document/ingestion/services/batch_ingest_service.py

from __future__ import annotations

from typing import List, Dict, Any, Optional
import asyncio

from engines.document.ingestion.services.upload_service import UploadService
from engines.document.ingestion.ingestion_context import IngestionContext
from engines.document.models.media_types import MediaType
from engines.document.ingestion.ingestion_models import DocumentIngestionResult


class BatchIngestService:
    """
    Run ingestion for multiple files in parallel or sequential mode.
    """

    def __init__(self, upload_service: UploadService):
        self.upload_service = upload_service

    # ------------------------------------------------------------------
    async def ingest_sequential(
        self,
        items: List[Dict[str, Any]],
    ) -> List[DocumentIngestionResult]:

        results = []
        for item in items:
            ctx: IngestionContext = item["context"]

            result = await self.upload_service.ingest(
                filename=item["filename"],
                media_type=item["media_type"],
                data=item["data"],
                metadata=item.get("metadata"),
                context=ctx,
            )
            results.append(result)

        return results

    # ------------------------------------------------------------------
    async def ingest_parallel(
        self,
        items: List[Dict[str, Any]],
        limit: int = 5,
    ) -> List[DocumentIngestionResult]:

        semaphore = asyncio.Semaphore(limit)

        async def handle(item):
            async with semaphore:
                return await self.upload_service.ingest(
                    filename=item["filename"],
                    media_type=item["media_type"],
                    data=item["data"],
                    metadata=item.get("metadata"),
                    context=item["context"],
                )

        return await asyncio.gather(*(handle(i) for i in items))
