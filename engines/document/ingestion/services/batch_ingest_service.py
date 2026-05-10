# engines/document/ingestion/services/batch_ingest_service.py
from __future__ import annotations

import asyncio
from typing import Any

from ..ingestion_context import IngestionContext
from ..ingestion_models import DocumentIngestionResult
from .upload_service import UploadService


class BatchIngestService:
    """
    Run ingestion for multiple files in parallel or sequential mode.
    """

    def __init__(self, upload_service: UploadService):
        self.upload_service = upload_service

    # ------------------------------------------------------------------
    async def ingest_sequential(
        self,
        items: list[dict[str, Any]],
    ) -> list[DocumentIngestionResult]:

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
        items: list[dict[str, Any]],
        limit: int = 5,
    ) -> list[DocumentIngestionResult]:

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
