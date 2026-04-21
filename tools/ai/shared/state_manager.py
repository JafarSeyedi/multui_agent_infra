#!/usr/bin/env python3
"""
State Manager - Persistent state management for the AI development framework.

Part of the Shared module (shared/state_manager.py)

This state_manager.py provides:

Multiple Storage Backends - JSON, SQLite, Pickle, Memory
Automatic Persistence - Configurable auto-save intervals
TTL Support - Time-to-live for automatic entry expiration
Snapshots and Rollback - Create and restore state snapshots
Backup and Restore - Automatic backups with retention
Thread-Safe Operations - Locking for concurrent access
Lazy Loading - Load state only when needed
Atomic Transactions - Context manager for atomic operations
Namespaced Storage - Organize state with prefixes
Import/Export - JSON serialization for portability
Statistics and Monitoring - Track state usage
CLI Interface - Command-line state management

The state manager provides persistent storage for all framework components, enabling resumable 
operations and cross-session state preservation.


┌─────────────────────────────────────────────────────────────────┐
│                         STATE MANAGER                           │
│  (Shared - persists ALL data: workflows, tasks, contexts, etc.) │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌────────────────┐    ┌────────────────┐    ┌───────────────┐
│    CONTEXT     │    │    SESSION     │    │    STATE      │
│(ContextManager)│    │(SessionManager)│    │(Workflow/Task)│
└────────────────┘    └────────────────┘    └───────────────┘


STATE (What)
    The actual data at a point in time
    Stored in state_manager (shared)

    Examples: workflow execution state, task status, variable values
    Lifespan: Persists until explicitly deleted/cleaned up
    Scope: Global to the system

CONTEXT (Where + Why)
    The execution environment that holds state
    Managed by ContextManager 
    Provides isolation between different executions
    Examples: WorkflowContext, TaskContext
    Lifespan: From workflow/task start to completion
    Scope: Specific to a workflow or task execution
    Contains: Variables, metadata, parent-child relationships

SESSION (Who + When)
    The interactive period of user/agent engagement
    Tracks a continuous interaction flow
    Examples: CLI session, API session, Human-in-the-loop session
    Lifespan: From login/start to logout/expiry
    Scope: Specific to a user/agent identity
    Contains: Authentication, preferences, active workflows/tasks

Relationships:
    A SESSION can have multiple WORKFLOW CONTEXTS
    A WORKFLOW CONTEXT can have multiple TASK CONTEXTS
    Each CONTEXT manages its own STATE via state_manager

"""

import os
import json
import sqlite3
import threading
import hashlib
import shutil
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from contextlib import contextmanager
import pickle
import tempfile

from .logger import get_logger
from .file_utils import ensure_dir, safe_read, safe_write, safe_copy
from .config import get_config, StateConfig

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class StorageBackend(str, Enum):
    """Storage backend type."""
    JSON = "json"
    SQLITE = "sqlite"
    PICKLE = "pickle"
    MEMORY = "memory"
    CUSTOM = "custom"


class CompressionType(str, Enum):
    """Compression type."""
    NONE = "none"
    GZIP = "gzip"
    ZLIB = "zlib"
    LZ4 = "lz4"


class EncryptionType(str, Enum):
    """Encryption type."""
    NONE = "none"
    AES = "aes"
    FERNET = "fernet"


class StateScope(str, Enum):
    """State scope."""
    GLOBAL = "global"
    PROJECT = "project"
    SESSION = "session"
    USER = "user"
    TEMPORARY = "temporary"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class StateEntry:
    """State entry with metadata."""
    key: str
    value: Any
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    accessed_at: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    ttl: Optional[int] = None  # Time to live in seconds
    scope: StateScope = StateScope.GLOBAL
    version: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        if self.ttl is None:
            return False
        expiry = self.updated_at + timedelta(seconds=self.ttl)
        return datetime.now() > expiry
    
    def touch(self):
        """Update access time and count."""
        self.accessed_at = datetime.now()
        self.access_count += 1


@dataclass
class StateSnapshot:
    """Snapshot of state at a point in time."""
    id: str
    created_at: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    description: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================
# STORAGE BACKENDS
# ============================================================

class StorageBackendBase:
    """Base class for storage backends."""
    
    def __init__(self, config: StateConfig):
        self.config = config
    
    def load(self) -> Dict[str, StateEntry]:
        """Load all state entries."""
        raise NotImplementedError
    
    def save(self, entries: Dict[str, StateEntry]):
        """Save all state entries."""
        raise NotImplementedError
    
    def close(self):
        """Close the backend."""
        pass


