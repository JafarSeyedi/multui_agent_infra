import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any
from ..base import VectorDBAdapter

class InMemoryVectorStore(VectorDBAdapter):
    """
    In-memory vector store for development and testing.
    Simulates basic upsert and query functionality.
    """

    def __init__(self):
        self._vectors = []
        self._metadatas = []
        self._ids = [] # We need to store IDs too for deletion and consistent upsert logic

    async def create_index(self, name: str, dimension: int, config: Optional[Dict] = None):
        """No-op for in-memory store, index is implicitly created."""
        print(f"InMemoryVectorStore: Index '{name}' with dimension {dimension} created (implicitly).")
        self._dimension = dimension # Store dimension for potential future checks

    async def upsert(self, ids: List[str], vectors: List[List[float]], metadata: List[Dict]):
        """
        Upserts vectors and metadata. Replaces existing entries if IDs match.
        Assumes vectors are already normalized if needed by the application.
        """
        if len(ids) != len(vectors) or len(ids) != len(metadata):
            raise ValueError("Length of ids, vectors, and metadata must match.")

        for i in range(len(ids)):
            item_id = ids[i]
            vector = vectors[i]
            meta = metadata[i]

            if item_id in self._ids:
                # Update existing
                idx = self._ids.index(item_id)
                self._vectors[idx] = vector
                self._metadatas[idx] = meta
            else:
                # Add new
                self._ids.append(item_id)
                self._vectors.append(vector)
                self._metadatas.append(meta)
        print(f"InMemoryVectorStore: Upserted {len(ids)} items. Total items: {len(self._ids)}")


    async def batch_upsert(self, items: List[Dict]):
        """
        Upserts items in batches. Each item should have 'id', 'vector', 'metadata'.
        """
        ids = [item['id'] for item in items]
        vectors = [item['vector'] for item in items]
        metadatas = [item['metadata'] for item in items]
        await self.upsert(ids, vectors, metadatas)


    async def query(self, vector: List[float], top_k: int = 5, filters: Optional[Dict] = None) -> List[Dict]:
        """
        Searches for most similar vectors using cosine similarity.
        Basic filtering can be implemented here if needed, but for simplicity, it's omitted.
        """
        if not self._vectors:
            return []

        if len(vector) != self._dimension:
             raise ValueError(f"Query vector dimension ({len(vector)}) does not match index dimension ({self._dimension}).")


        vectors_np = np.array(self._vectors).astype("float32")
        query_vector_np = np.array(vector).astype("float32")

        # Cosine similarity calculation
        similarities = cosine_similarity([query_vector_np], vectors_np)[0]

        # Get top K indices, handling cases where top_k > number of vectors
        num_items = len(self._vectors)
        actual_top_k = min(top_k, num_items)

        best_indices = np.argsort(similarities)[::-1][:actual_top_k]

        results = []
        for i in best_indices:
            # In a real scenario, you might include the score and ID
            # For simplicity, returning only metadata as requested by the base interface
            result_meta = self._metadatas[i].copy() # Return a copy
            result_meta["_id"] = self._ids[i]
            result_meta["_score"] = float(similarities[i]) # Include score
            results.append(result_meta)

        return results

    async def delete(self, ids: List[str]):
        """Deletes items by their IDs."""
        indices_to_delete = {self._ids.index(id) for id in ids if id in self._ids}
        
        if not indices_to_delete:
            print("InMemoryVectorStore: No matching IDs found for deletion.")
            return

        # Sort indices in descending order to avoid issues when deleting
        sorted_indices = sorted(list(indices_to_delete), reverse=True)

        for index in sorted_indices:
            del self._ids[index]
            del self._vectors[index]
            del self._metadatas[index]
        
        print(f"InMemoryVectorStore: Deleted {len(ids)} items. Total remaining: {len(self._ids)}")
