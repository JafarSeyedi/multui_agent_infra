import weaviate
import json
import asyncio # Import asyncio
from typing import List, Dict, Any, Optional
from ..base import VectorDBAdapter
from ..embedding_utils import normalize_embedding

class WeaviateAdapter(VectorDBAdapter):
    """
    Adapter for Weaviate, a vector database with graph capabilities.
    Supports asynchronous operations.
    """

    def __init__(self, url: str = "http://localhost:8080", api_key: Optional[str] = None, class_name: str = "Document", dim: int = 1536):
        auth_params = None
        if api_key:
            auth_params = weaviate.auth.AuthApiKey(api_key=api_key)
        
        # Use async client
        self.client = weaviate.Client(url=url, auth_client_params=auth_params)
        self.class_name = class_name
        self._dimension = dim # Store dimension, will be confirmed/set during schema creation
        self._collection = None # Placeholder for the Weaviate class object


    async def _get_or_create_class(self):
        """Ensures the Weaviate schema for the class exists and returns the class object."""
        if self._collection is None:
            # Check if class exists
            try:
                class_schema = self.client.schema.get_class(self.class_name)
                self._dimension = class_schema['vectorizer']['vectorIndexConfig']['dimension'] # Get dimension from schema
                print(f"WeaviateAdapter: Class '{self.class_name}' already exists with dimension {self._dimension}.")
                self._collection = self.client.get_class(self.class_name) # Fetch class object
            except Exception: # Class does not exist
                print(f"WeaviateAdapter: Creating class '{self.class_name}' with dimension {self._dimension}.")
                
                class_obj = {
                    "class": self.class_name,
                    "description": "A vector document store",
                    "vectorizer": "none", # Using 'none' as we provide vectors manually
                    "vectorIndexConfig": {
                        "distance": weaviate.Config.VectorDistance.COSINE, # Default to cosine
                        # Example HNSW config, can be passed via 'config' arg in create_index
                        # "efConstruction": 128,
                        # "maxConnections": 64,
                    },
                    "properties": [
                        {
                            "name": "metadata", # Store all metadata as a JSON string
                            "dataType": ["string"]
                        },
                        # Add other indexed properties here if needed, e.g., "source": {"dataType": ["text"]}
                    ],
                }
                self.client.schema.create_class(class_obj)
                self._collection = self.client.get_class(self.class_name) # Fetch the created class object
        return self._collection

    async def create_index(self, name: str, dimension: int, config: Optional[Dict] = None):
        """
        Ensures the Weaviate schema for the class exists. 'name' is class name.
        'config' can contain vectorIndexConfig parameters.
        """
        self.class_name = name
        self._dimension = dimension # Update dimension based on call
        await self._get_or_create_class()
        print(f"WeaviateAdapter: Ensured Weaviate schema for class '{name}' with dimension {dimension}.")

    async def upsert(self, ids: List[str], vectors: List[List[float]], metadata: List[Dict]):
        """Upserts embeddings and metadata into Weaviate using batching."""
        if not ids: return
        if len(ids) != len(vectors) or len(ids) != len(metadata):
            raise ValueError("Length of ids, vectors, and metadata must match.")

        await self._get_or_create_class() # Ensure schema exists

        # Normalize vectors
        normalized_vectors = [normalize_embedding(v) for v in vectors]

        # Weaviate batch operations are typically synchronous, but we can run them in an executor
        # or use client.batch for convenience. The client.batch context manager handles async internally well.
        with self.client.batch as batch:
            batch.batch_size = 100 # Adjust batch size as needed
            for i in range(len(ids)):
                metadata_json = json.dumps(metadata[i])
                
                data_object = {
                    "metadata": metadata_json,
                    # Add other indexed properties here if they exist in your schema
                }
                
                batch.add_data_object(
                    data_object=data_object,
                    class_name=self.class_name,
                    uuid=ids[i],
                    vector=normalized_vectors[i]
                )
        print(f"WeaviateAdapter: Upserted {len(ids)} items into class '{self.class_name}'.")

    async def batch_upsert(self, items: List[Dict]):
        """
        Upserts items in batches. Each item should have 'id', 'vector', 'metadata'.
        """
        if not items: return
        ids = [item['id'] for item in items]
        vectors = [item['vector'] for item in items]
        metadatas = [item['metadata'] for item in items]
        await self.upsert(ids, vectors, metadatas)

    async def query(self, vector: List[float], top_k: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[Dict]:
        """
        Queries Weaviate. Filters need translation to Weaviate's filter syntax.
        """
        if self._dimension is None:
             raise RuntimeError("Weaviate dimension not set. Ensure schema is initialized.")

        # Normalize the query vector
        normalized_query_vector = normalize_embedding(vector)

        # Construct the Weaviate query builder
        query_builder = (
            self.client.query
            .get(self.class_name, ["metadata"]) # Fetch the metadata property
            .with_near_vector({"vector": normalized_query_vector})
            .with_limit(top_k)
            .with_include_vector(True) # Optionally include the vector itself
        )

        # Translate generic filters to Weaviate's filter syntax
        if filters:
            # Example filter: filters = {"source": "doc1"}
            # Weaviate filter: {"path": ["metadata"], "operator": "ContainsAny", "valueText": ["source:doc1"]}
            # This requires parsing the JSON string in metadata, which is inefficient.
            # It's better to index specific fields directly in the schema.
            # Assuming direct indexed properties for filters:
            weaviate_filter = {"operator": "And", "operands": []}
            for key, value in filters.items():
                # This mapping is a simplification. Real implementation needs robust mapping.
                # If key is 'source', path is ['source']
                # If key is 'score_gt', path is ['score'], operator is 'GreaterThan'
                # For now, assume simple equality on potentially indexed fields.
                
                # Example: filter for source = 'doc1'
                # if key == "source":
                #     weaviate_filter["operands"].append({
                #         "path": ["source"], "operator": "Equal", "valueText": value
                #     })
                
                # If your schema maps metadata JSON to a specific property, e.g., 'source'
                # you would filter on that property directly.
                # Since we store metadata as a JSON string, direct filtering is hard.
                # For demonstration, we skip complex filtering on the JSON string metadata.
                print(f"WeaviateAdapter: Direct filtering on JSON metadata '{key}' is complex. Consider indexing fields.")
            
            # If we had direct indexed properties, we would apply the filter:
            # if weaviate_filter["operands"]:
            #    query_builder.with_where(weaviate_filter)

        try:
            # Weaviate client methods are often synchronous. For async, use asyncio.to_thread
            # Or use a dedicated async client if available and stable.
            # For now, assume synchronous call wrapped in asyncio.to_thread if needed.
            # The weaviate-python client has some async support, let's try that.
            
            # Check if client is async-compatible (recent versions are)
            if asyncio.iscoroutinefunction(self.client.query.get().do):
                 results = await query_builder.do()
            else: # Fallback for older clients or synchronous calls
                 results = await asyncio.to_thread(query_builder.do)

        except Exception as e:
            print(f"WeaviateAdapter: Error during query: {e}")
            return []

        formatted_results = []
        if results and 'data' in results and 'Get' in results['data'] and self.class_name in results['data']['Get']:
            for item in results['data']['Get'][self.class_name]:
                metadata = json.loads(item.get("metadata", "{}")) # Parse JSON string
                additional_info = item.get('_additional', {})
                score = additional_info.get('distance') # Distance (lower is better for cosine)
                vec_id = additional_info.get('id') # Weaviate ID

                formatted_results.append({
                    "_id": vec_id,
                    "_score": 1.0 - score if score is not None else None, # Convert distance to similarity score
                    **metadata
                })
        return formatted_results

    async def delete(self, ids: List[str]):
        """Deletes items by their IDs from Weaviate."""
        if not ids: return
        
        # Weaviate's delete operation requires IDs in a specific format.
        # Using the batch delete API is more robust for multiple IDs.
        try:
            # Convert IDs to UUID objects if needed, though client might handle strings.
            uuids_to_delete = [str(id) for id in ids] # Ensure they are strings

            # Weaviate batch delete:
            with self.client.batch as batch:
                 for item_id in uuids_to_delete:
                      batch.delete_data_object(uuid=item_id, class_name=self.class_name)
            print(f"WeaviateAdapter: Initiated deletion of {len(ids)} items from class '{self.class_name}'.")
            # Note: Batch operations might execute asynchronously. Ensure proper handling.
        except Exception as e:
            print(f"WeaviateAdapter: Error initiating deletion: {e}")