class JSONStorageBackend(StorageBackendBase):
    """JSON file storage backend."""
    
    def __init__(self, config: StateConfig):
        super().__init__(config)
        self._file_path = config.directory / f"{config.scope.value}_state.json"
        self._lock = threading.Lock()
    
    def load(self) -> Dict[str, StateEntry]:
        """Load from JSON file."""
        if not self._file_path.exists():
            return {}
        
        try:
            with self._lock:
                content = self._file_path.read_text(encoding='utf-8')
                if not content:
                    return {}
                
                data = json.loads(content)
                entries = {}
                
                for key, value in data.get('entries', {}).items():
                    entry_data = value
                    entry_data['created_at'] = datetime.fromisoformat(entry_data['created_at'])
                    entry_data['updated_at'] = datetime.fromisoformat(entry_data['updated_at'])
                    entry_data['accessed_at'] = datetime.fromisoformat(entry_data['accessed_at'])
                    entry_data['scope'] = StateScope(entry_data.get('scope', 'global'))
                    
                    entries[key] = StateEntry(**entry_data)
                
                return entries
                
        except Exception as e:
            logger.error(f"Failed to load JSON state: {e}")
            return {}
    
    def save(self, entries: Dict[str, StateEntry]):
        """Save to JSON file."""
        try:
            data = {
                'version': 1,
                'updated_at': datetime.now().isoformat(),
                'entries': {}
            }
            
            for key, entry in entries.items():
                data['entries'][key] = {
                    'key': entry.key,
                    'value': entry.value,
                    'created_at': entry.created_at.isoformat(),
                    'updated_at': entry.updated_at.isoformat(),
                    'accessed_at': entry.accessed_at.isoformat(),
                    'access_count': entry.access_count,
                    'ttl': entry.ttl,
                    'scope': entry.scope.value,
                    'version': entry.version,
                    'metadata': entry.metadata
                }
            
            content = json.dumps(data, indent=2, default=str, ensure_ascii=False)
            
            # Atomic write
            with tempfile.NamedTemporaryFile(
                mode='w', encoding='utf-8', dir=self._file_path.parent, delete=False
            ) as tmp:
                tmp.write(content)
                tmp_path = Path(tmp.name)
            
            with self._lock:
                tmp_path.replace(self._file_path)
                
        except Exception as e:
            logger.error(f"Failed to save JSON state: {e}")


