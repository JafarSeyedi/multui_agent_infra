import faiss
import numpy as np
from ..base import VectorDBAdapter


class FAISSAdapter(VectorDBAdapter):

    def __init__(self, dim):

        self.index = faiss.IndexFlatIP(dim)
        self.vectors = []
        self.metadata = []

    async def upsert(self, ids, vectors, metadata):

        arr = np.array(vectors).astype("float32")

        self.index.add(arr)

        self.metadata.extend(metadata)

    async def query(self, vector, top_k=5):

        vec = np.array([vector]).astype("float32")

        scores, ids = self.index.search(vec, top_k)

        results = []

        for i in ids[0]:
            results.append(self.metadata[i])

        return results
