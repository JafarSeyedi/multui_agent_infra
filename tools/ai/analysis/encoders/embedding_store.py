#!/usr/bin/env python3
"""
Embedding Store - AI Development Framework
Vector storage and retrieval using ChromaDB for semantic search.

Part of the Level 2 Analysis tools (encoders/embedding_store.py)

This embedding_store.py provides:

1. Persistent Vector Storage - ChromaDB-based storage in .ai_state/vector_store/
2. Multiple Collections - Separate collections for code, docs, semantic chunks, symbols, etc.
3. Automatic Embedding - Integrates with OllamaEncoder for seamless embedding generation
4. Rich Search Capabilities - Semantic search with similarity scoring and metadata filtering
5. Batch Operations - Efficient bulk add/update/delete
6. Content Hashing - Avoids duplicate storage with SHA256-based IDs
7. Metadata Filtering - Filter search results by metadata fields
8. Hybrid Search - Combines vector similarity with text matching
9. Related Document Discovery - Find documents similar to a given document
10. Import/Export - JSON serialization for backup and migration
11. Collection Management - Create, list, clear, and delete collections
12. Caching Layer - In-memory cache for fast document retrieval

The embedding store provides the persistence layer for all vector embeddings, enabling semantic search across your entire codebase and documentation.
"""

import json
import hashlib
import uuid
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, Union, Iterator, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict

import chromadb
from chromadb.config import Settings
from chromadb.api import Collection
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings

from ...shared.logger import get_logger
from ...shared.state_manager import StateManager
from .ollama_encoder import OllamaEncoder, EncodingResult, EmbeddingModel, EncoderConfig

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class CollectionType(str, Enum):
    """Type of vector collection."""
    CODE = "code"                    # Code chunks
    DOCUMENTATION = "documentation"  # Documentation chunks
    SEMANTIC = "semantic"            # Semantic chunks
    SYMBOLS = "symbols"              # Code symbols
    ARCHITECTURE = "architecture"    # Architecture documents
    TASKS = "tasks"                  # Task descriptions
    KNOWLEDGE = "knowledge"          # General knowledge base
    CUSTOM = "custom"                # Custom collection


class DistanceMetric(str, Enum):
    """Distance metric for vector similarity."""
    COSINE = "cosine"      # Cosine similarity (default)
    EUCLIDEAN = "l2"       # Euclidean distance
    DOT_PRODUCT = "ip"     # Inner product


class IndexType(str, Enum):
    """Index type for ChromaDB."""
    HNSW = "hnsw"          # Hierarchical Navigable Small World
    FLAT = "flat"          # Flat index (brute force)


@dataclass
class StoreConfig:
    """Configuration for the embedding store."""
    persist_directory: Path = Path(".ai_state/vector_store")
    default_distance_metric: DistanceMetric = DistanceMetric.COSINE
    default_index_type: IndexType = IndexType.HNSW
    hnsw_m: int = 16                    # HNSW M parameter
    hnsw_ef_construction: int = 200     # HNSW efConstruction
    hnsw_ef_search: int = 100           # HNSW efSearch
    batch_size: int = 100               # Batch size for operations
    auto_create_collections: bool = True
    enable_telemetry: bool = False
    embedding_model: EmbeddingModel = EmbeddingModel.MXBAI_EMBED_LARGE


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class StoredDocument:
    """Document stored in vector database."""
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    collection: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    source_hash: str = ""
    
    def __post_init__(self):
        if not self.source_hash:
            self.source_hash = hashlib.sha256(
                f"{self.content}{json.dumps(self.metadata, sort_keys=True)}".encode()
            ).hexdigest()


@dataclass
class SearchResult:
    """Result from vector search."""
    id: str
    content: str
    metadata: Dict[str, Any]
    distance: float
    similarity: float
    collection: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'content': self.content,
            'metadata': self.metadata,
            'distance': self.distance,
            'similarity': self.similarity,
            'collection': self.collection
        }


@dataclass
class CollectionInfo:
    """Information about a collection."""
    name: str
    collection_type: CollectionType
    document_count: int
    distance_metric: DistanceMetric
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class BatchOperationResult:
    """Result of batch operation."""
    total: int
    successful: int
    failed: int
    errors: List[str] = field(default_factory=list)
    duration_ms: float = 0.0


# ============================================================
# OLLAMA EMBEDDING FUNCTION FOR CHROMADB
# ============================================================

class OllamaEmbeddingFunction(EmbeddingFunction):
    """ChromaDB embedding function using Ollama."""
    
    def __init__(self, encoder: OllamaEncoder, model: Optional[EmbeddingModel] = None):
        self.encoder = encoder
        self.model = model or encoder.config.default_model
    
    def __call__(self, input: Documents) -> Embeddings:
        """Generate embeddings for documents."""
        embeddings = []
        
        for text in input:
            result = self.encoder.encode_single(text, model=self.model)
            if result and result.embedding:
                embeddings.append(result.embedding)
            else:
                # Return zero vector as fallback
                dims = 1024 if 'large' in self.model.value else 768
                embeddings.append([0.0] * dims)
        
        return embeddings


