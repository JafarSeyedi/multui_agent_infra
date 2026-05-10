# engines/document/ingestion/ingestion_validator.py
from __future__ import annotations

from typing import Any

from ..models.media_types import MEDIA_TYPES
from ..models.media_types import MediaType
from .ingestion_errors import InvalidDocumentError
from .ingestion_errors import UnsupportedMediaTypeError


class IngestionValidator:
    """
    Validates canonical ingestion input BEFORE pipeline execution.
    Prevents wasted compute and early-detects user errors.
    """

    @staticmethod
    def validate_input(
        *,
        document_id: str,
        filename: str,
        media_type: str | MediaType,
        data: bytes,
        metadata: dict[str, Any] | None,
    ):
        if not document_id:
            raise InvalidDocumentError("document_id must not be empty")

        if not filename:
            raise InvalidDocumentError("filename must not be empty")

        if not data or len(data) == 0:
            raise InvalidDocumentError("Cannot ingest an empty file")

        # Validate media_type
        if isinstance(media_type, MediaType):
            try:
                _ = media_type
            except Exception:
                raise UnsupportedMediaTypeError(media_type.mime)
        if isinstance(media_type, str):
            try:
                _ = MEDIA_TYPES[media_type]
            except Exception:
                raise UnsupportedMediaTypeError(media_type)

        # metadata must be dict-like
        if metadata is not None and not isinstance(metadata, dict):
            raise InvalidDocumentError("metadata must be a dict if provided")
