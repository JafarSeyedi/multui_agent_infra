# engines/document/ingestion/services/async_ingest_service.py

from __future__ import annotations

from typing import Dict, Any

from .upload_service import UploadService
from ..ingestion_context import IngestionContext
from ...models.media_types import MediaType, MEDIA_TYPES
from ...models.media_detection import detect_media_type


class AsyncIngestService:
    """
    Generic async ingestion worker for queue systems.

    message example:
    {
        "filename": "...",
        "media_type": "pdf",       # optional
        "mime": "application/pdf", # optional
        "data": b"...",
        "metadata": {...},
        "context": IngestionContext
    }
    """

    def __init__(self, upload_service: UploadService):
        self.upload_service = upload_service

    # ---------------------------------------------------------
    async def process_message(self, message: Dict[str, Any]):
        context: IngestionContext = message["context"]

        # Step 1: determine media-type
        media_type = self._resolve_media_type(message)

        # Step 2: invoke ingestion
        return await self.upload_service.ingest(
            filename=message["filename"],
            media_type=media_type,
            data=message["data"],
            metadata=message.get("metadata"),
            context=context,
        )

    # ---------------------------------------------------------
    def _resolve_media_type(self, msg: Dict[str, Any]) -> MediaType:
        """
        Priority:
            1) explicit media_type key-name  (e.g. "pdf", "json")
            2) mime
            3) content detection
        """

        # case A: explicit media_type key → lookup in registry
        mt_key = msg.get("media_type")
        if isinstance(mt_key, str) and mt_key in MEDIA_TYPES:
            return MEDIA_TYPES[mt_key]

        # case B: explicit mime type
        mime = msg.get("mime")
        if mime:
            return detect_media_type(mime=mime, data=msg.get("data"))

        # case C: detect by filename + content
        return detect_media_type(
            path=msg.get("filename"),
            data=msg.get("data"),
        )
