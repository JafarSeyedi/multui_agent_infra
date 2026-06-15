from __future__ import annotations

from typing import Any

from .base_retriever import BaseRetriever
from .retriever_result import RetrievalResult
from engines.knowledge.rag.models import DocumentChunk
from ..embedding import EmbeddingModel
from ....storage.vector.base import VectorDBAdapter


class VectorRetriever(BaseRetriever):
    def __init__(self, vector_db: VectorDBAdapter, embedding_model: EmbeddingModel):
        self.vector_db = vector_db
        self.embedding_model = embedding_model

    async def search(
        self,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievalResult]:
        embedding = await self.embedding_model.embed_one(query)
        results = await self.vector_db.query(vector=embedding, top_k=top_k, filters=filters)

        output: list[RetrievalResult] = []
        for item in results:
            metadata = dict(item)
            metadata.pop("_id", None)
            score = float(metadata.pop("_score", 0.0))
            chunk = self._result_to_chunk(metadata)
            output.append(
                RetrievalResult(
                    chunk=chunk,
                    score=score,
                    source="vector",
                    meta={"vector_raw_score": score},
                )
            )
        return output

    def _result_to_chunk(self, payload: dict[str, Any]) -> DocumentChunk:
        if {"chunk_id", "document_id", "text"}.issubset(payload.keys()):
            return DocumentChunk(**payload)

        metadata = dict(payload.get("metadata") or {})
        return DocumentChunk(
            chunk_id=str(payload.get("chunk_id") or payload.get("id") or payload.get("_id") or "unknown"),
            document_id=str(payload.get("document_id") or metadata.get("document_id") or "unknown"),
            text=str(payload.get("text") or metadata.get("text") or ""),
            embedding=payload.get("embedding"),
            metadata=metadata,
        )
