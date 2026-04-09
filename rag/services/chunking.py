from __future__ import annotations

from typing import List

from config.models.rag.rag_models import Document, DocumentChunk


class Chunker:
    """Document chunker with sentence-aware overlap and stable chunk IDs."""

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 120):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    async def create_chunks(self, document: Document) -> List[DocumentChunk]:
        text = (document.metadata or {}).get("text") or ""
        if not text:
            return []

        windows = self._split_text(text)
        chunks: List[DocumentChunk] = []
        for index, chunk_text in enumerate(windows):
            chunks.append(
                DocumentChunk(
                    chunk_id=f"{document.document_id}:chunk:{index}",
                    document_id=document.document_id,
                    text=chunk_text,
                    embedding=None,
                    metadata={
                        "title": document.title,
                        "source": document.source,
                        "chunk_index": index,
                        "document_metadata": document.metadata or {},
                    },
                )
            )
        return chunks

    def _split_text(self, text: str) -> List[str]:
        clean_text = " ".join(text.split())
        if len(clean_text) <= self.chunk_size:
            return [clean_text]

        chunks: List[str] = []
        start = 0
        text_length = len(clean_text)
        while start < text_length:
            end = min(start + self.chunk_size, text_length)
            if end < text_length:
                boundary = clean_text.rfind(" ", start, end)
                if boundary > start + self.chunk_size // 2:
                    end = boundary
            chunk = clean_text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= text_length:
                break
            start = max(0, end - self.chunk_overlap)
        return chunks
