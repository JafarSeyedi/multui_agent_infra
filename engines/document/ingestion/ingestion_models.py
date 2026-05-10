# engines/document/ingestion/ingestion_models.py
from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel
from pydantic import Field

from ..models.base import BaseDocument
from ..models.media_types import MediaType



# -------------------------------------------------------------------
# DOCUMENT + PARSED MODELS
# -------------------------------------------------------------------
@dataclass
class DocumentAsset:
    """
    Physical binary asset stored in object storage or file store.
    """
    document_id: str
    media_type: MediaType                 # UploadService._guess_media_type()
    object_key: str
    sha256: str
    size: int
    storage_location: StorageLocation = StorageLocation.OBJECT_STORAGE
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)

class DocumentRecord(BaseModel):
    """
    Metadata-level document record (stored in DocumentStore).
    """
    document_id: str
    filename: str | None
    title: str | None
    media_type: MediaType                 # UploadService._guess_media_type()
    sha256: str
    object_key: str | None = None      # S3/GCS/ObjectStorage path
    text_preview: str | None = None    # first 200 chars
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


@dataclass
class ParsedDocument:
    """
    Output of parser layer.
    Raw text + metadata extracted.
    """
    document_id: str
    text: str
    num_chars: int
    num_words: int
    parser_name: str
    metadata: dict[str, Any] = field(default_factory=dict)


# -------------------------------------------------------------------
# CHUNK + EMBEDDING MODELS
# -------------------------------------------------------------------

class ChunkRecord(BaseModel):
    """
    A single semantic chunk produced during document ingestion.
    Suitable for indexing, embedding, and retrieval.
    """

    chunk_id: str                          # unique hash-id
    document_id: str                       # owning document
    index: int                              # sequential index within document

    text: str                               # actual chunk text
    token_count_estimate: int               # estimated token count (cheap method)

    start_char: int                         # char offset in full document text
    end_char: int                           # char offset (exclusive)

    embeddings: list[EmbeddingRecord] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

# -------------------------------------------------------------------
# ENUMS
# -------------------------------------------------------------------

class IngestionStatus(str, Enum):
    PENDING = "pending"
    EXTRACTED = "extracted"
    PARSED = "parsed"
    CHUNKED = "chunked"
    EMBEDDED = "embedded"
    STORED = "stored"
    COMPLETED = "completed"
    FAILED = "failed"


# -------------------------------------------------------------------
# BASIC SUPPORT MODELS
# -------------------------------------------------------------------

class StorageLocation(str, Enum):
    VECTOR_DB = "vector_db"
    DOCUMENT_DB = "document_db"
    CHUNK_DB = "chunk_db"
    OBJECT_STORAGE = "object_storage"
    TEMP_STORAGE = "temp_storage"


@dataclass
class IngestionEvent:
    """
    A single event in the document’s ingestion lifecycle.
    Used for auditing + observability.
    """
    step: str
    status: IngestionStatus
    message: str | None = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)



@dataclass
class EmbeddingRecord:
    """
    Vector embedding of each chunk.
    """
    document_id: str
    chunk_id: str
    vector: list[float]
    dim: int
    provider: str
    created_at: datetime = field(default_factory=datetime.utcnow)

# -------------------------------------------------------------------
# FINAL RESULT
# -------------------------------------------------------------------

class DocumentIngestionResult(BaseModel):
    """
    Returned by IngestionService after store step.
    """
    asset: DocumentAsset
    parsed_document: BaseDocument
    stored_document: DocumentRecord
    chunks: list[ChunkRecord] = field(default_factory=list)
    embedded_chunk_ids: list[str] | None = None

    document_id: str
    status: IngestionStatus
    events: list[IngestionEvent] = field(default_factory=list)
    embeddings: list[EmbeddingRecord] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    storage: dict[str, Any] = field(default_factory=dict)

    def add_event(self, step: str, status: IngestionStatus, message: str | None = None, **kwargs):
        self.events.append(IngestionEvent(step=step, status=status, message=message, metadata=kwargs))