class SQLiteStorageBackend(StorageBackendBase):
    """SQLite storage backend."""
    
    def __init__(self, config: StateConfig):
        super().__init__(config)
        self._db_path = config.directory / f"{config.scope.value}_state.db"
        self._conn: Optional[sqlite3.Connection] = None
        self._lock = threading.Lock()
        self._init_db()
    
    def _init_db(self):
        """Initialize database."""
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    accessed_at TEXT NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    ttl INTEGER,
                    scope TEXT DEFAULT 'global',
                    version INTEGER DEFAULT 1,
                    metadata TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_scope ON state(scope)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_updated ON state(updated_at)")
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Get database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(
                str(self._db_path),
                check_same_thread=False,
                timeout=10.0
            )
            self._conn.row_factory = sqlite3.Row
        
        try:
            yield self._conn
        finally:
            pass
    
    def load(self) -> Dict[str, StateEntry]:
        """Load from SQLite."""
        entries = {}
        
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("SELECT * FROM state")
                
                for row in cursor.fetchall():
                    entry = StateEntry(
                        key=row['key'],
                        value=json.loads(row['value']),
                        created_at=datetime.fromisoformat(row['created_at']),
                        updated_at=datetime.fromisoformat(row['updated_at']),
                        accessed_at=datetime.fromisoformat(row['accessed_at']),
                        access_count=row['access_count'],
                        ttl=row['ttl'],
                        scope=StateScope(row['scope']),
                        version=row['version'],
                        metadata=json.loads(row['metadata']) if row['metadata'] else {}
                    )
                    entries[entry.key] = entry
                
        except Exception as e:
            logger.error(f"Failed to load SQLite state: {e}")
        
        return entries
    
    def save(self, entries: Dict[str, StateEntry]):
        """Save to SQLite."""
        try:
            with self._get_connection() as conn:
                for key, entry in entries.items():
                    conn.execute("""
                        INSERT OR REPLACE INTO state 
                        (key, value, created_at, updated_at, accessed_at, 
                         access_count, ttl, scope, version, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        key,
                        json.dumps(entry.value, default=str),
                        entry.created_at.isoformat(),
                        entry.updated_at.isoformat(),
                        entry.accessed_at.isoformat(),
                        entry.access_count,
                        entry.ttl,
                        entry.scope.value,
                        entry.version,
                        json.dumps(entry.metadata)
                    ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to save SQLite state: {e}")
    
    def close(self):
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None


class MemoryStorageBackend(StorageBackendBase):
    """In-memory storage backend."""
    
    def __init__(self, config: StateConfig):
        super().__init__(config)
        self._entries: Dict[str, StateEntry] = {}
        self._lock = threading.Lock()
    
    def load(self) -> Dict[str, StateEntry]:
        """Load from memory."""
        with self._lock:
            return self._entries.copy()
    
    def save(self, entries: Dict[str, StateEntry]):
        """Save to memory."""
        with self._lock:
            # Evict old entries if over limit
            if len(entries) > self.config.max_memory_entries:
                sorted_entries = sorted(
                    entries.values(),
                    key=lambda e: e.accessed_at
                )
                for entry in sorted_entries[:len(entries) - self.config.max_memory_entries]:
                    del entries[entry.key]
            
            self._entries = entries


# ============================================================
# MAIN STATE MANAGER
# ============================================================

class StateManager:
    """
    Persistent state management for the AI development framework.
    
    Features:
    - Multiple storage backends (JSON, SQLite, Pickle, Memory)
    - Automatic persistence with configurable intervals
    - TTL (Time To Live) support for entries
    - Snapshots and rollback
    - Backup and restore
    - Compression and encryption
    - Thread-safe operations
    - Lazy loading
    - History tracking
    - Namespace/scoped storage
    - Atomic writes
    """
    
    def __init__(self, directory: Optional[Path] = None, config: Optional[StateConfig] = None):
        """Initialize state manager."""
        if config:
            self.config = config
        else:
            app_config = get_config()
            self.config = StateConfig(
                directory=directory or app_config.state.directory,
                backend=StorageBackend.JSON,
                auto_save=app_config.state.auto_save,
                save_interval=app_config.state.save_interval,
                max_history=app_config.state.max_history,
                compression=CompressionType.NONE,
                encryption=EncryptionType.NONE
            )
        
        self.config.directory = Path(self.config.directory)
        ensure_dir(self.config.directory)
        
        # Initialize backend
        self._backend = self._create_backend()
        
        # State storage
        self._entries: Dict[str, StateEntry] = {}
        self._history: List[StateSnapshot] = []
        self._dirty = False
        self._last_save = datetime.now()
        
        # Thread safety
        self._lock = threading.RLock()
        self._save_timer: Optional[threading.Timer] = None
        
        # Load existing state
        if not self.config.lazy_load:
            self._load()
        
        # Start auto-save timer
        if self.config.auto_save:
            self._schedule_save()
        
        # Start backup timer
        if self.config.backup_enabled:
            self._schedule_backup()
        
        logger.debug(f"StateManager initialized at {self.config.directory}")
    
    def _create_backend(self) -> StorageBackendBase:
        """Create storage backend."""
        if self.config.backend == StorageBackend.JSON:
            return JSONStorageBackend(self.config)
        elif self.config.backend == StorageBackend.SQLITE:
            return SQLiteStorageBackend(self.config)
        elif self.config.backend == StorageBackend.MEMORY:
            return MemoryStorageBackend(self.config)
        else:
            raise ValueError(f"Unsupported backend: {self.config.backend}")
    
    def _load(self):
        """Load state from backend."""
        with self._lock:
            self._entries = self._backend.load()
            self._cleanup_expired()
            logger.debug(f"Loaded {len(self._entries)} state entries")
    
    def _ensure_loaded(self):
        """Ensure state is loaded."""
        if not self._entries and self.config.lazy_load:
            self._load()
    
    def _schedule_save(self):
        """Schedule periodic save."""
        if self._save_timer:
            self._save_timer.cancel()
        
        self._save_timer = threading.Timer(self.config.save_interval, self._auto_save)
        self._save_timer.daemon = True
        self._save_timer.start()
    
    def _auto_save(self):
        """Auto-save callback."""
        if self._dirty:
            self.save()
        self._schedule_save()
    
    def _schedule_backup(self):
        """Schedule periodic backup."""
        timer = threading.Timer(self.config.backup_interval, self._auto_backup)
        timer.daemon = True
        timer.start()
    
    def _auto_backup(self):
        """Auto-backup callback."""
        self.create_backup()
        self._schedule_backup()
    
    def _cleanup_expired(self):
        """Remove expired entries."""
        expired = []
        for key, entry in self._entries.items():
            if entry.is_expired():
                expired.append(key)
        
        for key in expired:
            del self._entries[key]
        
        if expired:
            self._dirty = True
            logger.debug(f"Removed {len(expired)} expired entries")
    
    def _mark_dirty(self):
        """Mark state as dirty."""
        self._dirty = True
        self._last_save = datetime.now()
    
    # ============================================================
    # CRUD OPERATIONS
    # ============================================================
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a state value.
        
        Args:
            key: State key
            default: Default value if key not found
            
        Returns:
            Stored value or default
        """
        self._ensure_loaded()
        
        with self._lock:
            entry = self._entries.get(key)
            
            if entry is None:
                return default
            
            if entry.is_expired():
                del self._entries[key]
                self._dirty = True
                return default
            
            entry.touch()
            return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None,
            metadata: Optional[Dict[str, Any]] = None):
        """
        Set a state value.
        
        Args:
            key: State key
            value: Value to store
            ttl: Time to live in seconds
            metadata: Additional metadata
        """
        self._ensure_loaded()
        
        with self._lock:
            now = datetime.now()
            
            if key in self._entries:
                entry = self._entries[key]
                entry.value = value
                entry.updated_at = now
                entry.version += 1
                if ttl is not None:
                    entry.ttl = ttl
                if metadata:
                    entry.metadata.update(metadata)
            else:
                entry = StateEntry(
                    key=key,
                    value=value,
                    created_at=now,
                    updated_at=now,
                    accessed_at=now,
                    ttl=ttl or self.config.default_ttl,
                    scope=self.config.scope,
                    metadata=metadata or {}
                )
                self._entries[key] = entry
            
            self._mark_dirty()
    
    def update(self, data: Dict[str, Any], ttl: Optional[int] = None):
        """
        Update multiple state values.
        
        Args:
            data: Dictionary of key-value pairs
            ttl: Time to live for new entries
        """
        for key, value in data.items():
            self.set(key, value, ttl)
    
    def delete(self, key: str) -> bool:
        """
        Delete a state value.
        
        Args:
            key: State key
            
        Returns:
            True if deleted, False if not found
        """
        self._ensure_loaded()
        
        with self._lock:
            if key in self._entries:
                del self._entries[key]
                self._mark_dirty()
                return True
            return False
    
    def delete_many(self, keys: List[str]) -> int:
        """
        Delete multiple state values.
        
        Args:
            keys: List of state keys
            
        Returns:
            Number of deleted entries
        """
        self._ensure_loaded()
        
        with self._lock:
            count = 0
            for key in keys:
                if key in self._entries:
                    del self._entries[key]
                    count += 1
            
            if count > 0:
                self._mark_dirty()
            
            return count
    
    def exists(self, key: str) -> bool:
        """
        Check if key exists.
        
        Args:
            key: State key
            
        Returns:
            True if key exists and not expired
        """
        self._ensure_loaded()
        
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return False
            if entry.is_expired():
                del self._entries[key]
                self._dirty = True
                return False
            return True
    
    def get_all(self, prefix: Optional[str] = None) -> Dict[str, Any]:
        """
        Get all state values.
        
        Args:
            prefix: Filter keys by prefix
            
        Returns:
            Dictionary of key-value pairs
        """
        self._ensure_loaded()
        
        with self._lock:
            self._cleanup_expired()
            
            if prefix:
                return {
                    k: v.value for k, v in self._entries.items()
                    if k.startswith(prefix)
                }
            else:
                return {k: v.value for k, v in self._entries.items()}
    
    def keys(self, pattern: Optional[str] = None) -> List[str]:
        """
        Get all keys.
        
        Args:
            pattern: Filter keys by pattern (supports * wildcard)
            
        Returns:
            List of keys
        """
        self._ensure_loaded()
        
        with self._lock:
            self._cleanup_expired()
            
            if pattern:
                import fnmatch
                return [k for k in self._entries.keys() if fnmatch.fnmatch(k, pattern)]
            else:
                return list(self._entries.keys())
    
    def clear(self):
        """Clear all state values."""
        with self._lock:
            self._entries.clear()
            self._mark_dirty()
    
    def get_metadata(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get entry metadata.
        
        Args:
            key: State key
            
        Returns:
            Metadata dictionary or None
        """
        self._ensure_loaded()
        
        with self._lock:
            entry = self._entries.get(key)
            if entry and not entry.is_expired():
                return entry.metadata.copy()
            return None
    
    def touch(self, key: str) -> bool:
        """
        Update access time for a key.
        
        Args:
            key: State key
            
        Returns:
            True if touched, False if not found
        """
        self._ensure_loaded()
        
        with self._lock:
            entry = self._entries.get(key)
            if entry and not entry.is_expired():
                entry.touch()
                self._mark_dirty()
                return True
            return False
    
    def increment(self, key: str, amount: int = 1) -> int:
        """
        Increment a numeric value.
        
        Args:
            key: State key
            amount: Amount to increment
            
        Returns:
            New value
        """
        self._ensure_loaded()
        
        with self._lock:
            entry = self._entries.get(key)
            if entry and not entry.is_expired():
                if isinstance(entry.value, (int, float)):
                    entry.value += amount
                else:
                    entry.value = amount
                entry.updated_at = datetime.now()
                entry.version += 1
            else:
                entry = StateEntry(
                    key=key,
                    value=amount,
                    scope=self.config.scope
                )
                self._entries[key] = entry
            
            self._mark_dirty()
            return entry.value
    
    def append(self, key: str, value: Any) -> List[Any]:
        """
        Append to a list value.
        
        Args:
            key: State key
            value: Value to append
            
        Returns:
            Updated list
        """
        self._ensure_loaded()
        
        with self._lock:
            entry = self._entries.get(key)
            if entry and not entry.is_expired():
                if isinstance(entry.value, list):
                    entry.value.append(value)
                else:
                    entry.value = [entry.value, value] if entry.value is not None else [value]
                entry.updated_at = datetime.now()
                entry.version += 1
            else:
                entry = StateEntry(
                    key=key,
                    value=[value],
                    scope=self.config.scope
                )
                self._entries[key] = entry
            
            self._mark_dirty()
            return entry.value
    
    # ============================================================
    # PERSISTENCE OPERATIONS
    # ============================================================
    
    def save(self, force: bool = False):
        """
        Save state to storage.
        
        Args:
            force: Force save even if not dirty
        """
        if not force and not self._dirty:
            return
        
        with self._lock:
            self._cleanup_expired()
            
            try:
                self._backend.save(self._entries)
                self._dirty = False
                logger.debug(f"Saved {len(self._entries)} state entries")
            except Exception as e:
                logger.error(f"Failed to save state: {e}")
                raise
    
    def load(self, force: bool = False):
        """
        Load state from storage.
        
        Args:
            force: Force load even if already loaded
        """
        if force or self.config.lazy_load:
            with self._lock:
                self._entries = self._backend.load()
                self._cleanup_expired()
                self._dirty = False
                logger.debug(f"Loaded {len(self._entries)} state entries")
    
    def reload(self):
        """Reload state from storage, discarding changes."""
        self.load(force=True)
    
    def flush(self):
        """Force save and clear memory if using lazy load."""
        self.save(force=True)
        if self.config.lazy_load:
            with self._lock:
                self._entries.clear()
    
    # ============================================================
    # SNAPSHOT OPERATIONS
    # ============================================================
    
    def create_snapshot(self, description: Optional[str] = None) -> str:
        """
        Create a state snapshot.
        
        Args:
            description: Snapshot description
            
        Returns:
            Snapshot ID
        """
        with self._lock:
            snapshot_id = hashlib.md5(
                f"{datetime.now().isoformat()}:{len(self._history)}".encode()
            ).hexdigest()[:12]
            
            snapshot = StateSnapshot(
                id=snapshot_id,
                description=description,
                data={k: v.value for k, v in self._entries.items()}
            )
            
            self._history.append(snapshot)
            
            # Trim history
            if len(self._history) > self.config.max_history:
                self._history = self._history[-self.config.max_history:]
            
            # Save snapshot to disk
            snapshot_file = self.config.directory / "snapshots" / f"{snapshot_id}.json"
            snapshot_file.parent.mkdir(parents=True, exist_ok=True)
            
            snapshot_data = {
                'id': snapshot.id,
                'created_at': snapshot.created_at.isoformat(),
                'description': snapshot.description,
                'data': snapshot.data,
                'metadata': snapshot.metadata
            }
            
            with open(snapshot_file, 'w', encoding='utf-8') as f:
                json.dump(snapshot_data, f, indent=2, default=str)
            
            logger.info(f"Created snapshot {snapshot_id}: {description or 'No description'}")
            return snapshot_id
    
    def restore_snapshot(self, snapshot_id: str) -> bool:
        """
        Restore from a snapshot.
        
        Args:
            snapshot_id: Snapshot ID
            
        Returns:
            True if restored successfully
        """
        # Check in-memory history
        for snapshot in self._history:
            if snapshot.id == snapshot_id:
                with self._lock:
                    self._entries.clear()
                    for key, value in snapshot.data.items():
                        self._entries[key] = StateEntry(
                            key=key,
                            value=value,
                            scope=self.config.scope
                        )
                    self._mark_dirty()
                    self.save()
                logger.info(f"Restored snapshot {snapshot_id}")
                return True
        
        # Check disk
        snapshot_file = self.config.directory / "snapshots" / f"{snapshot_id}.json"
        if snapshot_file.exists():
            try:
                with open(snapshot_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                with self._lock:
                    self._entries.clear()
                    for key, value in data['data'].items():
                        self._entries[key] = StateEntry(
                            key=key,
                            value=value,
                            scope=self.config.scope
                        )
                    self._mark_dirty()
                    self.save()
                
                logger.info(f"Restored snapshot {snapshot_id} from disk")
                return True
                
            except Exception as e:
                logger.error(f"Failed to restore snapshot: {e}")
                return False
        
        logger.warning(f"Snapshot not found: {snapshot_id}")
        return False
    
    def list_snapshots(self) -> List[Dict[str, Any]]:
        """
        List all snapshots.
        
        Returns:
            List of snapshot info
        """
        snapshots = []
        
        # In-memory snapshots
        for snapshot in self._history:
            snapshots.append({
                'id': snapshot.id,
                'created_at': snapshot.created_at,
                'description': snapshot.description,
                'entries': len(snapshot.data),
                'source': 'memory'
            })
        
        # Disk snapshots
        snapshots_dir = self.config.directory / "snapshots"
        if snapshots_dir.exists():
            for snapshot_file in snapshots_dir.glob("*.json"):
                try:
                    with open(snapshot_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    snapshots.append({
                        'id': data['id'],
                        'created_at': datetime.fromisoformat(data['created_at']),
                        'description': data.get('description'),
                        'entries': len(data['data']),
                        'source': 'disk'
                    })
                except Exception:
                    pass
        
        return sorted(snapshots, key=lambda s: s['created_at'], reverse=True)
    
    def delete_snapshot(self, snapshot_id: str) -> bool:
        """
        Delete a snapshot.
        
        Args:
            snapshot_id: Snapshot ID
            
        Returns:
            True if deleted
        """
        # Remove from memory
        self._history = [s for s in self._history if s.id != snapshot_id]
        
        # Remove from disk
        snapshot_file = self.config.directory / "snapshots" / f"{snapshot_id}.json"
        if snapshot_file.exists():
            snapshot_file.unlink()
            return True
        
        return False
    
    # ============================================================
    # BACKUP OPERATIONS
    # ============================================================
    
    def create_backup(self) -> Optional[Path]:
        """
        Create a backup of current state.
        
        Returns:
            Path to backup file
        """
        self.save()
        
        backup_dir = self.config.directory / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"state_backup_{timestamp}.json"
        
        try:
            # Find state file
            state_file = self.config.directory / f"{self.config.scope.value}_state.json"
            
            if state_file.exists():
                shutil.copy2(state_file, backup_file)
                
                # Cleanup old backups
                backups = sorted(backup_dir.glob("state_backup_*.json"))
                if len(backups) > self.config.max_backups:
                    for old_backup in backups[:-self.config.max_backups]:
                        old_backup.unlink()
                
                logger.info(f"Created backup: {backup_file}")
                return backup_file
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
        
        return None
    
    def restore_backup(self, backup_path: Path) -> bool:
        """
        Restore from a backup.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            True if restored successfully
        """
        if not backup_path.exists():
            logger.error(f"Backup not found: {backup_path}")
            return False
        
        state_file = self.config.directory / f"{self.config.scope.value}_state.json"
        
        try:
            shutil.copy2(backup_path, state_file)
            self.load(force=True)
            logger.info(f"Restored from backup: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False
    
    def list_backups(self) -> List[Path]:
        """
        List available backups.
        
        Returns:
            List of backup file paths
        """
        backup_dir = self.config.directory / "backups"
        if not backup_dir.exists():
            return []
        
        backups = sorted(backup_dir.glob("state_backup_*.json"), reverse=True)
        return backups
    
    # ============================================================
    # TRANSACTION OPERATIONS
    # ============================================================
    
    @contextmanager
    def transaction(self):
        """
        Context manager for atomic transactions.
        
        Usage:
            with state.transaction():
                state.set("key1", "value1")
                state.set("key2", "value2")
        """
        snapshot_id = self.create_snapshot("transaction_start")
        
        try:
            yield
            self.save()
        except Exception as e:
            logger.error(f"Transaction failed, rolling back: {e}")
            self.restore_snapshot(snapshot_id)
            raise
        finally:
            self.delete_snapshot(snapshot_id)
    
    # ============================================================
    # NAMESPACE OPERATIONS
    # ============================================================
    
    def namespace(self, prefix: str) -> 'StateNamespace':
        """
        Get a namespaced state manager.
        
        Args:
            prefix: Namespace prefix
            
        Returns:
            StateNamespace instance
        """
        return StateNamespace(self, prefix)
    
    # ============================================================
    # UTILITY METHODS
    # ============================================================
    
    def export(self, output_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Export state to dictionary.
        
        Args:
            output_path: Optional path to save JSON file
            
        Returns:
            Dictionary of state data
        """
        self._ensure_loaded()
        
        with self._lock:
            data = {
                'exported_at': datetime.now().isoformat(),
                'config': {
                    'scope': self.config.scope.value,
                    'backend': self.config.backend.value
                },
                'entries': {}
            }
            
            for key, entry in self._entries.items():
                if not entry.is_expired():
                    data['entries'][key] = {
                        'value': entry.value,
                        'created_at': entry.created_at.isoformat(),
                        'updated_at': entry.updated_at.isoformat(),
                        'ttl': entry.ttl,
                        'metadata': entry.metadata
                    }
            
            if output_path:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, default=str)
                logger.info(f"Exported state to {output_path}")
            
            return data
    
    def import_state(self, data: Dict[str, Any], merge: bool = False):
        """
        Import state from dictionary.
        
        Args:
            data: State data dictionary
            merge: If True, merge with existing state
        """
        if not merge:
            self.clear()
        
        with self._lock:
            for key, entry_data in data.get('entries', {}).items():
                self._entries[key] = StateEntry(
                    key=key,
                    value=entry_data['value'],
                    created_at=datetime.fromisoformat(entry_data['created_at']),
                    updated_at=datetime.fromisoformat(entry_data['updated_at']),
                    ttl=entry_data.get('ttl'),
                    metadata=entry_data.get('metadata', {})
                )
            
            self._mark_dirty()
            self.save()
        
        logger.info(f"Imported {len(data.get('entries', {}))} state entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get state statistics.
        
        Returns:
            Statistics dictionary
        """
        self._ensure_loaded()
        
        with self._lock:
            total_entries = len(self._entries)
            expired = sum(1 for e in self._entries.values() if e.is_expired())
            total_size = sum(len(json.dumps(e.value, default=str)) for e in self._entries.values())
            
            by_scope = {}
            for entry in self._entries.values():
                scope = entry.scope.value
                by_scope[scope] = by_scope.get(scope, 0) + 1
            
            return {
                'total_entries': total_entries,
                'expired_entries': expired,
                'active_entries': total_entries - expired,
                'estimated_size_bytes': total_size,
                'by_scope': by_scope,
                'dirty': self._dirty,
                'last_save': self._last_save.isoformat() if self._last_save else None,
                'history_count': len(self._history)
            }
    
    def close(self):
        """Close state manager and save pending changes."""
        if self._save_timer:
            self._save_timer.cancel()
        
        self.save()
        self._backend.close()
        logger.debug("StateManager closed")


# ============================================================
# STATE NAMESPACE
# ============================================================

class StateNamespace:
    """Namespaced state manager."""
    
    def __init__(self, manager: StateManager, prefix: str):
        self._manager = manager
        self._prefix = prefix.rstrip(':') + ':'
    
    def _key(self, key: str) -> str:
        """Build namespaced key."""
        return f"{self._prefix}{key}"
    
    def get(self, key: str, default: Any = None) -> Any:
        return self._manager.get(self._key(key), default)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        self._manager.set(self._key(key), value, ttl)
    
    def delete(self, key: str) -> bool:
        return self._manager.delete(self._key(key))
    
    def exists(self, key: str) -> bool:
        return self._manager.exists(self._key(key))
    
    def get_all(self) -> Dict[str, Any]:
        prefix_len = len(self._prefix)
        all_data = self._manager.get_all(self._prefix)
        return {k[prefix_len:]: v for k, v in all_data.items()}
    
    def keys(self) -> List[str]:
        prefix_len = len(self._prefix)
        return [k[prefix_len:] for k in self._manager.keys(f"{self._prefix}*")]
    
    def clear(self):
        for key in self.keys():
            self.delete(key)
    
    def namespace(self, sub_prefix: str) -> 'StateNamespace':
        return StateNamespace(self._manager, f"{self._prefix}{sub_prefix}")


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for state manager."""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="State management utilities")
    parser.add_argument("--dir", type=Path, default=Path(".ai_state"), help="State directory")
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Get command
    get_parser = subparsers.add_parser('get', help='Get a value')
    get_parser.add_argument('key', help='State key')
    get_parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    # Set command
    set_parser = subparsers.add_parser('set', help='Set a value')
    set_parser.add_argument('key', help='State key')
    set_parser.add_argument('value', help='Value to set')
    set_parser.add_argument('--ttl', type=int, help='Time to live in seconds')
    
    # Delete command
    del_parser = subparsers.add_parser('delete', help='Delete a value')
    del_parser.add_argument('key', help='State key')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all keys')
    list_parser.add_argument('--pattern', default='*', help='Key pattern')
    
    # Stats command
    subparsers.add_parser('stats', help='Show statistics')
    
    # Snapshot command
    snapshot_parser = subparsers.add_parser('snapshot', help='Snapshot operations')
    snapshot_parser.add_argument('--create', action='store_true', help='Create snapshot')
    snapshot_parser.add_argument('--list', action='store_true', help='List snapshots')
    snapshot_parser.add_argument('--restore', help='Restore snapshot')
    snapshot_parser.add_argument('--description', help='Snapshot description')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export state')
    export_parser.add_argument('--output', '-o', type=Path, help='Output file')
    
    # Import command
    import_parser = subparsers.add_parser('import', help='Import state')
    import_parser.add_argument('file', type=Path, help='Input file')
    import_parser.add_argument('--merge', action='store_true', help='Merge with existing')
    
    args = parser.parse_args()
    
    manager = StateManager(directory=args.dir)
    
    if args.command == 'get':
        value = manager.get(args.key)
        if value is None:
            print("Not found")
            sys.exit(1)
        elif args.json:
            print(json.dumps(value, indent=2, default=str))
        else:
            print(value)
    
    elif args.command == 'set':
        # Try to parse as JSON
        try:
            value = json.loads(args.value)
        except json.JSONDecodeError:
            value = args.value
        
        manager.set(args.key, value, ttl=args.ttl)
        manager.save()
        print(f"Set {args.key}")
    
    elif args.command == 'delete':
        if manager.delete(args.key):
            print(f"Deleted {args.key}")
        else:
            print("Not found")
            sys.exit(1)
    
    elif args.command == 'list':
        keys = manager.keys(args.pattern)
        for key in keys:
            print(key)
        print(f"\nTotal: {len(keys)} keys")
    
    elif args.command == 'stats':
        stats = manager.get_stats()
        print(json.dumps(stats, indent=2, default=str))
    
    elif args.command == 'snapshot':
        if args.create:
            snapshot_id = manager.create_snapshot(args.description)
            print(f"Created snapshot: {snapshot_id}")
        elif args.list:
            snapshots = manager.list_snapshots()
            for s in snapshots:
                print(f"{s['id']}: {s['created_at']} - {s.get('description', 'No description')} ({s['entries']} entries)")
        elif args.restore:
            if manager.restore_snapshot(args.restore):
                print(f"Restored snapshot: {args.restore}")
            else:
                print("Snapshot not found")
                sys.exit(1)
    
    elif args.command == 'export':
        data = manager.export(args.output)
        if not args.output:
            print(json.dumps(data, indent=2, default=str))
        else:
            print(f"Exported to {args.output}")
    
    elif args.command == 'import':
        with open(args.file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        manager.import_state(data, merge=args.merge)
        print(f"Imported from {args.file}")
    
    else:
        parser.print_help()
    
    manager.close()


if __name__ == "__main__":
    main()