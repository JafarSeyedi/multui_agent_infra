# rag/evidence/evidence_clusterer.py
from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.cluster import KMeans  # type: ignore[import-untyped]

from engines.knowledge.rag.models import RetrievedDocument


class EvidenceClusterer:

    def __init__(self, embedding_model: Any) -> None:
        self.embedding_model = embedding_model

    async def cluster(
        self,
        results: list[RetrievedDocument],
        k: int = 4,
    ) -> list[RetrievedDocument]:

        if not results:
            return []

        texts = [r.chunk.text for r in results]
        embeddings = await self.embedding_model.embed_batch(texts)

        X = np.array(embeddings)
        k = min(k, len(results))

        model = KMeans(n_clusters=k, n_init="auto")
        labels: list[int] = model.fit_predict(X).tolist()

        clusters: dict[int, list[RetrievedDocument]] = {}
        for i, lab in enumerate(labels):
            clusters.setdefault(lab, []).append(results[i])

        return [group[0] for group in clusters.values()]
