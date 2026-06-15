# engines/document/ingestion/ingestion_context.py
from __future__ import annotations

import hashlib
import uuid
from typing import Any
from typing import Optional

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from ..chunking.base import BaseChunker
from ..chunking.base import ChunkingConfig
from ..embedding.service import DocumentEmbeddingService
from ..models.base import BaseDocument
from ..models.document_registry import DocumentRegistry
from ..models.media_types import MediaType
from ..storage.chunk_store import ChunkStore
from ..storage.document_store import DocumentStore
from ..storage.metadata_store import MetadataStore
from .ingestion_models import ChunkRecord
from .ingestion_models import DocumentAsset
from .ingestion_models import DocumentRecord
from .ingestion_models import EmbeddingRecord
from .ingestion_models import IngestionEvent
from .ingestion_models import ParsedDocument
from engines.storage.object.base import ObjectStorage


class IngestionContext(BaseModel):
    """
    Context used throughout the ingestion pipeline.
    Steps mutate this context progressively.
    """

    # ------------------------------------------------------------------
    # Core ingestion identifiers
    # ------------------------------------------------------------------
    document_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    object_key: str = ""
    filename: str
    media_type: MediaType
    sha256: str
    data: bytes

    # Raw upstream metadata (upload/batch)
    request_metadata: dict[str, Any] = Field(default_factory=dict)

    # ------------------------------------------------------------------
    # Parsing and document structures
    # ------------------------------------------------------------------
    # BaseDocument (raw internal representation)
    parsed_document: BaseDocument | None = None

    # More precise parsed output (the one used in ingestion_models)
    final_parsed_document: ParsedDocument | None = None

    # ------------------------------------------------------------------
    # Storage-level records
    # ------------------------------------------------------------------
    # Historical fields (kept for backward compatibility)
    asset_record: DocumentAsset | None = None
    document_record: DocumentRecord | None = None

    # Modern unified fields (direct mapping to DocumentIngestionResult)
    asset: DocumentAsset | None = None

    # ------------------------------------------------------------------
    # Chunking / Embedding pipeline outputs
    # ------------------------------------------------------------------
    chunks: list[ChunkRecord] = Field(default_factory=list)
    embeddings: list[EmbeddingRecord] = Field(default_factory=list)
    embedded_chunk_ids: list[str] = Field(default_factory=list)

    # Events collected during steps
    events: list[IngestionEvent] = Field(default_factory=list)

    # Pipeline config
    chunking: ChunkingConfig | None = None
    embed: bool = True

    # ------------------------------------------------------------------
    # DI‑injected subsystem references
    # ------------------------------------------------------------------
    registry: DocumentRegistry | None = None
    document_store: DocumentStore | None = None
    chunk_store: ChunkStore | None = None
    metadata_store: MetadataStore | None = None
    object_storage: ObjectStorage | None = None
    chunker: BaseChunker | None = None
    embedding_service: DocumentEmbeddingService | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # ------------------------------------------------------------------
    # Factory constructor
    # ------------------------------------------------------------------
    @classmethod
    def create(
        cls,
        *,
        filename: str,
        data: bytes,
        media_type: MediaType,
        metadata: dict[str, Any] | None = None,
        chunking: ChunkingConfig | None = None,
        embed: bool = True,
        registry: DocumentRegistry | None = None,
        document_store: DocumentStore | None = None,
        chunk_store: ChunkStore | None = None,
        metadata_store: MetadataStore | None = None,
        object_storage: ObjectStorage | None = None,
        chunker: BaseChunker | None = None,
        embedding_service: DocumentEmbeddingService | None = None,
    ) -> IngestionContext:

        checksum = hashlib.sha256(data).hexdigest()

        return cls(
            filename=filename,
            data=data,
            media_type=media_type,
            sha256=checksum,
            request_metadata=metadata or {},
            chunking=chunking,
            embed=embed,
            registry=registry,
            document_store=document_store,
            chunk_store=chunk_store,
            metadata_store=metadata_store,
            object_storage=object_storage,
            chunker=chunker,
            embedding_service=embedding_service,
        )

    # ------------------------------------------------------------------
    # Helper constructors used by step_store
    # ------------------------------------------------------------------
    def build_asset_record(self) -> DocumentAsset:
        """
        Build DocumentAsset from current state.
        This is the storage-level representation (object store).
        """
        return DocumentAsset(
            document_id=self.document_id,
            media_type=self.media_type,
            sha256=self.sha256,
            size=len(self.data),
            object_key=self.object_key,
            metadata=self.request_metadata.copy(),
        )

    def build_document_record(self) -> DocumentRecord:
        """
        Build DocumentRecord (database-level representation).
        """
        assert self.parsed_document is not None

        preview = None
        if getattr(self.parsed_document, "raw_text", None) and self.parsed_document.raw_text:
            preview = self.parsed_document.raw_text[:200]

        return DocumentRecord(
            document_id=self.document_id,
            filename=self.filename,
            title=self.parsed_document.title or self.filename,
            sha256=self.sha256,
            media_type=self.media_type,
            object_key=self.object_key,
            text_preview=preview,
            metadata=self.request_metadata.copy(),
        )
