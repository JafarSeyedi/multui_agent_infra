from __future__ import annotations

from abc import ABC
from abc import abstractmethod

from ..ingestion.ingestion_models import ChunkRecord
from ..models.base import BaseDocument
from .models import ChunkingConfig


class BaseChunker(ABC):
    """Abstract contract for document chunking strategies."""

    @abstractmethod
    async def chunk_document(
        self,
        document: BaseDocument,
        config: ChunkingConfig | None = None,
    ) -> list[ChunkRecord]:
        ...