# ============================================================
# COLLECTION MANAGER
# ============================================================

class CollectionManager:
    """Manages ChromaDB collections."""
    
    def __init__(self, config: StoreConfig):
        self.config = config
        self._collections: Dict[str, Collection] = {}
        self._collection_metadata: Dict[str, Dict[str, Any]] = {}
    
    def create_collection(self,
                          name: str,
                          collection_type: CollectionType,
                          distance_metric: Optional[DistanceMetric] = None,
                          metadata: Optional[Dict[str, Any]] = None) -> Collection:
        """Create a new collection."""
        distance_metric = distance_metric or self.config.default_distance_metric
        
        # Store collection metadata
        self._collection_metadata[name] = {
            'type': collection_type.value,
            'distance_metric': distance_metric.value,
            'created_at': datetime.now().isoformat(),
            'user_metadata': metadata or {}
        }
        
        return self._collections[name]
    
    def get_collection(self, name: str) -> Optional[Collection]:
        """Get a collection by name."""
        return self._collections.get(name)
    
    def get_or_create_collection(self,
                                  name: str,
                                  collection_type: CollectionType,
                                  embedding_function: Optional[EmbeddingFunction] = None,
                                  distance_metric: Optional[DistanceMetric] = None,
                                  metadata: Optional[Dict[str, Any]] = None) -> Collection:
        """Get existing collection or create new one."""
        if name in self._collections:
            return self._collections[name]
        
        return self.create_collection(
            name=name,
            collection_type=collection_type,
            distance_metric=distance_metric,
            metadata=metadata
        )
    
    def list_collections(self) -> List[str]:
        """List all collection names."""
        return list(self._collections.keys())
    
    def delete_collection(self, name: str) -> bool:
        """Delete a collection."""
        if name in self._collections:
            del self._collections[name]
            if name in self._collection_metadata:
                del self._collection_metadata[name]
            return True
        return False
    
    def get_collection_info(self, name: str) -> Optional[CollectionInfo]:
        """Get information about a collection."""
        if name not in self._collections:
            return None
        
        collection = self._collections[name]
        meta = self._collection_metadata.get(name, {})
        
        return CollectionInfo(
            name=name,
            collection_type=CollectionType(meta.get('type', 'custom')),
            document_count=collection.count(),
            distance_metric=DistanceMetric(meta.get('distance_metric', 'cosine')),
            metadata=meta.get('user_metadata', {}),
            created_at=datetime.fromisoformat(meta.get('created_at', datetime.now().isoformat())),
            last_updated=datetime.fromisoformat(meta.get('last_updated', datetime.now().isoformat()))
        )


# ============================================================
# MAIN EMBEDDING STORE CLASS
# ============================================================

