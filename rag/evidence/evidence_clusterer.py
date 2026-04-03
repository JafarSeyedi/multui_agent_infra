import numpy as np
from sklearn.cluster import KMeans

class EvidenceClusterer:

    def __init__(self, embedding_model):
        self.embedding_model = embedding_model

    async def cluster(self, results, k=4):

        texts = [r.chunk.text for r in results]

        embeddings = await self.embedding_model.embed_batch(texts)

        X = np.array(embeddings)

        k = min(k, len(results))

        model = KMeans(n_clusters=k)
        labels = model.fit_predict(X)

        clusters = {}

        for i, lab in enumerate(labels):

            clusters.setdefault(lab, []).append(results[i])

        representatives = []

        for group in clusters.values():
            representatives.append(group[0])

        return representatives
