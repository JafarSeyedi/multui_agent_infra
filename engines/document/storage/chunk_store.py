from __future__ import annotations

from ..ingestion.ingestion_models import ChunkRecord
from engines.storage.key_value.base import KeyValueStorage
from engines.storage.vector.base import VectorDBAdapter


class ChunkStore:
    """Chunk repository with optional vector index synchronization."""

    def __init__(
        self,
        storage: KeyValueStorage | None = None,
        vector_index: VectorDBAdapter | None = None,
        vector_index_name: str = "document_chunks",
    ) -> None:
        self.storage = storage
        self.vector_index = vector_index
        self.vector_index_name = vector_index_name
        self._chunks: dict[str, ChunkRecord] = {}
        self._embeddings: dict[str, list[float]] = {}
        self._vector_ready = False

    def _key(self, chunk_id: str) -> str:
        return f"chunk:{chunk_id}"

    async def add_chunks(self, chunks: list[ChunkRecord]) -> None:
        for chunk in chunks:
            self._chunks[chunk.chunk_id] = chunk
            if self.storage is not None:
                await self.storage.set(self._key(chunk.chunk_id), chunk.model_dump(mode="json"))

    async def get_chunk(self, chunk_id: str) -> ChunkRecord | None:
        cached = self._chunks.get(chunk_id)
        if cached is not None:
            return cached
        if self.storage is None:
            return None
        data = await self.storage.get(self._key(chunk_id))
        if not isinstance(data, dict):
            return None
        chunk = ChunkRecord(**data)
        self._chunks[chunk_id] = chunk
        return chunk

    async def list_chunks_for_document(self, document_id: str) -> list[ChunkRecord]:
        if self.storage is None:
            return [chunk for chunk in self._chunks.values() if chunk.document_id == document_id]
        keys = await self.storage.list_keys(prefix="chunk:")
        chunks: list[ChunkRecord] = []
        for key in keys:
            data = await self.storage.get(key)
            if isinstance(data, dict) and data.get("document_id") == document_id:
                chunk = ChunkRecord(**data)
                self._chunks[chunk.chunk_id] = chunk
                chunks.append(chunk)
        chunks.sort(key=lambda item: item.index)
        return chunks

    async def attach_embeddings(self, embeddings: dict[str, list[float]]) -> None:
        self._embeddings.update(embeddings)
        if self.vector_index is None or not embeddings:
            return
        await self._ensure_vector_index(next(iter(embeddings.values())))
        items: list[dict[str, object]] = []
        for chunk_id, embedding in embeddings.items():
            chunk = self._chunks.get(chunk_id)
            if chunk is None:
                continue
            items.append(
                {
                    "id": chunk_id,
                    "vector": embedding,
                    "metadata": {
                        "document_id": chunk.document_id,
                        "chunk_index": chunk.index,
                        "text": chunk.text,
                    },
                }
            )
        if items:
            await self.vector_index.batch_upsert(items)

    async def search_similar(self, embedding: list[float], top_k: int = 5) -> list[DocumentChunk]:
        from engines.knowledge.rag.rag_models import DocumentChunk
        if self.vector_index is None:
            return []
        results = await self.vector_index.query(embedding, top_k=top_k)
        chunks: list[DocumentChunk] = []
        for item in results:
            chunk_id = str(item.get("_id"))
            chunk = await self.get_chunk(chunk_id)
            if chunk is None:
                continue
            chunks.append(
                DocumentChunk(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    text=chunk.text,
                    embedding=self._embeddings.get(chunk.chunk_id),
                    metadata=chunk.metadata,
                )
            )
        return chunks

    async def delete_chunks_for_document(self, document_id: str) -> None:
        chunks = await self.list_chunks_for_document(document_id)
        chunk_ids = [chunk.chunk_id for chunk in chunks]
        for chunk_id in chunk_ids:
            self._chunks.pop(chunk_id, None)
            self._embeddings.pop(chunk_id, None)
            if self.storage is not None:
                await self.storage.delete(self._key(chunk_id))
        if self.vector_index is not None and chunk_ids:
            await self.vector_index.delete(chunk_ids)

    async def _ensure_vector_index(self, sample_embedding: list[float]) -> None:
        if self.vector_index is None or self._vector_ready:
            return
        await self.vector_index.create_index(self.vector_index_name, dimension=len(sample_embedding))
        self._vector_ready = True
