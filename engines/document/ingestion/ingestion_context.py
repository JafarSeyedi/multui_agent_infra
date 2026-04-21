# engines/document/ingestion/ingestion_context.py

from __future__ import annotations

import uuid
import hashlib
from typing import Optional, Dict, Any, List

from pydantic import BaseModel, Field

from engines.document.ingestion.ingestion_models import (
    DocumentAsset,
    DocumentRecord,
    ParsedDocument,
    ChunkRecord,
    EmbeddingRecord,
    IngestionEvent,
)
from engines.document.models.base import BaseDocument
from engines.document.models.media_types import MediaType

from engines.storage.object.base import ObjectStorage
from engines.document.models.document_registry import DocumentRegistry
from engines.document.chunking.base import ChunkingConfig, BaseChunker
from engines.document.storage.document_store import DocumentStore
from engines.document.storage.chunk_store import ChunkStore
from engines.document.storage.metadata_store import MetadataStore
from engines.document.embedding.service import DocumentEmbeddingService


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
    request_metadata: Dict[str, Any] = Field(default_factory=dict)

    # ------------------------------------------------------------------
    # Parsing and document structures
    # ------------------------------------------------------------------
    # BaseDocument (raw internal representation)
    parsed_document: Optional[BaseDocument] = None

    # More precise parsed output (the one used in ingestion_models)
    final_parsed_document: Optional[ParsedDocument] = None

    # ------------------------------------------------------------------
    # Storage-level records
    # ------------------------------------------------------------------
    # Historical fields (kept for backward compatibility)
    asset_record: Optional[DocumentAsset] = None
    document_record: Optional[DocumentRecord] = None

    # Modern unified fields (direct mapping to DocumentIngestionResult)
    asset: Optional[DocumentAsset] = None

    # ------------------------------------------------------------------
    # Chunking / Embedding pipeline outputs
    # ------------------------------------------------------------------
    chunks: List[ChunkRecord] = Field(default_factory=list)
    embeddings: List[EmbeddingRecord] = Field(default_factory=list)
    embedded_chunk_ids: List[str] = Field(default_factory=list)

    # Events collected during steps
    events: List[IngestionEvent] = Field(default_factory=list)

    # Pipeline config
    chunking: Optional[ChunkingConfig] = None
    embed: bool = True

    # ------------------------------------------------------------------
    # DI‑injected subsystem references
    # ------------------------------------------------------------------
    registry: Optional[DocumentRegistry] = None
    document_store: Optional[DocumentStore] = None
    chunk_store: Optional[ChunkStore] = None
    metadata_store: Optional[MetadataStore] = None
    object_storage: Optional[ObjectStorage] = None
    chunker: Optional[BaseChunker] = None
    embedding_service: Optional[DocumentEmbeddingService] = None

    class Config:
        arbitrary_types_allowed = True

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
        metadata: Optional[Dict[str, Any]] = None,
        chunking: Optional[ChunkingConfig] = None,
        embed: bool = True,
        registry: Optional[DocumentRegistry] = None,
        document_store: Optional[DocumentStore] = None,
        chunk_store: Optional[ChunkStore] = None,
        metadata_store: Optional[MetadataStore] = None,
        object_storage: Optional[ObjectStorage] = None,
        chunker: Optional[BaseChunker] = None,
        embedding_service: Optional[DocumentEmbeddingService] = None,
    ) -> "IngestionContext":

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

