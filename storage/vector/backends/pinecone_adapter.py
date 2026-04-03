import pinecone
from typing import List, Dict, Any, Optional
from ..base import VectorDBAdapter
from ..embedding_utils import normalize_embedding

class PineconeAdapter(VectorDBAdapter):
    """
    Adapter for Pinecone, a managed vector database service.
    Handles index initialization and operations like upsert, query, delete.
    """

    def __init__(self, api_key: str, environment: str, index_name: str = "documents", dimension: int = 1536, metric: str = "cosine"):
        self.api_key = api_key
        self.environment = environment
        self.index_name = index_name
        self._dimension = dimension
        self._metric = metric.lower()
        self._index = None
        self._initialize_connection()

    def _initialize_connection(self):
        """Initializes Pinecone connection and connects to the specified index."""
        try:
            pinecone.init(api_key=self.api_key, environment=self.environment)
            self._index = pinecone.Index(self.index_name)
            # Optional: Check index description to confirm dimension and metric
            # index_desc = self._index.describe_index_stats()
            # print(f"Pinecone connection established to index '{self.index_name}'. Index stats: {index_desc}")
            print(f"PineconeAdapter: Connected to index '{self.index_name}'.")
        except Exception as e:
            raise ConnectionError(f"Failed to initialize Pinecone connection or connect to index '{self.index_name}': {e}")

    async def create_index(self, name: str, dimension: int, config: Optional[Dict] = None):
        """
        Manages index creation in Pinecone. If index exists, it ensures configuration matches.
        'name' is the index name. 'config' can specify 'pod_type', 'replicas', etc.
        """
        self.index_name = name # Update internal index name if changed
        self._dimension = dimension
        if config and 'metric' in config:
            self._metric = config['metric'].lower()

        if self.index_name not in pinecone.list_indexes():
            print(f"PineconeAdapter: Index '{self.index_name}' does not exist. Creating...")
            create_args = {
                "name": self.index_name,
                "dimension": self._dimension,
                "metric": self._metric,
                "pod_type": config.get("pod_type", "p1.x1") if config else "p1.x1", # Default pod type
                "replicas": config.get("replicas", 1) if config else 1, # Default replicas
                # Add other Pinecone specific configurations as needed
            }
            pinecone.create_index(**create_args)
            print(f"PineconeAdapter: Index '{self.index_name}' created with dimension {self._dimension}, metric '{self._metric}'.")
        else:
            # Optional: Check if existing index configuration matches and update if necessary
            # index_description = pinecone.describe_index(self.index_name)
            # if index_description.dimension != self._dimension or index_description.metric != self._metric:
            #     print(f"PineconeAdapter: Index '{self.index_name}' configuration mismatch. Consider updating or recreating.")
            print(f"PineconeAdapter: Index '{self.index_name}' already exists.")
        
        # Re-establish connection to ensure it's using the potentially newly created index
        self._initialize_connection()

    async def upsert(self, ids: List[str], vectors: List[List[float]], metadata: List[Dict]):
        """Upserts embeddings and metadata into the Pinecone index."""
        if not ids: return
        if len(ids) != len(vectors) or len(ids) != len(metadata):
            raise ValueError("Length of ids, vectors, and metadata must match.")

        # Normalize vectors
        vectors_to_upsert = [normalize_embedding(v) for v in vectors]
        
        # Prepare data for Pinecone upsert: list of tuples (id, vector, metadata)
        upsert_data = list(zip(ids, vectors_to_upsert, metadata))
        
        # Pinecone's upsert has a payload limit. Batching is crucial for large datasets.
        # We'll implement batching here.
        batch_size = 100 # Pinecone's recommended batch size is often around 100
        for i in range(0, len(upsert_data), batch_size):
            batch = upsert_data[i:i + batch_size]
            try:
                self._index.upsert(vectors=batch)
            except Exception as e:
                print(f"PineconeAdapter: Error during batch upsert (batch {i//batch_size}): {e}")
                # Implement retry logic or error handling for failed batches
        print(f"PineconeAdapter: Upserted {len(ids)} items into index '{self.index_name}'.")

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
        Queries the Pinecone index. 'filters' dictionary maps to Pinecone's filter syntax.
        """
        if self._index is None:
             raise RuntimeError("Pinecone index not initialized.")

        # Normalize the query vector
        normalized_query_vector = normalize_embedding(vector)

        pinecone_filter = None
        if filters:
            # Pinecone's filter syntax uses operators like '$eq', '$gt', '$in', etc.
            # This requires mapping our generic filter keys/values to Pinecone's format.
            # Example: filters = {"source": "doc1"} -> {"source": {"$eq": "doc1"}}
            # Example: filters = {"score_gt": 0.8} -> {"score": {"$gt": 0.8}}
            
            # A simple implementation for common cases:
            pinecone_filter = {}
            for key, value in filters.items():
                if isinstance(value, dict): # Handle complex filters like range queries
                    for op, val in value.items():
                        pinecone_filter[key] = {f"${op}": val}
                else: # Handle simple equality filters
                    pinecone_filter[key] = {"$eq": value}
            
            # Pinecone filter structure needs to be nested correctly if multiple conditions
            # For simplicity, assuming top-level filters are ANDed implicitly by constructing the dict.
            # If more complex AND/OR logic is needed, Pinecone's Filter object is required.

        try:
            results = self._index.query(
                vector=normalized_query_vector,
                top_k=top_k,
                include_metadata=True,
                filter=pinecone_filter # Apply filters
            )
        except Exception as e:
            print(f"PineconeAdapter: Error during query: {e}")
            return []

        formatted_results = []
        if results and results.get('matches'):
            for match in results['matches']:
                metadata = match.get('metadata', {})
                formatted_results.append({
                    "_id": match.get('id'),
                    "_score": match.get('score'),
                    **metadata
                })
        return formatted_results

    async def delete(self, ids: List[str]):
        """Deletes items by their IDs from the Pinecone index."""
        if not ids: return

        try:
            # Pinecone delete accepts a list of IDs directly
            self._index.delete(ids=ids)
            print(f"PineconeAdapter: Deleted {len(ids)} items from index '{self.index_name}'.")
        except Exception as e:
            print(f"PineconeAdapter: Error deleting items: {e}")
            # Implement retry logic or error handling
