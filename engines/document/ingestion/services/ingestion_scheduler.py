# engines/document/ingestion/services/ingestion_scheduler.py
from __future__ import annotations

import asyncio
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from ...models.media_detection import detect_media_type
from .upload_service import UploadService


class IngestionScheduler:
    """
    Scheduled ingestion from:
        - s3 bucket (sync or watcher)
        - FTP directory
        - local folder
        - remote mounts
        - iterable queues
        - any iterable file source
    Designed for cron-like or event-like ingestion.
    """

    def __init__(self, upload_service: UploadService):
        self.upload_service = upload_service

    # ------------------------------------------------------------------
    async def ingest_folder(self, folder: str):
        base = Path(folder)

        for path in base.iterdir():
            if not path.is_file():
                continue

            data = path.read_bytes()
            media_type = detect_media_type(path=path.name, data=data)

            # UploadService.ingest() will create IngestionContext internally
            await self.upload_service.ingest(
                filename=path.name,
                media_type=media_type,
                data=data,
                metadata={},       # no additional metadata
            )

    # ------------------------------------------------------------------
    async def ingest_iterable(self, items: Iterable[dict[str, Any]]):
        """
        items example:
        {
            "document_id": "...",
            "filename": "...",
            "data": b"...",
            "media_type": media_type,
            "metadata": {...}
        }
        """

        async def handle(item):
            return await self.upload_service.ingest(
                filename=item["filename"],
                media_type=item["media_type"],
                data=item["data"],
                metadata=item.get("metadata"),
            )

        return await asyncio.gather(*(handle(i) for i in items))
