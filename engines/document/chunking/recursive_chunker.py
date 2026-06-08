from __future__ import annotations

import hashlib
from collections.abc import Sequence

from ..ingestion.ingestion_models import ChunkRecord
from ..models.base import BaseDocument
from .base import BaseChunker
from .models import ChunkingConfig


class RecursiveTextChunker(BaseChunker):
    """Text chunker that recursively splits by semantic separators before hard wrapping."""

    async def chunk_document(
        self,
        document: BaseDocument,
        config: ChunkingConfig | None = None,
    ) -> list[ChunkRecord]:
        effective = config or ChunkingConfig()
        if not document.raw_text:
            return []
        text = document.raw_text.strip()

        segments = self._split_text(text, effective.separators, effective.chunk_size)
        merged = self._merge_segments(segments, effective)
        return [
            self._build_chunk(document=document, index=index, text=chunk_text, full_text=text)
            for index, chunk_text in enumerate(merged)
        ]

    def _split_text(self, text: str, separators: Sequence[str], max_size: int) -> list[str]:
        if len(text) <= max_size:
            return [text]
        if not separators:
            return self._hard_split(text, max_size)

        separator = separators[0]
        pieces = text.split(separator)
        if len(pieces) == 1:
            return self._split_text(text, separators[1:], max_size)

        results: list[str] = []
        current = ""
        for piece in pieces:
            candidate = piece if not current else current + separator + piece
            if len(candidate) <= max_size:
                current = candidate
                continue
            if current:
                results.extend(self._split_text(current, separators[1:], max_size))
            current = piece
        if current:
            results.extend(self._split_text(current, separators[1:], max_size))
        return results

    def _hard_split(self, text: str, max_size: int) -> list[str]:
        return [text[i : i + max_size] for i in range(0, len(text), max_size)]

    def _merge_segments(self, segments: Sequence[str], config: ChunkingConfig) -> list[str]:
        chunks: list[str] = []
        current = ""
        for segment in segments:
            stripped = segment.strip()
            if not stripped:
                continue
            if not current:
                current = stripped
                continue
            candidate = current + ("\n\n" if config.keep_paragraph_boundaries else " ") + stripped
            if len(candidate) <= config.chunk_size:
                current = candidate
                continue
            if len(current) >= config.min_chunk_size:
                chunks.append(current)
                overlap = current[-config.chunk_overlap :] if config.chunk_overlap > 0 else ""
                current = (overlap + " " + stripped).strip() if overlap else stripped
            else:
                current = candidate[: config.chunk_size]
                chunks.append(current)
                tail = candidate[config.chunk_size - config.chunk_overlap :]
                current = tail.strip()
        if current:
            chunks.append(current)
        return chunks

    def _build_chunk(self, document: BaseDocument, index: int, text: str, full_text: str) -> ChunkRecord:
        start = full_text.find(text)
        end = start + len(text) if start >= 0 else 0
        digest = hashlib.sha1(f"{document.document_id}:{index}:{text}".encode()).hexdigest()
        return ChunkRecord(
            chunk_id=f"chunk_{digest}",
            document_id=document.document_id,
            index=index,
            text=text,
            token_count_estimate=max(1, len(text.split())),
            start_char=max(start, 0),
            end_char=max(end, 0),
            embeddings=[],   # ← Important
            metadata={
                "source_format": document.media_type.format.value if document.media_type else "unknown",
                "chunker": "recursive",
                "chunk_size": len(text),
            },
        )
