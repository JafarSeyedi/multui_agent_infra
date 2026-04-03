from qdrant_client import QdrantClient, models
from typing import List, Dict, Any, Optional
from ..base import VectorDBAdapter
from ..embedding_utils import normalize_embedding # Import normalization

class QdrantAdapter(VectorDBAdapter):
    """
    Adapter for Qdrant, a fast and scalable vector database.
    """

    def __init__(self, url: str = "http://localhost:6333", collection_name: str = "documents"):
        self.client = QdrantClient(url=url)
        self.collection_name = collection_name
        self._dimension = None

    async def create_index(self, name: str, dimension: int, config: Optional[Dict] = None):
        """Creates or recreates a Qdrant collection with specified configuration."""
        self.collection_name = name
        self._dimension = dimension
        
        # Default index configuration (HNSW)
        hnsw_config = models.HnswConfigDiff(
            m=config.get("m", 16) if config else 16,
            ef_construct=config.get("ef_construction", 200) if config else 200,
        ) if config else None

        vector_params = models.VectorParams(
            size=dimension,
            distance=models.Distance.COSINE # Default to cosine
        )

        self.client.recreate_collection(
            collection_name=self.collection_name,
            vectors_config=vector_params,
            hnsw_config=hnsw_config
            # Add other configs like quantizer, optimizers, etc. if needed
        )
        print(f"QdrantAdapter: Collection '{self.collection_name}' recreated with dimension {dimension}.")

    async def upsert(self, ids: List[str], vectors: List[List[float]], metadata: List[Dict]):
        """Upserts points (vectors and metadata) into the Qdrant collection."""
        if not ids: return
        if len(ids) != len(vectors) or len(ids) != len(metadata):
            raise ValueError("Length of ids, vectors, and metadata must match.")

        if self._dimension is None:
             raise RuntimeError("Collection dimension not set. Call create_index first.")
        
        # Normalize vectors before upserting
        normalized_vectors = [normalize_embedding(v) for v in vectors]

        # Convert metadata into Qdrant's payload format
        points = []
        for i in range(len(ids)):
            points.append(models.PointStruct(
                id=ids[i],
                vector=normalized_vectors[i],
                payload={**metadata[i]} # Qdrant expects payload as a dict
            ))

        # Use batching for efficiency
        self.client.upsert(
            collection_name=self.collection_name,
            wait=True, # Wait for operation to complete
            points=points
        )
        print(f"QdrantAdapter: Upserted {len(ids)} items into collection '{self.collection_name}'.")

    async def batch_upsert(self, items: List[Dict]):
        """
        Upserts items in batches. Each item should have 'id', 'vector', 'metadata'.
        """
        if not items: return
        ids = [item['id'] for item in items]
        vectors = [item['vector'] for item in items]
        metadatas = [item['metadata'] for item in items]
        await self.upsert(ids, vectors, metadatas)


    async def query(self, vector: List[float], top_k: int = 5, filters: Optional[Dict] = None) -> List[Dict]:
        """
        Queries Qdrant collection. 'filters' dictionary is translated to Qdrant's filter structure.
        """
        if self._dimension is None:
             raise RuntimeError("Collection dimension not set. Call create_index first.")

        # Normalize the query vector
        normalized_query_vector = normalize_embedding(vector)

        # Translate generic filters to Qdrant filter models
        qdrant_filter = None
        if filters:
            # Example: filters = {"source": "doc1", "score_gt": 0.8}
            # This requires mapping and constructing Qdrant's Filter object
            # For simplicity, let's assume filters are direct key-value matches for now.
            # More complex filters (range, exists, etc.) need explicit mapping.
            
            # Example for a simple key-value filter:
            filter_conditions = []
            for key, value in filters.items():
                if isinstance(value, (int, float, str, bool)):
                    filter_conditions.append(models.FieldCondition(
                        key=key,
                        match=models.MatchValue(value=value)
                    ))
                elif isinstance(value, dict) and "gt" in value: # Example for range filter
                    filter_conditions.append(models.FieldCondition(
                        key=key,
                        range=models.Range(gte=value["gt"]) # Assuming gt means greater than or equal
                    ))
            if filter_conditions:
                qdrant_filter = models.Filter(must=filter_conditions)


        try:
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=normalized_query_vector,
                limit=top_k,
                query_filter=qdrant_filter,
                with_payload=True # Include payload (metadata)
            )
        except Exception as e:
            print(f"QdrantAdapter: Error during query: {e}")
            return []

        formatted_results = []
        if search_result:
            for hit in search_result:
                formatted_results.append({
                    "_id": hit.id,
                    "_score": hit.score,
                    **hit.payload # Payload contains the metadata
                })
        return formatted_results

    async def delete(self, ids: List[str]):
        """Deletes points by their IDs from the Qdrant collection."""
        if not ids: return

        try:
            self.client.delete(
                collection_name=self.collection_name,
                wait=True,
                points_selector=models.PointSelector(
                    ids=ids
                )
            )
            print(f"QdrantAdapter: Deleted {len(ids)} items from collection '{self.collection_name}'.")
        except Exception as e:
            print(f"QdrantAdapter: Error deleting items: {e}")
