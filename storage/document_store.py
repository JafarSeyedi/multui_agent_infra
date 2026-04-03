from __future__ import annotations

from typing import Dict, List, Optional

from config.models.rag.rag_models import Document, DocumentChunk

from .base_storage import StorageAdapter


class DocumentStore:
    """Document repository with in-memory caching and optional persistence."""

    def __init__(self, storage: Optional[StorageAdapter] = None):
        self.storage = storage
        self.documents: Dict[str, Document] = {}
        self.chunks: Dict[str, DocumentChunk] = {}
        self._chunks_by_doc: Dict[str, List[str]] = {}

    async def add_document(self, doc: Document) -> None:
        self.documents[doc.document_id] = doc
        if self.storage:
            await self.storage.save(f"doc:{doc.document_id}", doc.dict())

    async def add_chunks(self, chunks: List[DocumentChunk]) -> None:
        for chunk in chunks:
            self.chunks[chunk.chunk_id] = chunk
            self._chunks_by_doc.setdefault(chunk.document_id, [])
            if chunk.chunk_id not in self._chunks_by_doc[chunk.document_id]:
                self._chunks_by_doc[chunk.document_id].append(chunk.chunk_id)
            if self.storage:
                await self.storage.save(f"chunk:{chunk.chunk_id}", chunk.dict())

    async def get_document(self, document_id: str) -> Optional[Document]:
        if document_id in self.documents:
            return self.documents[document_id]
        if self.storage:
            data = await self.storage.load(f"doc:{document_id}")
            if data:
                document = Document(**data)
                self.documents[document_id] = document
                return document
        return None

    async def get_chunk(self, chunk_id: str) -> Optional[DocumentChunk]:
        if chunk_id in self.chunks:
            return self.chunks[chunk_id]
        if self.storage:
            data = await self.storage.load(f"chunk:{chunk_id}")
            if data:
                chunk = DocumentChunk(**data)
                self.chunks[chunk_id] = chunk
                self._chunks_by_doc.setdefault(chunk.document_id, []).append(chunk.chunk_id)
                return chunk
        return None

    async def get_chunks_by_doc(self, document_id: str) -> List[DocumentChunk]:
        chunk_ids = self._chunks_by_doc.get(document_id, [])
        if chunk_ids:
            return [self.chunks[chunk_id] for chunk_id in chunk_ids if chunk_id in self.chunks]

        if self.storage:
            keys = await self.storage.list_keys(prefix="chunk:")
            chunks: List[DocumentChunk] = []
            for key in keys:
                data = await self.storage.load(key)
                if data and data.get("document_id") == document_id:
                    chunk = DocumentChunk(**data)
                    self.chunks[chunk.chunk_id] = chunk
                    self._chunks_by_doc.setdefault(document_id, []).append(chunk.chunk_id)
                    chunks.append(chunk)
            return chunks
        return []

    async def search_by_keyword(self, keyword: str) -> List[DocumentChunk]:
        needle = keyword.casefold()
        return [chunk for chunk in self.chunks.values() if needle in chunk.text.casefold()]

    async def delete_document(self, document_id: str) -> None:
        self.documents.pop(document_id, None)
        chunk_ids = self._chunks_by_doc.pop(document_id, [])
        for chunk_id in chunk_ids:
            self.chunks.pop(chunk_id, None)
            if self.storage:
                await self.storage.delete(f"chunk:{chunk_id}")
        if self.storage:
            await self.storage.delete(f"doc:{document_id}")
