from abc import ABC, abstractmethod
from typing import List, Dict, Any
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


class VectorDBAdapter(ABC):

    @abstractmethod
    def upsert(self, vectors: List[List[float]], metadatas: List[Dict[str, Any]]) -> None:
        """Insert or update embeddings and metadata"""
        pass

    @abstractmethod
    def query(self, vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for most similar vectors"""
        pass


class InMemoryVectorStore(VectorDBAdapter):

    def __init__(self):
        self.vectors = []
        self.metadatas = []

    def upsert(self, vectors, metadatas):
        self.vectors.extend(vectors)
        self.metadatas.extend(metadatas)

    def query(self, vector, top_k=5):
        if not self.vectors:
            return []
        similarities = cosine_similarity([vector], self.vectors)[0]
        best_indices = np.argsort(similarities)[::-1][:top_k]
        return [self.metadatas[i] for i in best_indices]
