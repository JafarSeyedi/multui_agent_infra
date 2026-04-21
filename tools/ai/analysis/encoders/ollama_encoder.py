#!/usr/bin/env python3
"""
Ollama Encoder - AI Development Framework
Encodes text chunks into vector embeddings using Ollama models.

Part of the Level 2 Analysis tools (encoders/ollama_encoder.py)
"""

import json
import time
import hashlib
import asyncio
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, Union, Iterator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict
import numpy as np

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ...shared.logger import get_logger
from ...shared.state_manager import StateManager

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class EmbeddingModel(str, Enum):
    """Available Ollama embedding models."""
    MXBAI_EMBED_LARGE = "mxbai-embed-large:latest"  # 1024 dimensions
    NOMIC_EMBED_TEXT = "nomic-embed-text:latest"    # 768 dimensions
    ALL_MINILM = "all-minilm:latest"                # 384 dimensions
    BGE_M3 = "bge-m3:latest"                        # 1024 dimensions
    BGE_LARGE = "bge-large:latest"                  # 1024 dimensions


class EncodingStatus(str, Enum):
    """Status of encoding operation."""
    PENDING = "pending"
    ENCODING = "encoding"
    COMPLETED = "completed"
    FAILED = "failed"
    CACHED = "cached"


class PoolingStrategy(str, Enum):
    """Strategy for pooling token embeddings."""
    MEAN = "mean"
    CLS = "cls"
    MAX = "max"
    WEIGHTED_MEAN = "weighted_mean"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class EncodingRequest:
    """A single encoding request."""
    id: str
    text: str
    model: EmbeddingModel
    priority: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class EncodingResult:
    """Result of an encoding operation."""
    request_id: str
    embedding: List[float]
    model: EmbeddingModel
    dimensions: int
    tokens_used: int
    processing_time_ms: float
    status: EncodingStatus
    content_hash: str
    cached: bool = False
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class BatchEncodingResult:
    """Result of batch encoding."""
    results: List[EncodingResult]
    total_requests: int
    successful: int
    failed: int
    cached: int
    total_tokens: int
    total_time_ms: float
    model: EmbeddingModel
    completed_at: datetime = field(default_factory=datetime.now)


@dataclass
class ModelInfo:
    """Information about an embedding model."""
    name: str
    dimensions: int
    max_tokens: int
    description: str
    is_loaded: bool = False
    memory_usage_mb: Optional[float] = None


@dataclass
class EncoderConfig:
    """Configuration for the encoder."""
    base_url: str = "http://localhost:11434"
    default_model: EmbeddingModel = EmbeddingModel.MXBAI_EMBED_LARGE
    batch_size: int = 10
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: int = 60
    cache_enabled: bool = True
    cache_dir: Optional[Path] = None
    pooling_strategy: PoolingStrategy = PoolingStrategy.MEAN
    normalize_embeddings: bool = True
    truncate_text: bool = True
    max_text_length: int = 8192
    concurrent_requests: int = 5
    enable_metrics: bool = True


# ============================================================
# EMBEDDING CACHE
# ============================================================

