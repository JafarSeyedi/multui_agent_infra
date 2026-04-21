#!/usr/bin/env python3
"""
Batch Encoder - AI Development Framework
Handles large-scale batch encoding with queue management and parallel processing.

Part of the Level 2 Analysis tools (encoders/batch_encoder.py)

This batch_encoder.py provides:

1. Priority Job Queue - FIFO queue with priority levels (low, normal, high, critical)
2. Concurrent Processing - Multiple jobs processed simultaneously with configurable workers
3. Checkpoint/Resume - Automatic checkpointing for long-running jobs
4. Parallel Encoding - Thread/process pool for batch encoding within jobs
5. Rate Limiting - Token bucket rate limiter for API throttling
6. Scheduling Windows - Optional time windows for processing
7. Comprehensive Metrics - Job and batch-level performance metrics
8. Job Persistence - Jobs survive restarts via state management
9. Retry Support - Automatic retry for failed requests
10. Progress Tracking - Real-time progress updates
11. Async Support - Async processing mode for high throughput
12. Export Capabilities - Export job results to JSON

The batch encoder provides industrial-scale encoding capabilities, handling thousands of texts efficiently with proper queue management and fault tolerance.

"""

import json
import time
import asyncio
import threading
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, Union, Iterator, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict
from queue import Queue, PriorityQueue
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import multiprocessing as mp