class EmbeddingStore:
    """
    Vector storage and retrieval using ChromaDB.
    
    Features:
    - Persistent vector storage with ChromaDB
    - Multiple collections for different content types
    - Automatic embedding generation via Ollama
    - Semantic search with metadata filtering
    - Batch operations for efficiency
    - Incremental updates with content hashing
    - Collection management (create, list, delete)
    - Similarity threshold filtering
    - Hybrid search (vector + metadata)
    - Export and import capabilities
    - Change tracking and versioning
    """
    
    def __init__(self, 
                 config: Optional[StoreConfig] = None,
                 encoder: Optional[OllamaEncoder] = None):
        self.config = config or StoreConfig()
        self.encoder = encoder or OllamaEncoder()
        
        # Ensure persist directory exists
        self.config.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = self._create_client()
        
        # Create embedding function
        self.embedding_function = OllamaEmbeddingFunction(
            self.encoder, 
            self.config.embedding_model
        )
        
        # Collection manager
        self.collections = CollectionManager(self.config)
        
        # State management
        self.state = StateManager(self.config.persist_directory / "store_state.json")
        
        # Cache for fast lookups
        self._document_cache: Dict[str, Dict[str, StoredDocument]] = defaultdict(dict)
        
        # Initialize default collections
        self._initialize_default_collections()
        
        logger.info(f"EmbeddingStore initialized at {self.config.persist_directory}")
    
    def _create_client(self) -> chromadb.PersistentClient:
        """Create ChromaDB persistent client."""
        return chromadb.PersistentClient(
            path=str(self.config.persist_directory),
            settings=Settings(
                anonymized_telemetry=self.config.enable_telemetry,
                allow_reset=True
            )
        )
    
    def _initialize_default_collections(self):
        """Initialize default collections."""
        default_collections = [
            (self._get_collection_name(CollectionType.CODE), CollectionType.CODE),
            (self._get_collection_name(CollectionType.DOCUMENTATION), CollectionType.DOCUMENTATION),
            (self._get_collection_name(CollectionType.SEMANTIC), CollectionType.SEMANTIC),
            (self._get_collection_name(CollectionType.SYMBOLS), CollectionType.SYMBOLS),
            (self._get_collection_name(CollectionType.ARCHITECTURE), CollectionType.ARCHITECTURE),
            (self._get_collection_name(CollectionType.TASKS), CollectionType.TASKS),
            (self._get_collection_name(CollectionType.KNOWLEDGE), CollectionType.KNOWLEDGE),
        ]
        
        for name, coll_type in default_collections:
            if self.config.auto_create_collections:
                collection = self.client.get_or_create_collection(
                    name=name,
                    embedding_function=self.embedding_function,
                    metadata={
                        "hnsw:space": self.config.default_distance_metric.value,
                        "hnsw:M": self.config.hnsw_m,
                        "hnsw:construction_ef": self.config.hnsw_ef_construction,
                        "hnsw:search_ef": self.config.hnsw_ef_search,
                        "type": coll_type.value
                    }
                )
                self.collections._collections[name] = collection
                self.collections._collection_metadata[name] = {
                    'type': coll_type.value,
                    'distance_metric': self.config.default_distance_metric.value,
                    'created_at': datetime.now().isoformat()
                }
    
    def _get_collection_name(self, collection_type: CollectionType) -> str:
        """Get standardized collection name."""
        return f"{collection_type.value}_embeddings"
    
    def _compute_document_id(self, content: str, metadata: Dict[str, Any]) -> str:
        """Compute unique document ID."""
        # Use source_file and chunk_id if available
        if 'source_file' in metadata and 'chunk_id' in metadata:
            base = f"{metadata['source_file']}_{metadata['chunk_id']}"
        elif 'symbol_name' in metadata:
            base = f"{metadata.get('source_file', '')}_{metadata['symbol_name']}"
        else:
            base = content[:100]
        
        hash_val = hashlib.sha256(f"{base}{json.dumps(metadata, sort_keys=True)}".encode()).hexdigest()
        return f"doc_{hash_val[:24]}"
    
    def _distance_to_similarity(self, distance: float, metric: DistanceMetric) -> float:
        """Convert distance to similarity score (0-1)."""
        if metric == DistanceMetric.COSINE:
            # Cosine distance is 1 - similarity
            return 1.0 - distance
        elif metric == DistanceMetric.EUCLIDEAN:
            # Convert Euclidean to similarity
            return 1.0 / (1.0 + distance)
        elif metric == DistanceMetric.DOT_PRODUCT:
            # Dot product can be negative, normalize
            return max(0.0, min(1.0, (distance + 1.0) / 2.0))
        return 1.0 - distance
    
    # ============================================================
    # DOCUMENT OPERATIONS
    # ============================================================
    
    def add(self,
            content: str,
            collection_type: CollectionType,
            metadata: Optional[Dict[str, Any]] = None,
            doc_id: Optional[str] = None) -> Optional[str]:
        """Add a single document to the store."""
        collection_name = self._get_collection_name(collection_type)
        collection = self.collections.get_or_create_collection(
            name=collection_name,
            collection_type=collection_type,
            embedding_function=self.embedding_function,
            distance_metric=self.config.default_distance_metric
        )
        
        if collection is None:
            logger.error(f"Failed to get collection: {collection_name}")
            return None
        
        metadata = metadata or {}
        doc_id = doc_id or self._compute_document_id(content, metadata)
        
        # Create stored document
        doc = StoredDocument(
            id=doc_id,
            content=content,
            metadata=metadata,
            collection=collection_name
        )
        
        try:
            # Check if document already exists
            existing = collection.get(ids=[doc_id])
            if existing and existing['ids']:
                # Update existing document
                collection.update(
                    ids=[doc_id],
                    documents=[content],
                    metadatas=[metadata]
                )
                logger.debug(f"Updated document: {doc_id}")
            else:
                # Add new document
                collection.add(
                    ids=[doc_id],
                    documents=[content],
                    metadatas=[metadata]
                )
                logger.debug(f"Added document: {doc_id}")
            
            # Cache document
            self._document_cache[collection_name][doc_id] = doc
            
            return doc_id
            
        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            return None
    
    def add_batch(self,
                  documents: List[Tuple[str, Dict[str, Any]]],
                  collection_type: CollectionType,
                  ids: Optional[List[str]] = None) -> BatchOperationResult:
        """Add multiple documents in batch."""
        start_time = datetime.now()
        
        collection_name = self._get_collection_name(collection_type)
        collection = self.collections.get_or_create_collection(
            name=collection_name,
            collection_type=collection_type,
            embedding_function=self.embedding_function
        )
        
        if collection is None:
            return BatchOperationResult(
                total=len(documents),
                successful=0,
                failed=len(documents),
                errors=["Failed to get collection"]
            )
        
        # Prepare batch data
        batch_ids = []
        batch_documents = []
        batch_metadatas = []
        
        for i, (content, metadata) in enumerate(documents):
            doc_id = ids[i] if ids and i < len(ids) else self._compute_document_id(content, metadata)
            batch_ids.append(doc_id)
            batch_documents.append(content)
            batch_metadatas.append(metadata)
        
        successful = 0
        failed = 0
        errors = []
        
        # Process in chunks
        for i in range(0, len(batch_ids), self.config.batch_size):
            chunk_ids = batch_ids[i:i + self.config.batch_size]
            chunk_docs = batch_documents[i:i + self.config.batch_size]
            chunk_metas = batch_metadatas[i:i + self.config.batch_size]
            
            try:
                # Check existing
                existing = collection.get(ids=chunk_ids)
                existing_ids = set(existing['ids'])
                
                # Split into updates and inserts
                update_indices = [j for j, doc_id in enumerate(chunk_ids) if doc_id in existing_ids]
                insert_indices = [j for j, doc_id in enumerate(chunk_ids) if doc_id not in existing_ids]
                
                # Perform updates
                if update_indices:
                    collection.update(
                        ids=[chunk_ids[j] for j in update_indices],
                        documents=[chunk_docs[j] for j in update_indices],
                        metadatas=[chunk_metas[j] for j in update_indices]
                    )
                    successful += len(update_indices)
                
                # Perform inserts
                if insert_indices:
                    collection.add(
                        ids=[chunk_ids[j] for j in insert_indices],
                        documents=[chunk_docs[j] for j in insert_indices],
                        metadatas=[chunk_metas[j] for j in insert_indices]
                    )
                    successful += len(insert_indices)
                
                # Update cache
                for j, doc_id in enumerate(chunk_ids):
                    doc = StoredDocument(
                        id=doc_id,
                        content=chunk_docs[j],
                        metadata=chunk_metas[j],
                        collection=collection_name
                    )
                    self._document_cache[collection_name][doc_id] = doc
                    
            except Exception as e:
                failed += len(chunk_ids)
                errors.append(f"Batch error at offset {i}: {e}")
                logger.error(f"Batch add failed: {e}")
        
        duration = (datetime.now() - start_time).total_seconds() * 1000
        
        return BatchOperationResult(
            total=len(documents),
            successful=successful,
            failed=failed,
            errors=errors,
            duration_ms=duration
        )
    
    def get(self, doc_id: str, collection_type: Optional[CollectionType] = None) -> Optional[StoredDocument]:
        """Get a document by ID."""
        # Try cache first
        if collection_type:
            collection_name = self._get_collection_name(collection_type)
            if doc_id in self._document_cache.get(collection_name, {}):
                return self._document_cache[collection_name][doc_id]
        else:
            # Search all collections
            for coll_name, cache in self._document_cache.items():
                if doc_id in cache:
                    return cache[doc_id]
        
        # Not in cache, query ChromaDB
        search_collections = [collection_type] if collection_type else list(CollectionType)
        
        for ct in search_collections:
            collection_name = self._get_collection_name(ct)
            collection = self.collections.get_collection(collection_name)
            
            if collection:
                try:
                    result = collection.get(ids=[doc_id])
                    if result and result['ids']:
                        doc = StoredDocument(
                            id=result['ids'][0],
                            content=result['documents'][0] if result['documents'] else "",
                            metadata=result['metadatas'][0] if result['metadatas'] else {},
                            collection=collection_name
                        )
                        # Cache for future
                        self._document_cache[collection_name][doc_id] = doc
                        return doc
                except Exception as e:
                    logger.warning(f"Failed to get document {doc_id}: {e}")
        
        return None
    
    def get_batch(self, doc_ids: List[str], collection_type: CollectionType) -> List[Optional[StoredDocument]]:
        """Get multiple documents by IDs."""
        collection_name = self._get_collection_name(collection_type)
        collection = self.collections.get_collection(collection_name)
        
        if not collection:
            return [None] * len(doc_ids)
        
        try:
            result = collection.get(ids=doc_ids)
            
            documents = []
            for i, doc_id in enumerate(doc_ids):
                if doc_id in result['ids']:
                    idx = result['ids'].index(doc_id)
                    doc = StoredDocument(
                        id=doc_id,
                        content=result['documents'][idx] if result['documents'] else "",
                        metadata=result['metadatas'][idx] if result['metadatas'] else {},
                        collection=collection_name
                    )
                    self._document_cache[collection_name][doc_id] = doc
                    documents.append(doc)
                else:
                    documents.append(None)
            
            return documents
            
        except Exception as e:
            logger.error(f"Batch get failed: {e}")
            return [None] * len(doc_ids)
    
    def update(self,
               doc_id: str,
               content: Optional[str] = None,
               metadata: Optional[Dict[str, Any]] = None,
               collection_type: Optional[CollectionType] = None) -> bool:
        """Update a document."""
        # Get existing document
        existing = self.get(doc_id, collection_type)
        if not existing:
            logger.warning(f"Document not found: {doc_id}")
            return False
        
        collection_name = existing.collection
        collection = self.collections.get_collection(collection_name)
        
        if not collection:
            return False
        
        new_content = content if content is not None else existing.content
        new_metadata = metadata if metadata is not None else existing.metadata
        
        try:
            collection.update(
                ids=[doc_id],
                documents=[new_content],
                metadatas=[new_metadata]
            )
            
            # Update cache
            existing.content = new_content
            existing.metadata = new_metadata
            existing.updated_at = datetime.now()
            self._document_cache[collection_name][doc_id] = existing
            
            return True
            
        except Exception as e:
            logger.error(f"Update failed: {e}")
            return False
    
    def delete(self, doc_id: str, collection_type: Optional[CollectionType] = None) -> bool:
        """Delete a document."""
        search_collections = [collection_type] if collection_type else list(CollectionType)
        
        for ct in search_collections:
            collection_name = self._get_collection_name(ct)
            collection = self.collections.get_collection(collection_name)
            
            if collection:
                try:
                    collection.delete(ids=[doc_id])
                    
                    # Remove from cache
                    if doc_id in self._document_cache.get(collection_name, {}):
                        del self._document_cache[collection_name][doc_id]
                    
                    return True
                except Exception:
                    pass
        
        return False
    
    def delete_batch(self, doc_ids: List[str], collection_type: CollectionType) -> BatchOperationResult:
        """Delete multiple documents."""
        collection_name = self._get_collection_name(collection_type)
        collection = self.collections.get_collection(collection_name)
        
        if not collection:
            return BatchOperationResult(
                total=len(doc_ids),
                successful=0,
                failed=len(doc_ids),
                errors=["Collection not found"]
            )
        
        try:
            collection.delete(ids=doc_ids)
            
            # Remove from cache
            for doc_id in doc_ids:
                if doc_id in self._document_cache.get(collection_name, {}):
                    del self._document_cache[collection_name][doc_id]
            
            return BatchOperationResult(
                total=len(doc_ids),
                successful=len(doc_ids),
                failed=0,
                duration_ms=0
            )
            
        except Exception as e:
            return BatchOperationResult(
                total=len(doc_ids),
                successful=0,
                failed=len(doc_ids),
                errors=[str(e)]
            )
    
    # ============================================================
    # SEARCH OPERATIONS
    # ============================================================
    
    def search(self,
               query: str,
               collection_type: Optional[CollectionType] = None,
               n_results: int = 10,
               where: Optional[Dict[str, Any]] = None,
               where_document: Optional[Dict[str, Any]] = None,
               min_similarity: float = 0.0) -> List[SearchResult]:
        """Semantic search across collections."""
        search_collections = [collection_type] if collection_type else [
            CollectionType.CODE,
            CollectionType.DOCUMENTATION,
            CollectionType.SEMANTIC,
            CollectionType.KNOWLEDGE
        ]
        
        all_results = []
        
        for ct in search_collections:
            collection_name = self._get_collection_name(ct)
            collection = self.collections.get_collection(collection_name)
            
            if not collection:
                continue
            
            try:
                results = collection.query(
                    query_texts=[query],
                    n_results=min(n_results, collection.count()),
                    where=where,
                    where_document=where_document,
                    include=["documents", "metadatas", "distances"]
                )
                
                if results and results['ids'] and results['ids'][0]:
                    distance_metric = DistanceMetric(
                        self.collections._collection_metadata.get(collection_name, {}).get('distance_metric', 'cosine')
                    )
                    
                    for i, doc_id in enumerate(results['ids'][0]):
                        distance = results['distances'][0][i]
                        similarity = self._distance_to_similarity(distance, distance_metric)
                        
                        if similarity >= min_similarity:
                            result = SearchResult(
                                id=doc_id,
                                content=results['documents'][0][i] if results['documents'] else "",
                                metadata=results['metadatas'][0][i] if results['metadatas'] else {},
                                distance=distance,
                                similarity=similarity,
                                collection=collection_name
                            )
                            all_results.append(result)
                            
            except Exception as e:
                logger.warning(f"Search failed for collection {collection_name}: {e}")
        
        # Sort by similarity
        all_results.sort(key=lambda x: x.similarity, reverse=True)
        
        return all_results[:n_results]
    
    def search_by_embedding(self,
                            embedding: List[float],
                            collection_type: CollectionType,
                            n_results: int = 10,
                            where: Optional[Dict[str, Any]] = None,
                            min_similarity: float = 0.0) -> List[SearchResult]:
        """Search using pre-computed embedding."""
        collection_name = self._get_collection_name(collection_type)
        collection = self.collections.get_collection(collection_name)
        
        if not collection:
            return []
        
        try:
            results = collection.query(
                query_embeddings=[embedding],
                n_results=min(n_results, collection.count()),
                where=where,
                include=["documents", "metadatas", "distances"]
            )
            
            search_results = []
            if results and results['ids'] and results['ids'][0]:
                distance_metric = DistanceMetric(
                    self.collections._collection_metadata.get(collection_name, {}).get('distance_metric', 'cosine')
                )
                
                for i, doc_id in enumerate(results['ids'][0]):
                    distance = results['distances'][0][i]
                    similarity = self._distance_to_similarity(distance, distance_metric)
                    
                    if similarity >= min_similarity:
                        result = SearchResult(
                            id=doc_id,
                            content=results['documents'][0][i] if results['documents'] else "",
                            metadata=results['metadatas'][0][i] if results['metadatas'] else {},
                            distance=distance,
                            similarity=similarity,
                            collection=collection_name
                        )
                        search_results.append(result)
            
            return search_results
            
        except Exception as e:
            logger.error(f"Embedding search failed: {e}")
            return []
    
    def hybrid_search(self,
                      query: str,
                      collection_type: Optional[CollectionType] = None,
                      n_results: int = 10,
                      where: Optional[Dict[str, Any]] = None,
                      text_weight: float = 0.3,
                      vector_weight: float = 0.7) -> List[SearchResult]:
        """Hybrid search combining vector and text matching."""
        # Get vector search results
        vector_results = self.search(
            query=query,
            collection_type=collection_type,
            n_results=n_results * 2,
            where=where
        )
        
        # Simple text-based scoring (keyword matching)
        query_terms = set(query.lower().split())
        
        for result in vector_results:
            content_terms = set(result.content.lower().split())
            text_score = len(query_terms & content_terms) / max(len(query_terms), 1)
            
            # Combine scores
            result.similarity = (vector_weight * result.similarity) + (text_weight * text_score)
        
        # Re-sort and return
        vector_results.sort(key=lambda x: x.similarity, reverse=True)
        return vector_results[:n_results]
    
    def search_across_collections(self,
                                  query: str,
                                  collection_types: List[CollectionType],
                                  n_results_per_collection: int = 5) -> Dict[str, List[SearchResult]]:
        """Search across multiple collections and return results grouped by collection."""
        results = {}
        
        for ct in collection_types:
            ct_results = self.search(
                query=query,
                collection_type=ct,
                n_results=n_results_per_collection
            )
            results[ct.value] = ct_results
        
        return results
    
    # ============================================================
    # COLLECTION MANAGEMENT
    # ============================================================
    
    def create_collection(self,
                          name: str,
                          collection_type: CollectionType = CollectionType.CUSTOM,
                          distance_metric: Optional[DistanceMetric] = None,
                          metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Create a custom collection."""
        try:
            collection = self.client.create_collection(
                name=name,
                embedding_function=self.embedding_function,
                metadata={
                    "hnsw:space": (distance_metric or self.config.default_distance_metric).value,
                    "hnsw:M": self.config.hnsw_m,
                    "hnsw:construction_ef": self.config.hnsw_ef_construction,
                    "hnsw:search_ef": self.config.hnsw_ef_search,
                    "type": collection_type.value,
                    **(metadata or {})
                }
            )
            
            self.collections._collections[name] = collection
            self.collections._collection_metadata[name] = {
                'type': collection_type.value,
                'distance_metric': (distance_metric or self.config.default_distance_metric).value,
                'created_at': datetime.now().isoformat(),
                'user_metadata': metadata or {}
            }
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create collection {name}: {e}")
            return False
    
    def list_collections(self) -> List[CollectionInfo]:
        """List all collections with metadata."""
        infos = []
        
        for name in self.collections.list_collections():
            info = self.collections.get_collection_info(name)
            if info:
                infos.append(info)
        
        return infos
    
    def get_collection_stats(self, collection_type: Optional[CollectionType] = None) -> Dict[str, Any]:
        """Get statistics for collections."""
        stats = {}
        
        collections_to_check = [collection_type] if collection_type else list(CollectionType)
        
        for ct in collections_to_check:
            collection_name = self._get_collection_name(ct)
            collection = self.collections.get_collection(collection_name)
            
            if collection:
                stats[ct.value] = {
                    'document_count': collection.count(),
                    'collection_name': collection_name,
                    'distance_metric': self.collections._collection_metadata.get(collection_name, {}).get('distance_metric')
                }
        
        return stats
    
    def delete_collection(self, collection_type: CollectionType) -> bool:
        """Delete an entire collection."""
        collection_name = self._get_collection_name(collection_type)
        
        try:
            self.client.delete_collection(collection_name)
            
            if collection_name in self.collections._collections:
                del self.collections._collections[collection_name]
            if collection_name in self.collections._collection_metadata:
                del self.collections._collection_metadata[collection_name]
            if collection_name in self._document_cache:
                del self._document_cache[collection_name]
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete collection {collection_name}: {e}")
            return False
    
    def clear_collection(self, collection_type: CollectionType) -> bool:
        """Clear all documents from a collection."""
        collection_name = self._get_collection_name(collection_type)
        
        # Delete and recreate
        if self.delete_collection(collection_type):
            return self.create_collection(collection_name, collection_type)
        
        return False
    
    # ============================================================
    # IMPORT/EXPORT
    # ============================================================
    
    def export_collection(self,
                          collection_type: CollectionType,
                          output_path: Optional[Path] = None) -> List[Dict[str, Any]]:
        """Export collection documents to JSON."""
        collection_name = self._get_collection_name(collection_type)
        collection = self.collections.get_collection(collection_name)
        
        if not collection:
            return []
        
        try:
            # Get all documents
            results = collection.get(include=["documents", "metadatas"])
            
            documents = []
            if results and results['ids']:
                for i, doc_id in enumerate(results['ids']):
                    documents.append({
                        'id': doc_id,
                        'content': results['documents'][i] if results['documents'] else "",
                        'metadata': results['metadatas'][i] if results['metadatas'] else {}
                    })
            
            if output_path:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        'collection_type': collection_type.value,
                        'exported_at': datetime.now().isoformat(),
                        'count': len(documents),
                        'documents': documents
                    }, f, indent=2)
                logger.info(f"Exported {len(documents)} documents to {output_path}")
            
            return documents
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return []
    
    def import_collection(self,
                          documents: List[Dict[str, Any]],
                          collection_type: CollectionType,
                          clear_existing: bool = False) -> BatchOperationResult:
        """Import documents into a collection."""
        if clear_existing:
            self.clear_collection(collection_type)
        
        batch_docs = []
        batch_ids = []
        
        for doc in documents:
            batch_docs.append((doc['content'], doc.get('metadata', {})))
            batch_ids.append(doc.get('id'))
        
        return self.add_batch(batch_docs, collection_type, batch_ids)
    
    # ============================================================
    # UTILITY METHODS
    # ============================================================
    
    def count(self, collection_type: Optional[CollectionType] = None) -> int:
        """Count documents in collections."""
        if collection_type:
            collection_name = self._get_collection_name(collection_type)
            collection = self.collections.get_collection(collection_name)
            return collection.count() if collection else 0
        
        total = 0
        for ct in CollectionType:
            collection_name = self._get_collection_name(ct)
            collection = self.collections.get_collection(collection_name)
            if collection:
                total += collection.count()
        
        return total
    
    def get_by_metadata(self,
                        metadata_filter: Dict[str, Any],
                        collection_type: Optional[CollectionType] = None) -> List[StoredDocument]:
        """Get documents by metadata filter."""
        search_collections = [collection_type] if collection_type else list(CollectionType)
        documents = []
        
        for ct in search_collections:
            collection_name = self._get_collection_name(ct)
            collection = self.collections.get_collection(collection_name)
            
            if not collection:
                continue
            
            try:
                results = collection.get(where=metadata_filter, include=["documents", "metadatas"])
                
                if results and results['ids']:
                    for i, doc_id in enumerate(results['ids']):
                        doc = StoredDocument(
                            id=doc_id,
                            content=results['documents'][i] if results['documents'] else "",
                            metadata=results['metadatas'][i] if results['metadatas'] else {},
                            collection=collection_name
                        )
                        documents.append(doc)
                        
            except Exception as e:
                logger.warning(f"Metadata query failed: {e}")
        
        return documents
    
    def get_by_source_file(self, source_file: str, collection_type: Optional[CollectionType] = None) -> List[StoredDocument]:
        """Get all documents from a specific source file."""
        return self.get_by_metadata({'source_file': source_file}, collection_type)
    
    def get_related(self, doc_id: str, n_results: int = 5, min_similarity: float = 0.5) -> List[SearchResult]:
        """Find documents related to a given document."""
        doc = self.get(doc_id)
        if not doc:
            return []
        
        # Get document's embedding
        result = self.encoder.encode_single(doc.content)
        if not result or not result.embedding:
            return []
        
        # Search using embedding
        collection_type = None
        for ct in CollectionType:
            if self._get_collection_name(ct) == doc.collection:
                collection_type = ct
                break
        
        return self.search_by_embedding(
            embedding=result.embedding,
            collection_type=collection_type or CollectionType.CUSTOM,
            n_results=n_results + 1,  # +1 because the document itself will be returned
            min_similarity=min_similarity
        )[1:]  # Skip the first result (the document itself)
    
    def similarity_matrix(self, doc_ids: List[str], collection_type: CollectionType) -> Dict[str, Dict[str, float]]:
        """Compute similarity matrix for a set of documents."""
        docs = self.get_batch(doc_ids, collection_type)
        
        # Get embeddings
        embeddings = []
        valid_docs = []
        
        for doc in docs:
            if doc:
                result = self.encoder.encode_single(doc.content)
                if result and result.embedding:
                    embeddings.append(result.embedding)
                    valid_docs.append(doc)
        
        if not embeddings:
            return {}
        
        # Compute similarities
        matrix = {}
        for i, doc1 in enumerate(valid_docs):
            matrix[doc1.id] = {}
            for j, doc2 in enumerate(valid_docs):
                if i != j:
                    sim = self.encoder.cosine_similarity(embeddings[i], embeddings[j])
                    matrix[doc1.id][doc2.id] = sim
        
        return matrix
    
    def reset(self) -> bool:
        """Reset the entire vector store."""
        try:
            self.client.reset()
            self._document_cache.clear()
            self.collections._collections.clear()
            self.collections._collection_metadata.clear()
            self._initialize_default_collections()
            logger.warning("Vector store reset")
            return True
        except Exception as e:
            logger.error(f"Reset failed: {e}")
            return False
    
    def close(self):
        """Close the store and save state."""
        self.state.save()
        logger.info("EmbeddingStore closed")


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for embedding store."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Vector storage and retrieval using ChromaDB")
    parser.add_argument("--persist-dir", type=Path, default=Path(".ai_state/vector_store"),
                       help="Persistence directory")
    parser.add_argument("--collection", choices=[c.value for c in CollectionType],
                       help="Collection type")
    parser.add_argument("--query", type=str, help="Search query")
    parser.add_argument("--n-results", type=int, default=10, help="Number of search results")
    parser.add_argument("--add", type=Path, help="Add document from file")
    parser.add_argument("--export", type=Path, help="Export collection to file")
    parser.add_argument("--import", type=Path, help="Import collection from file")
    parser.add_argument("--stats", action="store_true", help="Show collection statistics")
    parser.add_argument("--list-collections", action="store_true", help="List all collections")
    parser.add_argument("--clear", action="store_true", help="Clear collection")
    parser.add_argument("--reset", action="store_true", help="Reset entire store")
    
    args = parser.parse_args()
    
    config = StoreConfig(persist_directory=args.persist_dir)
    store = EmbeddingStore(config)
    
    if args.reset:
        if store.reset():
            print("Store reset successfully")
        else:
            print("Reset failed")
        return
    
    if args.list_collections:
        collections = store.list_collections()
        for coll in collections:
            print(f"- {coll.name}: {coll.collection_type.value} ({coll.document_count} docs)")
        return
    
    if args.stats:
        stats = store.get_collection_stats()
        print(json.dumps(stats, indent=2))
        return
    
    if args.collection and args.clear:
        ct = CollectionType(args.collection)
        if store.clear_collection(ct):
            print(f"Collection '{ct.value}' cleared")
        else:
            print(f"Failed to clear collection")
        return
    
    if args.export and args.collection:
        ct = CollectionType(args.collection)
        docs = store.export_collection(ct, args.export)
        print(f"Exported {len(docs)} documents")
        return
    
    if args.import_file and args.collection:
        ct = CollectionType(args.collection)
        with open(args.import_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        result = store.import_collection(data.get('documents', []), ct)
        print(f"Imported {result.successful} documents, {result.failed} failed")
        return
    
    if args.add and args.collection:
        ct = CollectionType(args.collection)
        content = args.add.read_text(encoding='utf-8')
        doc_id = store.add(content, ct, {'source_file': str(args.add)})
        print(f"Added document: {doc_id}")
        return
    
    if args.query:
        ct = CollectionType(args.collection) if args.collection else None
        results = store.search(args.query, ct, args.n_results)
        
        print(f"\nSearch results for: '{args.query}'\n")
        for i, r in enumerate(results, 1):
            print(f"{i}. [Similarity: {r.similarity:.3f}] {r.collection}")
            print(f"   ID: {r.id}")
            print(f"   Content: {r.content[:200]}...")
            if r.metadata:
                print(f"   Metadata: {json.dumps(r.metadata, default=str)[:100]}")
            print()
        return
    
    # Default: show help
    parser.print_help()


if __name__ == "__main__":
    main()