class EmbeddingCache:
    """Persistent cache for embeddings."""
    
    def __init__(self, cache_dir: Path, model: EmbeddingModel):
        self.cache_dir = cache_dir
        self.model = model
        self.cache_file = cache_dir / f"{model.value.replace(':', '_').replace('/', '_')}_cache.json"
        self.cache: Dict[str, Dict[str, Any]] = {}
        self._load()
    
    def _load(self):
        """Load cache from disk."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.cache = data.get('embeddings', {})
                logger.info(f"Loaded {len(self.cache)} cached embeddings for {self.model.value}")
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
                self.cache = {}
    
    def save(self):
        """Save cache to disk."""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'model': self.model.value,
                    'updated_at': datetime.now().isoformat(),
                    'embeddings': self.cache
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def get(self, content_hash: str) -> Optional[EncodingResult]:
        """Get cached embedding."""
        if content_hash in self.cache:
            data = self.cache[content_hash]
            return EncodingResult(
                request_id=data.get('request_id', ''),
                embedding=data['embedding'],
                model=EmbeddingModel(data['model']),
                dimensions=data['dimensions'],
                tokens_used=data.get('tokens_used', 0),
                processing_time_ms=0,
                status=EncodingStatus.CACHED,
                content_hash=content_hash,
                cached=True,
                metadata=data.get('metadata', {}),
                created_at=datetime.fromisoformat(data['created_at']) if 'created_at' in data else datetime.now()
            )
        return None
    
    def set(self, content_hash: str, result: EncodingResult):
        """Cache an embedding."""
        self.cache[content_hash] = {
            'request_id': result.request_id,
            'embedding': result.embedding,
            'model': result.model.value,
            'dimensions': result.dimensions,
            'tokens_used': result.tokens_used,
            'metadata': result.metadata,
            'created_at': result.created_at.isoformat()
        }
        
        # Periodic save (every 100 additions)
        if len(self.cache) % 100 == 0:
            self.save()
    
    def clear(self):
        """Clear the cache."""
        self.cache.clear()
        if self.cache_file.exists():
            self.cache_file.unlink()
    
    def size(self) -> int:
        """Get cache size."""
        return len(self.cache)


# ============================================================
# OLLAMA CLIENT
# ============================================================

class OllamaClient:
    """HTTP client for Ollama API with retry logic."""
    
    def __init__(self, config: EncoderConfig):
        self.config = config
        self.session = self._create_session()
        self._available_models: Optional[List[ModelInfo]] = None
    
    def _create_session(self) -> requests.Session:
        """Create HTTP session with retry strategy."""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=self.config.retry_delay,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def get_available_models(self) -> List[ModelInfo]:
        """Get list of available embedding models."""
        try:
            response = self.session.get(
                f"{self.config.base_url}/api/tags",
                timeout=self.config.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            models = []
            
            for model_data in data.get('models', []):
                model_name = model_data.get('name', '')
                
                # Filter for embedding models
                if any(emb in model_name.lower() for emb in ['embed', 'bge', 'minilm', 'nomic', 'mxbai']):
                    # Determine dimensions based on model name
                    dimensions = 1024
                    if 'nomic' in model_name.lower():
                        dimensions = 768
                    elif 'minilm' in model_name.lower():
                        dimensions = 384
                    elif 'large' in model_name.lower():
                        dimensions = 1024
                    
                    models.append(ModelInfo(
                        name=model_name,
                        dimensions=dimensions,
                        max_tokens=8192,
                        description=model_data.get('description', ''),
                        is_loaded=True,
                        memory_usage_mb=model_data.get('size', 0) / (1024 * 1024)
                    ))
            
            self._available_models = models
            return models
            
        except Exception as e:
            logger.error(f"Failed to get available models: {e}")
            return []
    
    def embed(self, text: str, model: str) -> Optional[Dict[str, Any]]:
        """Send embedding request to Ollama."""
        try:
            response = self.session.post(
                f"{self.config.base_url}/api/embeddings",
                json={
                    "model": model,
                    "prompt": text,
                    "options": {
                        "temperature": 0.0
                    }
                },
                timeout=self.config.timeout
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Embedding request failed: {e}")
            return None
    
    def embed_batch(self, texts: List[str], model: str) -> List[Optional[Dict[str, Any]]]:
        """Send batch embedding requests."""
        results = []
        for text in texts:
            result = self.embed(text, model)
            results.append(result)
            time.sleep(0.05)  # Small delay to avoid overwhelming
        return results
    
    def check_health(self) -> bool:
        """Check if Ollama is healthy."""
        try:
            response = self.session.get(
                f"{self.config.base_url}/api/tags",
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    def pull_model(self, model: str) -> bool:
        """Pull a model from Ollama registry."""
        try:
            response = self.session.post(
                f"{self.config.base_url}/api/pull",
                json={"name": model},
                timeout=300  # Longer timeout for model download
            )
            response.raise_for_status()
            logger.info(f"Successfully pulled model: {model}")
            return True
        except Exception as e:
            logger.error(f"Failed to pull model {model}: {e}")
            return False
    
    def close(self):
        """Close the HTTP session."""
        self.session.close()


# ============================================================
# MAIN ENCODER CLASS
# ============================================================

class OllamaEncoder:
    """
    Encodes text into vector embeddings using Ollama models.
    
    Features:
    - Multiple embedding model support
    - Persistent caching to avoid re-encoding
    - Batch processing with concurrency
    - Automatic retry with exponential backoff
    - Model health checking and auto-pull
    - Embedding normalization
    - Text truncation and preprocessing
    - Pooling strategies for long texts
    - Metrics and monitoring
    - Async support for high throughput
    """
    
    def __init__(self, config: Optional[EncoderConfig] = None):
        self.config = config or EncoderConfig()
        self.client = OllamaClient(self.config)
        
        # Setup cache
        if self.config.cache_enabled:
            cache_dir = self.config.cache_dir or Path(".ai_state/embeddings")
            cache_dir.mkdir(parents=True, exist_ok=True)
            self.caches: Dict[EmbeddingModel, EmbeddingCache] = {}
        
        # Metrics
        self.metrics = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'failed_requests': 0,
            'total_tokens': 0,
            'total_time_ms': 0.0
        }
        
        # State
        self.state = StateManager(Path(".ai_state") / "ollama_encoder.json")
        self._ensure_models()
    
    def _ensure_models(self):
        """Ensure required models are available."""
        if not self.client.check_health():
            logger.warning("Ollama is not running or not accessible")
            return
        
        available = self.client.get_available_models()
        available_names = [m.name for m in available]
        
        # Check if default model is available
        default_model = self.config.default_model.value
        if default_model not in available_names:
            logger.info(f"Default model {default_model} not found, attempting to pull...")
            self.client.pull_model(default_model)
    
    def _get_cache(self, model: EmbeddingModel) -> EmbeddingCache:
        """Get or create cache for model."""
        if not hasattr(self, 'caches'):
            self.caches = {}
        
        if model not in self.caches:
            cache_dir = self.config.cache_dir or Path(".ai_state/embeddings")
            self.caches[model] = EmbeddingCache(cache_dir, model)
        
        return self.caches[model]
    
    def _compute_content_hash(self, text: str, model: EmbeddingModel) -> str:
        """Compute hash for text content."""
        content = f"{text}|{model.value}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text before encoding."""
        if not text:
            return ""
        
        # Basic cleaning
        text = text.strip()
        
        # Truncate if needed
        if self.config.truncate_text and len(text) > self.config.max_text_length:
            # Simple truncation - could be improved with smarter splitting
            text = text[:self.config.max_text_length]
        
        return text
    
    def _normalize_embedding(self, embedding: List[float]) -> List[float]:
        """Normalize embedding to unit length."""
        if not self.config.normalize_embeddings:
            return embedding
        
        import numpy as np
        vec = np.array(embedding)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        
        return vec.tolist()
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)."""
        # Rough estimate: 1 token ≈ 4 characters for English
        return len(text) // 4
    
    # ============================================================
    # SINGLE ENCODING
    # ============================================================
    
    def encode_single(self, 
                      text: str,
                      model: Optional[EmbeddingModel] = None,
                      request_id: Optional[str] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> Optional[EncodingResult]:
        """Encode a single text string."""
        start_time = time.time()
        model = model or self.config.default_model
        
        # Preprocess
        text = self._preprocess_text(text)
        if not text:
            return None
        
        content_hash = self._compute_content_hash(text, model)
        
        # Check cache
        if self.config.cache_enabled:
            cache = self._get_cache(model)
            cached = cache.get(content_hash)
            if cached:
                self.metrics['cache_hits'] += 1
                return cached
        
        self.metrics['cache_misses'] += 1
        self.metrics['total_requests'] += 1
        
        request_id = request_id or f"req_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(text) % 10000}"
        
        # Send request
        response = self.client.embed(text, model.value)
        
        processing_time = (time.time() - start_time) * 1000
        self.metrics['total_time_ms'] += processing_time
        
        if response and 'embedding' in response:
            embedding = response['embedding']
            
            # Normalize
            embedding = self._normalize_embedding(embedding)
            
            # Estimate tokens
            tokens_used = self._estimate_tokens(text)
            self.metrics['total_tokens'] += tokens_used
            
            result = EncodingResult(
                request_id=request_id,
                embedding=embedding,
                model=model,
                dimensions=len(embedding),
                tokens_used=tokens_used,
                processing_time_ms=processing_time,
                status=EncodingStatus.COMPLETED,
                content_hash=content_hash,
                metadata=metadata or {}
            )
            
            # Cache result
            if self.config.cache_enabled:
                cache = self._get_cache(model)
                cache.set(content_hash, result)
            
            return result
        else:
            self.metrics['failed_requests'] += 1
            return EncodingResult(
                request_id=request_id,
                embedding=[],
                model=model,
                dimensions=0,
                tokens_used=0,
                processing_time_ms=processing_time,
                status=EncodingStatus.FAILED,
                content_hash=content_hash,
                error="Failed to get embedding"
            )
    
    # ============================================================
    # BATCH ENCODING
    # ============================================================
    
    def encode_batch(self,
                     requests: List[EncodingRequest],
                     model: Optional[EmbeddingModel] = None) -> BatchEncodingResult:
        """Encode a batch of requests."""
        start_time = time.time()
        model = model or self.config.default_model
        
        results = []
        successful = 0
        failed = 0
        cached = 0
        total_tokens = 0
        
        # Process in batches
        for i in range(0, len(requests), self.config.batch_size):
            batch = requests[i:i + self.config.batch_size]
            
            for req in batch:
                result = self.encode_single(
                    text=req.text,
                    model=model,
                    request_id=req.id,
                    metadata=req.metadata
                )
                
                if result:
                    results.append(result)
                    if result.status == EncodingStatus.COMPLETED:
                        successful += 1
                        total_tokens += result.tokens_used
                    elif result.status == EncodingStatus.CACHED:
                        cached += 1
                        successful += 1
                        total_tokens += result.tokens_used
                    else:
                        failed += 1
                else:
                    failed += 1
                
            # Progress logging
            if (i + len(batch)) % 50 == 0:
                logger.info(f"Encoded {i + len(batch)}/{len(requests)} requests")
        
        total_time = (time.time() - start_time) * 1000
        
        return BatchEncodingResult(
            results=results,
            total_requests=len(requests),
            successful=successful,
            failed=failed,
            cached=cached,
            total_tokens=total_tokens,
            total_time_ms=total_time,
            model=model
        )
    
    async def encode_batch_async(self,
                                  requests: List[EncodingRequest],
                                  model: Optional[EmbeddingModel] = None) -> BatchEncodingResult:
        """Asynchronously encode a batch of requests."""
        import aiohttp
        import asyncio
        
        start_time = time.time()
        model = model or self.config.default_model
        
        semaphore = asyncio.Semaphore(self.config.concurrent_requests)
        results = []
        successful = 0
        failed = 0
        cached = 0
        total_tokens = 0
        
        async def process_request(req: EncodingRequest) -> Optional[EncodingResult]:
            async with semaphore:
                # Check cache first
                text = self._preprocess_text(req.text)
                content_hash = self._compute_content_hash(text, model)
                
                if self.config.cache_enabled:
                    cache = self._get_cache(model)
                    cached_result = cache.get(content_hash)
                    if cached_result:
                        return cached_result
                
                # Encode via API
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            f"{self.config.base_url}/api/embeddings",
                            json={"model": model.value, "prompt": text},
                            timeout=self.config.timeout
                        ) as response:
                            data = await response.json()
                            
                            if 'embedding' in data:
                                embedding = self._normalize_embedding(data['embedding'])
                                tokens = self._estimate_tokens(text)
                                
                                result = EncodingResult(
                                    request_id=req.id,
                                    embedding=embedding,
                                    model=model,
                                    dimensions=len(embedding),
                                    tokens_used=tokens,
                                    processing_time_ms=0,
                                    status=EncodingStatus.COMPLETED,
                                    content_hash=content_hash,
                                    metadata=req.metadata
                                )
                                
                                # Cache result
                                if self.config.cache_enabled:
                                    cache = self._get_cache(model)
                                    cache.set(content_hash, result)
                                
                                return result
                except Exception as e:
                    logger.error(f"Async encoding failed: {e}")
                
                return None
        
        # Process all requests
        tasks = [process_request(req) for req in requests]
        completed = await asyncio.gather(*tasks)
        
        for result in completed:
            if result:
                results.append(result)
                if result.status == EncodingStatus.COMPLETED:
                    successful += 1
                    total_tokens += result.tokens_used
                elif result.status == EncodingStatus.CACHED:
                    cached += 1
                    successful += 1
                    total_tokens += result.tokens_used
                else:
                    failed += 1
            else:
                failed += 1
        
        total_time = (time.time() - start_time) * 1000
        
        return BatchEncodingResult(
            results=results,
            total_requests=len(requests),
            successful=successful,
            failed=failed,
            cached=cached,
            total_tokens=total_tokens,
            total_time_ms=total_time,
            model=model
        )
    
    # ============================================================
    # SIMILARITY AND SEARCH
    # ============================================================
    
    def cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two embeddings."""
        import numpy as np
        a = np.array(a)
        b = np.array(b)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))
    
    def find_similar(self,
                     query: Union[str, List[float]],
                     candidates: List[EncodingResult],
                     top_k: int = 5,
                     threshold: float = 0.0) -> List[Tuple[EncodingResult, float]]:
        """Find most similar candidates to query."""
        # Get query embedding
        if isinstance(query, str):
            query_result = self.encode_single(query)
            if not query_result:
                return []
            query_embedding = query_result.embedding
        else:
            query_embedding = query
        
        # Calculate similarities
        similarities = []
        for candidate in candidates:
            if candidate.embedding:
                sim = self.cosine_similarity(query_embedding, candidate.embedding)
                if sim >= threshold:
                    similarities.append((candidate, sim))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def batch_similarity(self,
                         embeddings: List[List[float]],
                         query_embedding: List[float]) -> List[float]:
        """Calculate similarities for a batch of embeddings."""
        import numpy as np
        
        embeddings_matrix = np.array(embeddings)
        query_vec = np.array(query_embedding)
        
        # Normalize
        query_norm = query_vec / (np.linalg.norm(query_vec) + 1e-10)
        embeddings_norm = embeddings_matrix / (np.linalg.norm(embeddings_matrix, axis=1, keepdims=True) + 1e-10)
        
        # Dot product
        similarities = np.dot(embeddings_norm, query_norm)
        return similarities.tolist()
    
    # ============================================================
    # MODEL MANAGEMENT
    # ============================================================
    
    def get_available_models(self) -> List[ModelInfo]:
        """Get available embedding models."""
        return self.client.get_available_models()
    
    def get_model_info(self, model: EmbeddingModel) -> Optional[ModelInfo]:
        """Get information about a specific model."""
        models = self.get_available_models()
        for m in models:
            if m.name == model.value:
                return m
        return None
    
    def pull_model(self, model: EmbeddingModel) -> bool:
        """Pull a model from registry."""
        return self.client.pull_model(model.value)
    
    def check_health(self) -> Dict[str, Any]:
        """Check health of Ollama service."""
        is_healthy = self.client.check_health()
        models = self.get_available_models() if is_healthy else []
        
        return {
            'healthy': is_healthy,
            'base_url': self.config.base_url,
            'available_models': [m.name for m in models],
            'default_model': self.config.default_model.value,
            'cache_size': sum(c.size() for c in self.caches.values()) if hasattr(self, 'caches') else 0
        }
    
    # ============================================================
    # CACHE MANAGEMENT
    # ============================================================
    
    def clear_cache(self, model: Optional[EmbeddingModel] = None):
        """Clear embedding cache."""
        if model:
            if hasattr(self, 'caches') and model in self.caches:
                self.caches[model].clear()
        else:
            if hasattr(self, 'caches'):
                for cache in self.caches.values():
                    cache.clear()
    
    def save_cache(self):
        """Save all caches to disk."""
        if hasattr(self, 'caches'):
            for cache in self.caches.values():
                cache.save()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not hasattr(self, 'caches'):
            return {'total_entries': 0, 'by_model': {}}
        
        stats = {'total_entries': 0, 'by_model': {}}
        
        for model, cache in self.caches.items():
            size = cache.size()
            stats['by_model'][model.value] = size
            stats['total_entries'] += size
        
        return stats
    
    # ============================================================
    # METRICS AND MONITORING
    # ============================================================
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get encoding metrics."""
        metrics = self.metrics.copy()
        
        # Calculate derived metrics
        if metrics['total_requests'] > 0:
            metrics['cache_hit_rate'] = metrics['cache_hits'] / metrics['total_requests']
            metrics['avg_time_ms'] = metrics['total_time_ms'] / metrics['total_requests']
        else:
            metrics['cache_hit_rate'] = 0.0
            metrics['avg_time_ms'] = 0.0
        
        # Add cache stats
        metrics['cache_stats'] = self.get_cache_stats()
        
        return metrics
    
    def reset_metrics(self):
        """Reset metrics."""
        self.metrics = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'failed_requests': 0,
            'total_tokens': 0,
            'total_time_ms': 0.0
        }
    
    # ============================================================
    # UTILITY METHODS
    # ============================================================
    
    def encode_texts(self,
                     texts: List[str],
                     model: Optional[EmbeddingModel] = None,
                     metadata_list: Optional[List[Dict[str, Any]]] = None) -> List[EncodingResult]:
        """Convenience method to encode a list of texts."""
        requests = []
        for i, text in enumerate(texts):
            req = EncodingRequest(
                id=f"text_{i}",
                text=text,
                model=model or self.config.default_model,
                metadata=metadata_list[i] if metadata_list and i < len(metadata_list) else {}
            )
            requests.append(req)
        
        result = self.encode_batch(requests, model)
        return result.results
    
    def encode_chunks(self,
                      chunks: List[Any],
                      text_extractor: Optional[callable] = None,
                      model: Optional[EmbeddingModel] = None) -> List[EncodingResult]:
        """Encode a list of chunk objects."""
        requests = []
        
        for i, chunk in enumerate(chunks):
            if text_extractor:
                text = text_extractor(chunk)
            elif hasattr(chunk, 'content'):
                text = chunk.content
            else:
                text = str(chunk)
            
            req = EncodingRequest(
                id=getattr(chunk, 'id', f"chunk_{i}"),
                text=text,
                model=model or self.config.default_model,
                metadata={
                    'chunk_id': getattr(chunk, 'id', None),
                    'chunk_type': getattr(chunk, 'chunk_type', None),
                    'source_file': getattr(chunk, 'file_path', None)
                }
            )
            requests.append(req)
        
        result = self.encode_batch(requests, model)
        return result.results
    
    def reduce_dimensions(self,
                          embedding: List[float],
                          target_dim: int = 2,
                          method: str = 'pca') -> List[float]:
        """Reduce embedding dimensions for visualization."""
        import numpy as np
        
        # This is a placeholder - actual implementation would use PCA/UMAP
        vec = np.array(embedding)
        
        if method == 'pca':
            # Simple averaging for demo
            reduced = np.mean(vec.reshape(-1, target_dim), axis=0)
        else:
            reduced = vec[:target_dim]
        
        return reduced.tolist()
    
    def close(self):
        """Clean up resources."""
        self.save_cache()
        self.client.close()
        self.state.save()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for Ollama encoder."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Encode text using Ollama embedding models")
    parser.add_argument("input", type=Path, help="Input text file or directory")
    parser.add_argument("--output", "-o", type=Path, help="Output JSON file")
    parser.add_argument("--model", choices=[m.value for m in EmbeddingModel],
                       default=EmbeddingModel.MXBAI_EMBED_LARGE.value, help="Embedding model")
    parser.add_argument("--batch-size", type=int, default=10, help="Batch size")
    parser.add_argument("--url", default="http://localhost:11434", help="Ollama URL")
    parser.add_argument("--no-cache", action="store_true", help="Disable caching")
    parser.add_argument("--health", action="store_true", help="Check health only")
    parser.add_argument("--clear-cache", action="store_true", help="Clear cache")
    parser.add_argument("--stats", action="store_true", help="Show cache statistics")
    
    args = parser.parse_args()
    
    config = EncoderConfig(
        base_url=args.url,
        default_model=EmbeddingModel(args.model),
        batch_size=args.batch_size,
        cache_enabled=not args.no_cache
    )
    
    encoder = OllamaEncoder(config)
    
    if args.health:
        health = encoder.check_health()
        print(json.dumps(health, indent=2))
        return
    
    if args.clear_cache:
        encoder.clear_cache()
        print("Cache cleared")
        return
    
    if args.stats:
        stats = encoder.get_cache_stats()
        print(json.dumps(stats, indent=2))
        return
    
    # Read input
    if args.input.is_file():
        text = args.input.read_text(encoding='utf-8')
        texts = [text]
    else:
        texts = []
        for file_path in args.input.glob("*.txt"):
            texts.append(file_path.read_text(encoding='utf-8'))
    
    # Encode
    results = encoder.encode_texts(texts)
    
    # Output
    output_data = {
        'model': args.model,
        'count': len(results),
        'results': [
            {
                'request_id': r.request_id,
                'embedding': r.embedding,
                'dimensions': r.dimensions,
                'tokens_used': r.tokens_used,
                'cached': r.cached,
                'content_hash': r.content_hash
            }
            for r in results if r.status == EncodingStatus.COMPLETED
        ]
    }
    
    json_str = json.dumps(output_data, indent=2)
    
    if args.output:
        args.output.write_text(json_str)
        print(f"Output saved to {args.output}")
    else:
        print(json_str)
    
    # Show metrics
    metrics = encoder.get_metrics()
    print(f"\nMetrics: {metrics['successful_requests']} successful, "
          f"{metrics['cache_hit_rate']:.1%} cache hit rate, "
          f"{metrics['avg_time_ms']:.1f}ms avg")


if __name__ == "__main__":
    main()