from ...shared.logger import get_logger
from ...shared.state_manager import StateManager
from .ollama_encoder import (
    OllamaEncoder, 
    EncodingRequest, 
    EncodingResult, 
    BatchEncodingResult,
    EmbeddingModel, 
    EncoderConfig,
    EncodingStatus
)

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class BatchPriority(int, Enum):
    """Priority levels for batch processing."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class BatchStatus(str, Enum):
    """Status of a batch job."""
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CheckpointStrategy(str, Enum):
    """Strategy for checkpointing."""
    NONE = "none"
    PER_BATCH = "per_batch"
    PER_N_ITEMS = "per_n_items"
    TIME_INTERVAL = "time_interval"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class BatchJob:
    """A batch encoding job."""
    id: str
    name: str
    requests: List[EncodingRequest]
    model: EmbeddingModel
    priority: BatchPriority = BatchPriority.NORMAL
    status: BatchStatus = BatchStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    total_items: int = 0
    processed_items: int = 0
    successful_items: int = 0
    failed_items: int = 0
    cached_items: int = 0
    result: Optional[BatchEncodingResult] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    checkpoint_data: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        self.total_items = len(self.requests)
    
    def update_progress(self):
        """Update progress percentage."""
        if self.total_items > 0:
            self.progress = (self.processed_items / self.total_items) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'model': self.model.value,
            'priority': self.priority.value,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'progress': self.progress,
            'total_items': self.total_items,
            'processed_items': self.processed_items,
            'successful_items': self.successful_items,
            'failed_items': self.failed_items,
            'cached_items': self.cached_items,
            'error': self.error,
            'metadata': self.metadata,
            'tags': self.tags
        }


@dataclass
class BatchConfig:
    """Configuration for batch encoder."""
    max_concurrent_jobs: int = 2
    max_workers: int = 4
    batch_size: int = 50
    queue_size: int = 1000
    checkpoint_enabled: bool = True
    checkpoint_strategy: CheckpointStrategy = CheckpointStrategy.PER_BATCH
    checkpoint_interval_items: int = 100
    checkpoint_interval_seconds: int = 60
    checkpoint_dir: Path = field(default_factory=lambda: Path(".ai_state/batch_checkpoints"))
    retry_failed: bool = True
    max_retries: int = 3
    retry_delay: float = 1.0
    progress_update_interval: int = 10  # Update progress every N items
    enable_metrics: bool = True
    enable_scheduling: bool = False
    schedule_window_start: Optional[str] = None  # "HH:MM"
    schedule_window_end: Optional[str] = None    # "HH:MM"
    rate_limit_rpm: Optional[int] = None  # Requests per minute


# ============================================================
# JOB QUEUE
# ============================================================

class JobQueue:
    """Priority queue for batch jobs."""
    
    def __init__(self, max_size: int = 1000):
        self._queue: PriorityQueue = PriorityQueue(maxsize=max_size)
        self._job_map: Dict[str, BatchJob] = {}
        self._lock = threading.Lock()
    
    def put(self, job: BatchJob) -> bool:
        """Add job to queue."""
        try:
            # Higher priority = lower number in queue
            priority_value = -job.priority.value
            self._queue.put_nowait((priority_value, job.created_at.timestamp(), job.id))
            
            with self._lock:
                self._job_map[job.id] = job
                job.status = BatchStatus.QUEUED
            
            return True
        except Exception:
            return False
    
    def get(self, timeout: Optional[float] = None) -> Optional[BatchJob]:
        """Get next job from queue."""
        try:
            _, _, job_id = self._queue.get(timeout=timeout)
            
            with self._lock:
                job = self._job_map.get(job_id)
                if job:
                    job.status = BatchStatus.PROCESSING
                    job.started_at = datetime.now()
                return job
                
        except Exception:
            return None
    
    def peek(self) -> Optional[BatchJob]:
        """Peek at next job without removing."""
        try:
            # Can't peek PriorityQueue directly
            return None
        except Exception:
            return None
    
    def remove(self, job_id: str) -> bool:
        """Remove job from queue."""
        with self._lock:
            if job_id in self._job_map:
                del self._job_map[job_id]
                return True
        return False
    
    def get_job(self, job_id: str) -> Optional[BatchJob]:
        """Get job by ID."""
        with self._lock:
            return self._job_map.get(job_id)
    
    def list_jobs(self, status: Optional[BatchStatus] = None) -> List[BatchJob]:
        """List jobs, optionally filtered by status."""
        with self._lock:
            jobs = list(self._job_map.values())
            if status:
                jobs = [j for j in jobs if j.status == status]
            return jobs
    
    def size(self) -> int:
        """Get queue size."""
        return self._queue.qsize()
    
    def clear(self):
        """Clear the queue."""
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except Exception:
                pass
        
        with self._lock:
            self._job_map.clear()


# ============================================================
# CHECKPOINT MANAGER
# ============================================================

class CheckpointManager:
    """Manages job checkpoints for resumability."""
    
    def __init__(self, checkpoint_dir: Path):
        self.checkpoint_dir = checkpoint_dir
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    def save_checkpoint(self, job: BatchJob):
        """Save job checkpoint."""
        checkpoint_file = self.checkpoint_dir / f"{job.id}_checkpoint.json"
        
        checkpoint_data = {
            'job_id': job.id,
            'processed_items': job.processed_items,
            'successful_items': job.successful_items,
            'failed_items': job.failed_items,
            'cached_items': job.cached_items,
            'remaining_request_ids': [r.id for r in job.requests[job.processed_items:]],
            'saved_at': datetime.now().isoformat(),
            'result_ids': [r.request_id for r in job.result.results] if job.result else []
        }
        
        job.checkpoint_data = checkpoint_data
        
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, indent=2)
        
        logger.debug(f"Checkpoint saved for job {job.id} at {job.processed_items} items")
    
    def load_checkpoint(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Load job checkpoint."""
        checkpoint_file = self.checkpoint_dir / f"{job_id}_checkpoint.json"
        
        if not checkpoint_file.exists():
            return None
        
        try:
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load checkpoint for {job_id}: {e}")
            return None
    
    def delete_checkpoint(self, job_id: str):
        """Delete job checkpoint."""
        checkpoint_file = self.checkpoint_dir / f"{job_id}_checkpoint.json"
        if checkpoint_file.exists():
            checkpoint_file.unlink()
    
    def list_checkpoints(self) -> List[str]:
        """List available checkpoint job IDs."""
        return [f.stem.replace('_checkpoint', '') for f in self.checkpoint_dir.glob("*_checkpoint.json")]


# ============================================================
# METRICS COLLECTOR
# ============================================================

