from __future__ import annotations

import math
from collections.abc import Sequence

from engines.knowledge.rag.models import DocumentChunk
from engines.knowledge.rag.reranking.base_reranker import BaseReranker


class Reranker(BaseReranker):
    """Lightweight production-safe reranker.

    Scores chunks using token overlap, phrase containment, and length-normalized
    recall so the pipeline works even without a heavy cross-encoder dependency.
    """

    async def rerank(self, query: str, chunks: Sequence[DocumentChunk]) -> list[float]:
        query_tokens = self._tokenize(query)
        query_set = set(query_tokens)
        scores: list[float] = []
        for chunk in chunks:
            chunk_tokens = self._tokenize(chunk.text)
            chunk_set = set(chunk_tokens)
            overlap = len(query_set & chunk_set)
            precision = overlap / (len(chunk_set) or 1)
            recall = overlap / (len(query_set) or 1)
            phrase_bonus = 0.15 if query.casefold() in chunk.text.casefold() else 0.0
            density_bonus = min(0.2, overlap / max(1, math.sqrt(len(chunk_tokens) or 1)))
            score = (0.45 * recall) + (0.3 * precision) + phrase_bonus + density_bonus
            scores.append(round(score, 6))
        return scores

    def _tokenize(self, text: str) -> list[str]:
        return [token.casefold() for token in text.split() if token.strip()]
