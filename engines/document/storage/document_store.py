from __future__ import annotations

from typing import Union

from ..ingestion.ingestion_models import DocumentRecord
from engines.knowledge.rag.rag_models import Document
from engines.knowledge.rag.rag_models import DocumentChunk
from engines.storage.key_value.base import KeyValueStorage


StoredDocument = Union[DocumentRecord, Document]


class DocumentStore:
    """Document repository with backward-compatible chunk access for the RAG layer."""

    def __init__(self, storage: KeyValueStorage | None = None) -> None:
        self.storage = storage
        self.documents: dict[str, StoredDocument] = {}
        self.chunks: dict[str, DocumentChunk] = {}
        self._chunks_by_doc: dict[str, list[str]] = {}

    def _document_key(self, document_id: str) -> str:
        return f"doc:{document_id}"

    def _chunk_key(self, chunk_id: str) -> str:
        return f"chunk:{chunk_id}"

    async def add_document(self, doc: StoredDocument) -> None:
        self.documents[doc.document_id] = doc
        if self.storage is not None:
            if isinstance(doc, DocumentRecord):
                stored_doc = {"kind": "document_record", "payload": doc.model_dump(mode="json")}
                await self.storage.set(self._document_key(doc.document_id), stored_doc)
            else:
                stored_doc = {"kind": "rag_document", "payload": doc.model_dump(mode="json")}
                await self.storage.set(self._document_key(doc.document_id), stored_doc)

    async def add_chunks(self, chunks: list[DocumentChunk]) -> None:
        for chunk in chunks:
            self.chunks[chunk.chunk_id] = chunk
            self._chunks_by_doc.setdefault(chunk.document_id, [])
            if chunk.chunk_id not in self._chunks_by_doc[chunk.document_id]:
                self._chunks_by_doc[chunk.document_id].append(chunk.chunk_id)
            if self.storage is not None:
                await self.storage.set(self._chunk_key(chunk.chunk_id), chunk.model_dump(mode="json"))

    async def get_document(self, document_id: str) -> StoredDocument | None:
        cached = self.documents.get(document_id)
        if cached is not None:
            return cached
        if self.storage is None:
            return None
        data = await self.storage.get(self._document_key(document_id))
        if not isinstance(data, dict):
            return None
        payload = data.get("payload")
        if not isinstance(payload, dict):
            return None
        kind = data.get("kind")
        if kind == "document_record":
            document: StoredDocument = DocumentRecord(**payload)
        else:
            document = Document(**payload)
        self.documents[document_id] = document
        return document

    async def get_document_record(self, document_id: str) -> DocumentRecord | None:
        document = await self.get_document(document_id)
        if isinstance(document, DocumentRecord):
            return document
        return None

    async def get_chunk(self, chunk_id: str) -> DocumentChunk | None:
        cached = self.chunks.get(chunk_id)
        if cached is not None:
            return cached
        if self.storage is None:
            return None
        data = await self.storage.get(self._chunk_key(chunk_id))
        if not isinstance(data, dict):
            return None
        chunk = DocumentChunk(**data)
        self.chunks[chunk_id] = chunk
        self._chunks_by_doc.setdefault(chunk.document_id, [])
        if chunk_id not in self._chunks_by_doc[chunk.document_id]:
            self._chunks_by_doc[chunk.document_id].append(chunk_id)
        return chunk

    async def get_chunks_by_doc(self, document_id: str) -> list[DocumentChunk]:
        chunk_ids = self._chunks_by_doc.get(document_id)
        if chunk_ids:
            return [self.chunks[chunk_id] for chunk_id in chunk_ids if chunk_id in self.chunks]
        if self.storage is None:
            return [chunk for chunk in self.chunks.values() if chunk.document_id == document_id]
        keys = await self.storage.list_keys(prefix="chunk:")
        chunks: list[DocumentChunk] = []
        for key in keys:
            data = await self.storage.get(key)
            if isinstance(data, dict) and data.get("document_id") == document_id:
                chunk = DocumentChunk(**data)
                self.chunks[chunk.chunk_id] = chunk
                self._chunks_by_doc.setdefault(document_id, []).append(chunk.chunk_id)
                chunks.append(chunk)
        return chunks

    async def list_documents(self) -> list[DocumentRecord]:
        records: list[DocumentRecord] = []
        for document in self.documents.values():
            if isinstance(document, DocumentRecord):
                records.append(document)
        if self.storage is None:
            return records
        keys = await self.storage.list_keys(prefix="doc:")
        for key in keys:
            data = await self.storage.get(key)
            if not isinstance(data, dict):
                continue
            if data.get("kind") != "document_record":
                continue
            payload = data.get("payload")
            if isinstance(payload, dict):
                record = DocumentRecord(**payload)
                self.documents[record.document_id] = record
                records.append(record)
        deduped = {record.document_id: record for record in records}
        return list(deduped.values())

    async def search_by_keyword(self, keyword: str) -> list[DocumentChunk]:
        needle = keyword.casefold()
        return [chunk for chunk in self.chunks.values() if needle in chunk.text.casefold()]

    async def delete_document(self, document_id: str) -> None:
        self.documents.pop(document_id, None)
        chunk_ids = self._chunks_by_doc.pop(document_id, [])
        for chunk_id in chunk_ids:
            self.chunks.pop(chunk_id, None)
            if self.storage is not None:
                await self.storage.delete(self._chunk_key(chunk_id))
        if self.storage is not None:
            await self.storage.delete(self._document_key(document_id))