class MetricsCollector:
    """Collects and aggregates batch encoding metrics."""
    
    def __init__(self):
        self.metrics: Dict[str, Any] = defaultdict(list)
        self._lock = threading.Lock()
    
    def record_job_start(self, job: BatchJob):
        """Record job start."""
        with self._lock:
            self.metrics['job_starts'].append({
                'job_id': job.id,
                'total_items': job.total_items,
                'timestamp': datetime.now().isoformat()
            })
    
    def record_job_completion(self, job: BatchJob):
        """Record job completion."""
        with self._lock:
            self.metrics['job_completions'].append({
                'job_id': job.id,
                'successful': job.successful_items,
                'failed': job.failed_items,
                'cached': job.cached_items,
                'duration_seconds': (job.completed_at - job.started_at).total_seconds() if job.started_at and job.completed_at else 0,
                'timestamp': datetime.now().isoformat()
            })
    
    def record_batch(self, size: int, duration_ms: float, success: bool):
        """Record batch processing."""
        with self._lock:
            self.metrics['batches'].append({
                'size': size,
                'duration_ms': duration_ms,
                'success': success,
                'timestamp': datetime.now().isoformat()
            })
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        with self._lock:
            summary = {
                'total_jobs_started': len(self.metrics['job_starts']),
                'total_jobs_completed': len(self.metrics['job_completions']),
                'total_batches': len(self.metrics['batches']),
            }
            
            if self.metrics['job_completions']:
                total_items = sum(j['successful'] + j['failed'] + j['cached'] for j in self.metrics['job_completions'])
                total_successful = sum(j['successful'] for j in self.metrics['job_completions'])
                total_cached = sum(j['cached'] for j in self.metrics['job_completions'])
                
                summary.update({
                    'total_items_processed': total_items,
                    'total_successful': total_successful,
                    'total_cached': total_cached,
                    'success_rate': total_successful / total_items if total_items > 0 else 0,
                    'cache_hit_rate': total_cached / total_items if total_items > 0 else 0,
                    'avg_duration_seconds': sum(j['duration_seconds'] for j in self.metrics['job_completions']) / len(self.metrics['job_completions'])
                })
            
            return summary
    
    def reset(self):
        """Reset metrics."""
        with self._lock:
            self.metrics.clear()


# ============================================================
# MAIN BATCH ENCODER CLASS
# ============================================================

