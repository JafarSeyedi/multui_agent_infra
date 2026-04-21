from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field

from engines.document.ingestion.ingestion_models import ChunkRecord


class ChunkingConfig(BaseModel):
    chunk_size: int = 800
    chunk_overlap: int = 120
    min_chunk_size: int = 120
    separators: List[str] = Field(default_factory=lambda: ["\n\n", "\n", ". ", " "])
    keep_paragraph_boundaries: bool = True
    include_page_markers: bool = True


class ChunkingResult(BaseModel):
    chunks: List[ChunkRecord] = Field(default_factory=list)
