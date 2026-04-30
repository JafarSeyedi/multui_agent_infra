from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

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
    ) -> List[ChunkRecord]:
        ...