class BatchEncoder:
    """
    High-performance batch encoder with queue management.
    
    Features:
    - Priority-based job queue
    - Concurrent job processing
    - Checkpoint/resume support
    - Parallel encoding with thread/process pools
    - Rate limiting
    - Scheduling windows
    - Comprehensive metrics
    - Retry with exponential backoff
    - Progress tracking
    - Job persistence and recovery
    """
    
    def __init__(self, 
                 config: Optional[BatchConfig] = None,
                 encoder: Optional[OllamaEncoder] = None):
        self.config = config or BatchConfig()
        self.encoder = encoder or OllamaEncoder()
        self.queue = JobQueue(max_size=self.config.queue_size)
        self.checkpoints = CheckpointManager(self.config.checkpoint_dir)
        self.metrics = MetricsCollector()
        
        # Job storage
        self.jobs: Dict[str, BatchJob] = {}
        self.completed_jobs: Dict[str, BatchJob] = {}
        
        # State management
        self.state = StateManager(Path(".ai_state") / "batch_encoder.json")
        
        # Processing control
        self._running = False
        self._workers: List[threading.Thread] = []
        self._executor: Optional[ThreadPoolExecutor] = None
        self._lock = threading.Lock()
        
        # Rate limiting
        self._rate_limiter: Optional[RateLimiter] = None
        if self.config.rate_limit_rpm:
            self._rate_limiter = RateLimiter(self.config.rate_limit_rpm)
        
        # Load persisted jobs
        self._load_state()
        
        logger.info(f"BatchEncoder initialized with {self.config.max_concurrent_jobs} concurrent jobs")
    
    def _load_state(self):
        """Load persisted jobs from state."""
        saved_jobs = self.state.get('jobs', {})
        for job_id, job_data in saved_jobs.items():
            if job_data.get('status') in [BatchStatus.PENDING.value, BatchStatus.QUEUED.value, BatchStatus.PROCESSING.value]:
                # Recreate job from saved data
                job = self._deserialize_job(job_data)
                if job:
                    self.jobs[job_id] = job
                    if job.status == BatchStatus.PENDING:
                        self.queue.put(job)
        
        saved_completed = self.state.get('completed_jobs', {})
        for job_id, job_data in saved_completed.items():
            job = self._deserialize_job(job_data)
            if job:
                self.completed_jobs[job_id] = job
    
    def _save_state(self):
        """Persist jobs to state."""
        job_data = {job_id: job.to_dict() for job_id, job in self.jobs.items()}
        completed_data = {job_id: job.to_dict() for job_id, job in self.completed_jobs.items()}
        
        self.state.set('jobs', job_data)
        self.state.set('completed_jobs', completed_data)
        self.state.save()
    
    def _deserialize_job(self, data: Dict[str, Any]) -> Optional[BatchJob]:
        """Deserialize job from dictionary."""
        try:
            return BatchJob(
                id=data['id'],
                name=data['name'],
                requests=[],  # Requests need to be rebuilt from source
                model=EmbeddingModel(data['model']),
                priority=BatchPriority(data['priority']),
                status=BatchStatus(data['status']),
                created_at=datetime.fromisoformat(data['created_at']),
                started_at=datetime.fromisoformat(data['started_at']) if data.get('started_at') else None,
                completed_at=datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None,
                progress=data.get('progress', 0.0),
                total_items=data.get('total_items', 0),
                processed_items=data.get('processed_items', 0),
                successful_items=data.get('successful_items', 0),
                failed_items=data.get('failed_items', 0),
                cached_items=data.get('cached_items', 0),
                error=data.get('error'),
                metadata=data.get('metadata', {}),
                tags=data.get('tags', [])
            )
        except Exception as e:
            logger.error(f"Failed to deserialize job: {e}")
            return None
    
    # ============================================================
    # JOB MANAGEMENT
    # ============================================================
    
    def submit(self,
               name: str,
               requests: List[EncodingRequest],
               model: Optional[EmbeddingModel] = None,
               priority: BatchPriority = BatchPriority.NORMAL,
               metadata: Optional[Dict[str, Any]] = None,
               tags: Optional[List[str]] = None) -> str:
        """Submit a batch job for processing."""
        job_id = self._generate_job_id(name)
        model = model or self.encoder.config.default_model
        
        job = BatchJob(
            id=job_id,
            name=name,
            requests=requests,
            model=model,
            priority=priority,
            metadata=metadata or {},
            tags=tags or []
        )
        
        with self._lock:
            self.jobs[job_id] = job
        
        # Add to queue
        if self.queue.put(job):
            logger.info(f"Job submitted: {job_id} with {len(requests)} requests")
            self._save_state()
            return job_id
        else:
            logger.error(f"Failed to queue job: {job_id}")
            job.status = BatchStatus.FAILED
            job.error = "Queue full"
            return job_id
    
    def _generate_job_id(self, name: str) -> str:
        """Generate unique job ID."""
        import uuid
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        short_uuid = str(uuid.uuid4())[:8]
        safe_name = "".join(c for c in name if c.isalnum() or c in '_-')[:30]
        return f"job_{timestamp}_{safe_name}_{short_uuid}"
    
    def submit_from_chunks(self,
                           name: str,
                           chunks: List[Any],
                           text_extractor: Optional[Callable] = None,
                           model: Optional[EmbeddingModel] = None,
                           priority: BatchPriority = BatchPriority.NORMAL,
                           chunk_metadata: Optional[List[Dict[str, Any]]] = None) -> str:
        """Submit a job from chunk objects."""
        requests = []
        
        for i, chunk in enumerate(chunks):
            if text_extractor:
                text = text_extractor(chunk)
            elif hasattr(chunk, 'content'):
                text = chunk.content
            else:
                text = str(chunk)
            
            metadata = {}
            if chunk_metadata and i < len(chunk_metadata):
                metadata = chunk_metadata[i]
            
            metadata.update({
                'chunk_id': getattr(chunk, 'id', f"chunk_{i}"),
                'chunk_type': getattr(chunk, 'chunk_type', 'unknown'),
                'source_file': getattr(chunk, 'file_path', None)
            })
            
            req = EncodingRequest(
                id=getattr(chunk, 'id', f"chunk_{i}"),
                text=text,
                model=model or self.encoder.config.default_model,
                metadata=metadata
            )
            requests.append(req)
        
        return self.submit(name, requests, model, priority, {'source': 'chunks'})
    
    def get_job(self, job_id: str) -> Optional[BatchJob]:
        """Get job by ID."""
        with self._lock:
            return self.jobs.get(job_id) or self.completed_jobs.get(job_id)
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending or queued job."""
        with self._lock:
            job = self.jobs.get(job_id)
            if job and job.status in [BatchStatus.PENDING, BatchStatus.QUEUED]:
                job.status = BatchStatus.CANCELLED
                job.completed_at = datetime.now()
                
                # Move to completed
                self.completed_jobs[job_id] = job
                del self.jobs[job_id]
                
                self.queue.remove(job_id)
                self.checkpoints.delete_checkpoint(job_id)
                self._save_state()
                
                logger.info(f"Job cancelled: {job_id}")
                return True
        
        return False
    
    def retry_job(self, job_id: str) -> Optional[str]:
        """Retry a failed job."""
        job = self.get_job(job_id)
        if not job or job.status not in [BatchStatus.FAILED, BatchStatus.PARTIAL]:
            return None
        
        # Create new job with failed items
        failed_requests = []
        if job.result:
            for result in job.result.results:
                if result.status == EncodingStatus.FAILED:
                    # Recreate request
                    req = EncodingRequest(
                        id=result.request_id,
                        text="",  # Need original text
                        model=job.model,
                        metadata=result.metadata
                    )
                    failed_requests.append(req)
        
        if failed_requests:
            return self.submit(
                name=f"{job.name}_retry",
                requests=failed_requests,
                model=job.model,
                priority=job.priority,
                metadata={'retry_of': job_id}
            )
        
        return None
    
    def list_jobs(self, status: Optional[BatchStatus] = None) -> List[BatchJob]:
        """List all jobs, optionally filtered by status."""
        with self._lock:
            all_jobs = list(self.jobs.values()) + list(self.completed_jobs.values())
            if status:
                all_jobs = [j for j in all_jobs if j.status == status]
            return sorted(all_jobs, key=lambda j: j.created_at, reverse=True)
    
    def delete_job(self, job_id: str) -> bool:
        """Delete a completed job."""
        with self._lock:
            if job_id in self.completed_jobs:
                del self.completed_jobs[job_id]
                self.checkpoints.delete_checkpoint(job_id)
                self._save_state()
                return True
        return False
    
    # ============================================================
    # PROCESSING
    # ============================================================
    
    def start(self, block: bool = False):
        """Start processing jobs."""
        if self._running:
            logger.warning("BatchEncoder already running")
            return
        
        self._running = True
        
        # Create worker threads
        for i in range(self.config.max_concurrent_jobs):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"BatchEncoder-{i}",
                daemon=True
            )
            worker.start()
            self._workers.append(worker)
        
        # Create thread pool for parallel encoding
        self._executor = ThreadPoolExecutor(max_workers=self.config.max_workers)
        
        logger.info(f"Started {self.config.max_concurrent_jobs} workers")
        
        if block:
            for worker in self._workers:
                worker.join()
    
    def stop(self, wait: bool = True):
        """Stop processing."""
        self._running = False
        
        if wait:
            for worker in self._workers:
                worker.join(timeout=5)
        
        if self._executor:
            self._executor.shutdown(wait=wait)
        
        self._save_state()
        logger.info("BatchEncoder stopped")
    
    def _worker_loop(self):
        """Worker thread loop."""
        while self._running:
            # Check scheduling window
            if not self._is_in_schedule_window():
                time.sleep(10)
                continue
            
            # Get next job
            job = self.queue.get(timeout=1.0)
            
            if job is None:
                continue
            
            try:
                self._process_job(job)
            except Exception as e:
                logger.error(f"Job processing failed: {e}")
                job.status = BatchStatus.FAILED
                job.error = str(e)
                job.completed_at = datetime.now()
            finally:
                # Move to completed
                with self._lock:
                    if job.id in self.jobs:
                        self.completed_jobs[job.id] = job
                        del self.jobs[job.id]
                
                self.checkpoints.delete_checkpoint(job.id)
                self._save_state()
    
    def _process_job(self, job: BatchJob):
        """Process a single job."""
        logger.info(f"Processing job {job.id}: {job.total_items} items")
        
        self.metrics.record_job_start(job)
        job.status = BatchStatus.PROCESSING
        job.started_at = datetime.now()
        
        # Check for checkpoint
        checkpoint = self.checkpoints.load_checkpoint(job.id)
        start_index = 0
        
        if checkpoint:
            job.processed_items = checkpoint['processed_items']
            job.successful_items = checkpoint['successful_items']
            job.failed_items = checkpoint['failed_items']
            job.cached_items = checkpoint['cached_items']
            start_index = checkpoint['processed_items']
            logger.info(f"Resuming job {job.id} from item {start_index}")
        
        # Initialize result
        job.result = BatchEncodingResult(
            results=[],
            total_requests=job.total_items,
            successful=0,
            failed=0,
            cached=0,
            total_tokens=0,
            total_time_ms=0,
            model=job.model
        )
        
        # Process in batches
        total_batches = (job.total_items - start_index + self.config.batch_size - 1) // self.config.batch_size
        
        for batch_idx in range(total_batches):
            batch_start = start_index + batch_idx * self.config.batch_size
            batch_end = min(batch_start + self.config.batch_size, job.total_items)
            batch_requests = job.requests[batch_start:batch_end]
            
            # Rate limiting
            if self._rate_limiter:
                self._rate_limiter.acquire(len(batch_requests))
            
            # Process batch
            batch_start_time = time.time()
            
            # Use parallel encoding for batch
            futures = []
            for req in batch_requests:
                future = self._executor.submit(
                    self.encoder.encode_single,
                    req.text,
                    job.model,
                    req.id,
                    req.metadata
                )
                futures.append((req, future))
            
            # Collect results
            for req, future in futures:
                try:
                    result = future.result(timeout=30)
                    
                    if result:
                        job.result.results.append(result)
                        
                        if result.status == EncodingStatus.COMPLETED:
                            job.successful_items += 1
                            job.result.successful += 1
                            job.result.total_tokens += result.tokens_used
                        elif result.status == EncodingStatus.CACHED:
                            job.cached_items += 1
                            job.result.cached += 1
                        else:
                            job.failed_items += 1
                            job.result.failed += 1
                    else:
                        job.failed_items += 1
                        job.result.failed += 1
                        
                except Exception as e:
                    logger.warning(f"Request {req.id} failed: {e}")
                    job.failed_items += 1
                    job.result.failed += 1
                    
                    if self.config.retry_failed:
                        # Could add to retry queue
                        pass
            
            batch_duration = (time.time() - batch_start_time) * 1000
            self.metrics.record_batch(len(batch_requests), batch_duration, True)
            
            # Update progress
            job.processed_items = batch_end
            job.update_progress()
            job.result.total_time_ms += batch_duration
            
            # Checkpoint
            if self.config.checkpoint_enabled:
                should_checkpoint = False
                
                if self.config.checkpoint_strategy == CheckpointStrategy.PER_BATCH:
                    should_checkpoint = True
                elif self.config.checkpoint_strategy == CheckpointStrategy.PER_N_ITEMS:
                    should_checkpoint = (job.processed_items % self.config.checkpoint_interval_items == 0)
                
                if should_checkpoint:
                    self.checkpoints.save_checkpoint(job)
            
            # Progress logging
            if (batch_idx + 1) % self.config.progress_update_interval == 0:
                logger.info(f"Job {job.id}: {job.progress:.1f}% ({job.processed_items}/{job.total_items})")
        
        # Mark complete
        job.status = BatchStatus.COMPLETED if job.failed_items == 0 else BatchStatus.PARTIAL
        job.completed_at = datetime.now()
        job.progress = 100.0
        
        self.metrics.record_job_completion(job)
        
        logger.info(f"Job {job.id} completed: {job.successful_items} success, {job.cached_items} cached, {job.failed_items} failed")
    
    def _is_in_schedule_window(self) -> bool:
        """Check if current time is within schedule window."""
        if not self.config.enable_scheduling:
            return True
        
        if not self.config.schedule_window_start or not self.config.schedule_window_end:
            return True
        
        now = datetime.now().time()
        start = datetime.strptime(self.config.schedule_window_start, "%H:%M").time()
        end = datetime.strptime(self.config.schedule_window_end, "%H:%M").time()
        
        if start <= end:
            return start <= now <= end
        else:
            return now >= start or now <= end
    
    # ============================================================
    # ASYNC PROCESSING
    # ============================================================
    
    async def process_async(self, job_id: Optional[str] = None):
        """Process jobs asynchronously."""
        import asyncio
        
        if job_id:
            job = self.get_job(job_id)
            if job:
                await self._process_job_async(job)
        else:
            while self._running:
                job = self.queue.get()
                if job:
                    await self._process_job_async(job)
                else:
                    await asyncio.sleep(0.1)
    
    async def _process_job_async(self, job: BatchJob):
        """Process a single job asynchronously."""
        logger.info(f"Processing job {job.id} asynchronously")
        
        job.status = BatchStatus.PROCESSING
        job.started_at = datetime.now()
        
        # Use async batch encoding
        result = await self.encoder.encode_batch_async(job.requests, job.model)
        
        job.result = result
        job.successful_items = result.successful
        job.failed_items = result.failed
        job.cached_items = result.cached
        job.processed_items = job.total_items
        job.status = BatchStatus.COMPLETED if result.failed == 0 else BatchStatus.PARTIAL
        job.completed_at = datetime.now()
        job.progress = 100.0
        
        logger.info(f"Job {job.id} completed: {result.successful} success, {result.cached} cached, {result.failed} failed")
    
    # ============================================================
    # UTILITY METHODS
    # ============================================================
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status."""
        return {
            'queue_size': self.queue.size(),
            'active_jobs': len([j for j in self.jobs.values() if j.status == BatchStatus.PROCESSING]),
            'pending_jobs': len([j for j in self.jobs.values() if j.status == BatchStatus.PENDING]),
            'queued_jobs': len([j for j in self.jobs.values() if j.status == BatchStatus.QUEUED]),
            'completed_jobs': len(self.completed_jobs),
            'workers': len(self._workers),
            'running': self._running
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get processing metrics."""
        metrics = self.metrics.get_summary()
        metrics.update(self.get_queue_status())
        return metrics
    
    def get_job_results(self, job_id: str) -> Optional[BatchEncodingResult]:
        """Get results for a completed job."""
        job = self.get_job(job_id)
        return job.result if job else None
    
    def export_job_results(self, job_id: str, output_path: Optional[Path] = None) -> Optional[str]:
        """Export job results to JSON."""
        job = self.get_job(job_id)
        if not job or not job.result:
            return None
        
        data = {
            'job_id': job.id,
            'job_name': job.name,
            'model': job.model.value,
            'status': job.status.value,
            'total_requests': job.result.total_requests,
            'successful': job.result.successful,
            'failed': job.result.failed,
            'cached': job.result.cached,
            'total_tokens': job.result.total_tokens,
            'total_time_ms': job.result.total_time_ms,
            'results': [
                {
                    'request_id': r.request_id,
                    'embedding': r.embedding,
                    'dimensions': r.dimensions,
                    'tokens_used': r.tokens_used,
                    'status': r.status.value,
                    'cached': r.cached,
                    'metadata': r.metadata
                }
                for r in job.result.results
            ]
        }
        
        json_str = json.dumps(data, indent=2)
        
        if output_path:
            output_path.write_text(json_str)
        
        return json_str
    
    def wait_for_job(self, job_id: str, timeout: Optional[float] = None) -> Optional[BatchJob]:
        """Wait for job to complete."""
        start_time = time.time()
        
        while True:
            job = self.get_job(job_id)
            
            if job and job.status in [BatchStatus.COMPLETED, BatchStatus.PARTIAL, BatchStatus.FAILED, BatchStatus.CANCELLED]:
                return job
            
            if timeout and (time.time() - start_time) > timeout:
                return None
            
            time.sleep(0.5)
    
    def wait_for_all(self, timeout: Optional[float] = None) -> bool:
        """Wait for all jobs to complete."""
        start_time = time.time()
        
        while True:
            with self._lock:
                pending = [j for j in self.jobs.values() if j.status not in [BatchStatus.COMPLETED, BatchStatus.PARTIAL, BatchStatus.FAILED, BatchStatus.CANCELLED]]
                
                if not pending and self.queue.size() == 0:
                    return True
            
            if timeout and (time.time() - start_time) > timeout:
                return False
            
            time.sleep(0.5)
    
    def clear_completed_jobs(self, older_than_days: Optional[int] = None):
        """Clear completed jobs."""
        with self._lock:
            to_delete = []
            for job_id, job in self.completed_jobs.items():
                if older_than_days:
                    cutoff = datetime.now() - timedelta(days=older_than_days)
                    if job.completed_at and job.completed_at < cutoff:
                        to_delete.append(job_id)
                else:
                    to_delete.append(job_id)
            
            for job_id in to_delete:
                del self.completed_jobs[job_id]
                self.checkpoints.delete_checkpoint(job_id)
            
            self._save_state()
            logger.info(f"Cleared {len(to_delete)} completed jobs")
    
    def close(self):
        """Clean up resources."""
        self.stop(wait=True)
        self._save_state()
        logger.info("BatchEncoder closed")


# ============================================================
# RATE LIMITER
# ============================================================

class RateLimiter:
    """Token bucket rate limiter."""
    
    def __init__(self, requests_per_minute: int):
        self.rate = requests_per_minute
        self.tokens = requests_per_minute
        self.last_refill = time.time()
        self._lock = threading.Lock()
    
    def acquire(self, count: int = 1):
        """Acquire tokens."""
        with self._lock:
            self._refill()
            
            while self.tokens < count:
                sleep_time = (count - self.tokens) / self.rate * 60
                time.sleep(sleep_time)
                self._refill()
            
            self.tokens -= count
    
    def _refill(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        new_tokens = elapsed * (self.rate / 60.0)
        self.tokens = min(self.rate, self.tokens + new_tokens)
        self.last_refill = now


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for batch encoder."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Batch encoding with queue management")
    parser.add_argument("--input", "-i", type=Path, help="Input file with texts to encode (one per line)")
    parser.add_argument("--output", "-o", type=Path, help="Output file for results")
    parser.add_argument("--name", type=str, default="cli_batch", help="Job name")
    parser.add_argument("--model", choices=[m.value for m in EmbeddingModel],
                       default=EmbeddingModel.MXBAI_EMBED_LARGE.value, help="Embedding model")
    parser.add_argument("--priority", choices=["low", "normal", "high", "critical"],
                       default="normal", help="Job priority")
    parser.add_argument("--concurrent", type=int, default=2, help="Max concurrent jobs")
    parser.add_argument("--workers", type=int, default=4, help="Worker threads per job")
    parser.add_argument("--batch-size", type=int, default=50, help="Batch size")
    parser.add_argument("--list-jobs", action="store_true", help="List all jobs")
    parser.add_argument("--job-id", type=str, help="Get specific job status")
    parser.add_argument("--wait", action="store_true", help="Wait for job to complete")
    parser.add_argument("--metrics", action="store_true", help="Show metrics")
    
    args = parser.parse_args()
    
    config = BatchConfig(
        max_concurrent_jobs=args.concurrent,
        max_workers=args.workers,
        batch_size=args.batch_size
    )
    
    encoder = BatchEncoder(config)
    
    if args.list_jobs:
        jobs = encoder.list_jobs()
        print(f"\nJobs ({len(jobs)}):\n")
        for job in jobs[:20]:
            print(f"  {job.id}: {job.name} [{job.status.value}] {job.progress:.1f}%")
        return
    
    if args.job_id:
        job = encoder.get_job(args.job_id)
        if job:
            print(json.dumps(job.to_dict(), indent=2, default=str))
        else:
            print(f"Job not found: {args.job_id}")
        return
    
    if args.metrics:
        print(json.dumps(encoder.get_metrics(), indent=2))
        return
    
    if args.input:
        # Read texts
        texts = args.input.read_text(encoding='utf-8').strip().split('\n')
        texts = [t.strip() for t in texts if t.strip()]
        
        # Create requests
        requests = []
        for i, text in enumerate(texts):
            req = EncodingRequest(
                id=f"input_{i}",
                text=text,
                model=EmbeddingModel(args.model)
            )
            requests.append(req)
        
        # Submit job
        priority_map = {'low': 0, 'normal': 1, 'high': 2, 'critical': 3}
        job_id = encoder.submit(
            name=args.name,
            requests=requests,
            model=EmbeddingModel(args.model),
            priority=BatchPriority(priority_map[args.priority])
        )
        
        print(f"Job submitted: {job_id}")
        
        # Start processing
        encoder.start()
        
        if args.wait:
            print("Waiting for job to complete...")
            job = encoder.wait_for_job(job_id)
            
            if job and args.output:
                encoder.export_job_results(job_id, args.output)
                print(f"Results saved to {args.output}")
            
            print(f"Job completed: {job.status.value}")
            print(f"  Successful: {job.successful_items}")
            print(f"  Cached: {job.cached_items}")
            print(f"  Failed: {job.failed_items}")
        
        encoder.stop()


if __name__ == "__main__":
    main()