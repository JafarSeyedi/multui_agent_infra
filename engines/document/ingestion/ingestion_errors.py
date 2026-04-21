# engines/document/ingestion/ingestion_errors.py

from __future__ import annotations

from typing import Optional, Any
from datetime import datetime


class IngestionError(Exception):
    """
    Base ingestion exception for all ingestion pipeline failures.
    Includes contextual metadata for debugging and logging.
    """

    def __init__(
        self,
        message: str,
        *,
        step: Optional[str] = None,
        details: Optional[Any] = None,
    ):
        super().__init__(message)
        self.step = step
        self.details = details
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> dict:
        return {
            "message": str(self),
            "step": self.step,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
        }


# -------------------------------------------------------------
# Specific ingestion exceptions
# -------------------------------------------------------------

class InvalidDocumentError(IngestionError):
    """Raised when the document is empty, corrupted, or invalid."""
    pass


class UnsupportedMediaTypeError(IngestionError):
    """Raised when no parser is registered for the media type."""

    def __init__(self, media_type: str, *, step: Optional[str] = None):
        super().__init__(
            message=f"Unsupported media type: {media_type}",
            step=step or "parse",
            details={"media_type": media_type},
        )


class ExtractionFailed(IngestionError):
    """Raised when extraction step fails."""
    pass


class ParseFailed(IngestionError):
    """Raised when parser fails to convert bytes to BaseDocument."""
    pass


class ChunkingFailed(IngestionError):
    """Raised when chunker fails."""
    pass


class EmbeddingFailed(IngestionError):
    """Raised when embedding service fails."""
    pass


class StorageFailed(IngestionError):
    """Raised when document/chunk/meta storage fails."""
    pass


class FinalizationFailed(IngestionError):
    """Raised when final metadata update or cleanup fails."""
    pass


# -------------------------------------------------------------
# Pipeline orchestrator wrapper
# -------------------------------------------------------------

class IngestionStepFailed(IngestionError):
    """
    Raised by the pipeline orchestrator.

    Wraps the real underlying exception and attaches the exact
    pipeline step name, providing a consistent failure envelope.
    """

    def __init__(self, step: str, exc: Exception):
        super().__init__(
            message=f"Ingestion step '{step}' failed: {exc}",
            step=step,
            details={"original_exception": repr(exc)},
        )
        self.original_exception = exc
