import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from ..base import VectorDBAdapter
from ..embedding_utils import normalize_embedding # Import normalization

class ChromaAdapter(VectorDBAdapter):
    """
    Adapter for ChromaDB, a lightweight, easy-to-use vector database.
    """

    def __init__(self, db_path: str = "./chroma_db", collection_name: str = "documents"):
        # ChromaDB can run in-memory, persistent, or client/server mode.
        # This uses persistent mode. Adjust 'db_path' for different locations.
        self.client = chromadb.PersistentClient(path=db_path, settings=Settings(allow_reset=True))
        self.collection_name = collection_name
        self._collection = None # Will be initialized on first use or explicitly created

    async def _get_or_create_collection(self, dimension: int):
        """Ensures the collection exists and has the correct dimension."""
        if self._collection is None:
            try:
                self._collection = self.client.get_collection(name=self.collection_name)
                # Optional: Check if dimension matches if collection already exists
                # For simplicity, assuming dimension is consistent or handled externally
            except: # Collection does not exist
                print(f"ChromaAdapter: Creating collection '{self.collection_name}' with dimension {dimension}")
                self._collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"} # Default to cosine, can be made configurable
                )
        return self._collection

    async def create_index(self, name: str, dimension: int, config: Optional[Dict] = None):
        """
        ChromaDB creates collections dynamically. This method ensures it exists
        and potentially sets collection-level configurations if Chroma supported it directly here.
        'name' here corresponds to the collection name.
        """
        # ChromaDB's create_collection is typically done once.
        # We ensure it exists via _get_or_create_collection.
        # Config can be used to specify distance metric, but it's often set at collection creation.
        await self._get_or_create_collection(dimension=dimension)
        print(f"ChromaAdapter: Ensured collection '{name}' exists with dimension {dimension}.")


    async def upsert(self, ids: List[str], vectors: List[List[float]], metadata: List[Dict]):
        """Upserts embeddings and metadata into the ChromaDB collection."""
        if not ids: return
        
        collection = await self._get_or_create_collection(dimension=len(vectors[0]))
        
        # ChromaDB expects metadata and documents (optional text content)
        # We'll put the provided metadata into Chroma's metadata field.
        # If your application uses text content, you might map it to 'documents' field.
        
        # Normalize vectors before upserting if needed by the application context
        normalized_vectors = [normalize_embedding(v) for v in vectors]

        collection.upsert(
            ids=ids,
            embeddings=normalized_vectors,
            metadatas=metadata
        )
        print(f"ChromaAdapter: Upserted {len(ids)} items into '{self.collection_name}'.")


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
        Queries the ChromaDB collection for similar vectors.
        'filters' can be used for metadata filtering.
        """
        if self._collection is None:
             raise RuntimeError("Collection not initialized. Call create_index or upsert first.")

        # Normalize query vector
        normalized_query_vector = normalize_embedding(vector)

        results = self._collection.query(
            query_embeddings=[normalized_query_vector],
            where=filters, # ChromaDB uses 'where' for metadata filtering
            n_results=top_k,
            include=['metadatas', 'distances'] # Include metadata and distance
        )

        # Chroma returns results in a nested structure
        formatted_results = []
        if results and results.get('ids') and results['ids'][0]:
            for i in range(len(results['ids'][0])):
                metadata = results['metadatas'][0][i] if results.get('metadatas') and results['metadatas'][0] else {}
                distance = results['distances'][0][i] if results.get('distances') and results['distances'][0] else None
                
                formatted_results.append({
                    "_id": results['ids'][0][i],
                    "_score": 1.0 - distance if distance is not None else None, # Convert distance to score (e.g., for cosine)
                    **metadata
                })
        return formatted_results

    async def delete(self, ids: List[str]):
        """Deletes items by their IDs from the collection."""
        if self._collection is None:
             print("ChromaAdapter: Cannot delete, collection not initialized.")
             return
        
        try:
            self._collection.delete(ids=ids)
            print(f"ChromaAdapter: Deleted {len(ids)} items from '{self.collection_name}'.")
        except Exception as e:
            print(f"ChromaAdapter: Error deleting items: {e}")
