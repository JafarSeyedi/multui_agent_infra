import numpy as np
from typing import List

from .base import BaseCompressor
from rag.rag_models import DocumentChunk
from rag.services.embedding import EmbeddingModel


class EmbeddingCompressor(BaseCompressor):

    def __init__(
        self,
        embedding_model: EmbeddingModel,
        retain_ratio: float = 0.5,
    ):
        self.embedding_model = embedding_model
        self.retain_ratio = retain_ratio

    async def compress(
        self,
        query: str,
        chunks: List[DocumentChunk],
    ) -> List[DocumentChunk]:

        q_emb = (await self.embedding_model.embed([query]))[0]

        results = []

        for ch in chunks:

            sentences = ch.text.split(". ")

            if len(sentences) <= 1:
                results.append(ch)
                continue

            emb = await self.embedding_model.embed(sentences)

            scores = [
                float(np.dot(q_emb, s) /
                (np.linalg.norm(q_emb) * np.linalg.norm(s)))
                for s in emb
            ]

            k = max(1, int(len(sentences) * self.retain_ratio))

            top_idx = np.argsort(scores)[-k:]

            kept = [sentences[i] for i in sorted(top_idx)]

            ch.text = ". ".join(kept)

            results.append(ch)

        return results
