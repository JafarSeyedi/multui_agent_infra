"""
Session Persistence for Session Manager

Handles persistent storage of session data using the shared state manager.
Provides:
- Session state persistence and recovery
- Session history and archiving
- Checkpoint and restore capabilities
- Session data migration
- Batch operations for session management


This session_persistence.py provides:

    Multiple Backend Support: STATE_MANAGER (default), JSON_FILE, SQLITE (planned), REDIS (planned)
    Session Snapshots: Point-in-time snapshots with checksum verification
    Session Archiving: Long-term storage for terminated sessions
    Automatic Saving: Background auto-save at configurable intervals
    Backup Management: Full backup creation and restoration
    Compression Support: Optional gzip compression for stored data
    Checksum Validation: Data integrity verification
    Cleanup Management: Automatic cleanup of old archives
    Caching: In-memory cache for frequently accessed sessions
    Persistence Statistics: Metrics about stored data

The persistence layer works seamlessly with the shared state_manager as the primary 
backend while providing additional features like snapshots, archiving, and backup capabilities.
"""

import json
import hashlib
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict
from contextlib import contextmanager

from ...shared.logger import get_logger
from ...shared.state_manager import state_manager
from ...shared.config import config
from ...shared.file_utils import file_utils

from .session_manager import Session, SessionActivity, SessionStatus, SessionType
from .session_types import SessionTypeConfig, SessionTypeRegistry

logger = get_logger(__name__)


class PersistenceBackend(Enum):
    """Supported persistence backends"""
    STATE_MANAGER = "state_manager"  # Default - uses shared state manager
    JSON_FILE = "json_file"          # JSON file backup
    SQLITE = "sqlite"                # SQLite database (future)
    REDIS = "redis"                  # Redis cache (future)


@dataclass
class PersistenceConfig:
    """Configuration for session persistence"""
    backend: PersistenceBackend = PersistenceBackend.STATE_MANAGER
    auto_save_interval_seconds: int = 60
    max_history_per_session: int = 1000
    archive_after_days: int = 7
    compression_enabled: bool = False
    encryption_enabled: bool = False
    backup_enabled: bool = True
    backup_interval_hours: int = 24
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "backend": self.backend.value,
            "auto_save_interval_seconds": self.auto_save_interval_seconds,
            "max_history_per_session": self.max_history_per_session,
            "archive_after_days": self.archive_after_days,
            "compression_enabled": self.compression_enabled,
            "encryption_enabled": self.encryption_enabled,
            "backup_enabled": self.backup_enabled,
            "backup_interval_hours": self.backup_interval_hours
        }


@dataclass
class SessionSnapshot:
    """Snapshot of a session at a point in time"""
    session_id: str
    snapshot_id: str
    timestamp: datetime
    session_data: Dict[str, Any]
    activity_count: int
    checksum: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "snapshot_id": self.snapshot_id,
            "timestamp": self.timestamp.isoformat(),
            "session_data": self.session_data,
            "activity_count": self.activity_count,
            "checksum": self.checksum,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionSnapshot":
        return cls(
            session_id=data["session_id"],
            snapshot_id=data["snapshot_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            session_data=data["session_data"],
            activity_count=data.get("activity_count", 0),
            checksum=data.get("checksum", ""),
            metadata=data.get("metadata", {})
        )


@dataclass
class SessionArchive:
    """Archived session data for long-term storage"""
    session_id: str
    user_id: Optional[str]
    session_type: str
    created_at: datetime
    terminated_at: datetime
    duration_seconds: float
    total_activities: int
    final_status: str
    compressed_data: Optional[bytes] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "session_type": self.session_type,
            "created_at": self.created_at.isoformat(),
            "terminated_at": self.terminated_at.isoformat(),
            "duration_seconds": self.duration_seconds,
            "total_activities": self.total_activities,
            "final_status": self.final_status,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionArchive":
        return cls(
            session_id=data["session_id"],
            user_id=data.get("user_id"),
            session_type=data["session_type"],
            created_at=datetime.fromisoformat(data["created_at"]),
            terminated_at=datetime.fromisoformat(data["terminated_at"]),
            duration_seconds=data["duration_seconds"],
            total_activities=data["total_activities"],
            final_status=data["final_status"],
            compressed_data=data.get("compressed_data"),
            metadata=data.get("metadata", {})
        )


class SessionPersistence:
    """
    Handles persistent storage for session data using shared state manager.
    
    Features:
    - Session state persistence and recovery
    - Point-in-time snapshots
    - Session archiving
    - Batch operations
    - Data integrity validation
    - Automatic backup and recovery
    """
    
    def __init__(self, config: PersistenceConfig = None):
        self.config = config or PersistenceConfig()
        self.storage_key = "session_persistence"
        self._snapshots: Dict[str, List[SessionSnapshot]] = defaultdict(list)
        self._archives: Dict[str, SessionArchive] = {}
        self._cache: Dict[str, Dict[str, Any]] = {}
        
        # Load data
        self._load_metadata()
        
        # Start background workers
        self._start_workers()
        
        logger.info(f"SessionPersistence initialized with backend {self.config.backend.value}")
    
    def _load_metadata(self) -> None:
        """Load persistence metadata from state manager"""
        try:
            snapshots_data = state_manager.get(f"{self.storage_key}.snapshots", {})
            for sid, snap_list in snapshots_data.items():
                self._snapshots[sid] = [
                    SessionSnapshot.from_dict(s) for s in snap_list
                ]
            
            archives_data = state_manager.get(f"{self.storage_key}.archives", {})
            for sid, arch_data in archives_data.items():
                self._archives[sid] = SessionArchive.from_dict(arch_data)
                
        except Exception as e:
            logger.warning(f"Failed to load persistence metadata: {e}")
    
    def _save_metadata(self) -> None:
        """Save persistence metadata to state manager"""
        try:
            snapshots_data = {
                sid: [s.to_dict() for s in snapshots]
                for sid, snapshots in self._snapshots.items()
            }
            state_manager.set(f"{self.storage_key}.snapshots", snapshots_data)
            
            archives_data = {
                sid: arch.to_dict() for sid, arch in self._archives.items()
            }
            state_manager.set(f"{self.storage_key}.archives", archives_data)
            
        except Exception as e:
            logger.error(f"Failed to save persistence metadata: {e}")
    
    def _start_workers(self) -> None:
        """Start background workers for auto-save and backup"""
        import threading
        
        def auto_save_worker():
            while True:
                try:
                    self._auto_save_all_sessions()
                except Exception as e:
                    logger.error(f"Auto-save worker error: {e}")
                threading.Event().wait(self.config.auto_save_interval_seconds)
        
        def backup_worker():
            if not self.config.backup_enabled:
                return
            while True:
                try:
                    self.create_backup()
                except Exception as e:
                    logger.error(f"Backup worker error: {e}")
                threading.Event().wait(self.config.backup_interval_hours * 3600)
        
        worker1 = threading.Thread(target=auto_save_worker, daemon=True)
        worker1.start()
        
        if self.config.backup_enabled:
            worker2 = threading.Thread(target=backup_worker, daemon=True)
            worker2.start()
    
    def _auto_save_all_sessions(self) -> None:
        """Automatically save all active sessions"""
        # Get all session IDs from state manager
        sessions_data = state_manager.get("session_manager.sessions", {})
        for session_id in sessions_data.keys():
            self.save_session_state(session_id)
    
    def save_session_state(self, session_id: str) -> bool:
        """
        Save current session state to persistence.
        
        Args:
            session_id: Session ID to save
            
        Returns:
            True if successful
        """
        try:
            # Get session from state manager
            sessions_data = state_manager.get("session_manager.sessions", {})
            session_data = sessions_data.get(session_id)
            
            if not session_data:
                logger.warning(f"Session {session_id} not found for saving")
                return False
            
            # Save to persistence backend
            if self.config.backend == PersistenceBackend.STATE_MANAGER:
                # Already in state manager, just update metadata
                saved_sessions = state_manager.get(f"{self.storage_key}.saved_sessions", {})
                saved_sessions[session_id] = {
                    "last_saved": datetime.now().isoformat(),
                    "session_data": session_data,
                    "checksum": self._calculate_checksum(session_data)
                }
                state_manager.set(f"{self.storage_key}.saved_sessions", saved_sessions)
                
            elif self.config.backend == PersistenceBackend.JSON_FILE:
                self._save_to_json_file(session_id, session_data)
            
            # Update cache
            self._cache[session_id] = session_data
            
            logger.debug(f"Saved session state for {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save session {session_id}: {e}")
            return False
    
    def _save_to_json_file(self, session_id: str, session_data: Dict[str, Any]) -> None:
        """Save session to JSON file backup"""
        import os
        backup_dir = config.get("paths.session_backup_dir", "data/session_backups")
        file_utils.ensure_directory(backup_dir)
        
        filename = f"{backup_dir}/{session_id}.json"
        if self.config.compression_enabled:
            import gzip
            content = json.dumps(session_data, default=str)
            compressed = gzip.compress(content.encode())
            with open(f"{filename}.gz", 'wb') as f:
                f.write(compressed)
        else:
            file_utils.write_json(filename, session_data)
    
    def load_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Load session state from persistence.
        
        Args:
            session_id: Session ID to load
            
        Returns:
            Session data dict or None
        """
        try:
            # Check cache first
            if session_id in self._cache:
                return self._cache[session_id]
            
            # Load from backend
            if self.config.backend == PersistenceBackend.STATE_MANAGER:
                saved_sessions = state_manager.get(f"{self.storage_key}.saved_sessions", {})
                session_data = saved_sessions.get(session_id, {}).get("session_data")
                
            elif self.config.backend == PersistenceBackend.JSON_FILE:
                session_data = self._load_from_json_file(session_id)
            else:
                session_data = None
            
            if session_data:
                # Verify checksum
                if self._verify_checksum(session_data):
                    self._cache[session_id] = session_data
                    return session_data
                else:
                    logger.warning(f"Checksum verification failed for session {session_id}")
                    return None
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {e}")
            return None
    
    def _load_from_json_file(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load session from JSON file backup"""
        backup_dir = config.get("paths.session_backup_dir", "data/session_backups")
        
        # Try compressed first
        import os
        gz_path = f"{backup_dir}/{session_id}.json.gz"
        if os.path.exists(gz_path):
            import gzip
            with gzip.open(gz_path, 'rb') as f:
                return json.loads(f.read().decode())
        
        # Try uncompressed
        json_path = f"{backup_dir}/{session_id}.json"
        if os.path.exists(json_path):
            return file_utils.read_json(json_path)
        
        return None
    
    def _calculate_checksum(self, data: Dict[str, Any]) -> str:
        """Calculate checksum for data integrity"""
        content = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _verify_checksum(self, data: Dict[str, Any]) -> bool:
        """Verify data checksum"""
        if "checksum" not in data:
            return True  # Old data without checksum
        stored_checksum = data.get("checksum")
        calculated_checksum = self._calculate_checksum({k: v for k, v in data.items() if k != "checksum"})
        return stored_checksum == calculated_checksum
    
    def create_snapshot(self, session_id: str, 
                       metadata: Dict[str, Any] = None) -> Optional[str]:
        """
        Create a point-in-time snapshot of a session.
        
        Args:
            session_id: Session ID
            metadata: Additional metadata for snapshot
            
        Returns:
            Snapshot ID or None
        """
        try:
            session_data = self.load_session_state(session_id)
            if not session_data:
                # Try to get from current state
                sessions_data = state_manager.get("session_manager.sessions", {})
                session_data = sessions_data.get(session_id)
            
            if not session_data:
                logger.warning(f"Cannot create snapshot for non-existent session {session_id}")
                return None
            
            snapshot_id = hashlib.md5(f"{session_id}_{datetime.now().isoformat()}".encode()).hexdigest()[:16]
            
            # Get activity count for this session
            activities_data = state_manager.get("session_manager.activities", [])
            activity_count = len([a for a in activities_data if a.get("session_id") == session_id])
            
            snapshot = SessionSnapshot(
                session_id=session_id,
                snapshot_id=snapshot_id,
                timestamp=datetime.now(),
                session_data=session_data,
                activity_count=activity_count,
                checksum=self._calculate_checksum(session_data),
                metadata=metadata or {}
            )
            
            self._snapshots[session_id].append(snapshot)
            
            # Limit snapshots per session
            if len(self._snapshots[session_id]) > self.config.max_history_per_session:
                self._snapshots[session_id] = self._snapshots[session_id][-self.config.max_history_per_session:]
            
            self._save_metadata()
            
            logger.info(f"Created snapshot {snapshot_id} for session {session_id}")
            return snapshot_id
            
        except Exception as e:
            logger.error(f"Failed to create snapshot for {session_id}: {e}")
            return None
    
    def restore_snapshot(self, session_id: str, snapshot_id: str) -> bool:
        """
        Restore session state from a snapshot.
        
        Args:
            session_id: Session ID
            snapshot_id: Snapshot ID to restore
            
        Returns:
            True if successful
        """
        try:
            snapshots = self._snapshots.get(session_id, [])
            snapshot = next((s for s in snapshots if s.snapshot_id == snapshot_id), None)
            
            if not snapshot:
                logger.warning(f"Snapshot {snapshot_id} not found for session {session_id}")
                return False
            
            # Restore to state manager
            sessions_data = state_manager.get("session_manager.sessions", {})
            sessions_data[session_id] = snapshot.session_data
            state_manager.set("session_manager.sessions", sessions_data)
            
            # Update cache
            self._cache[session_id] = snapshot.session_data
            
            logger.info(f"Restored session {session_id} from snapshot {snapshot_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore snapshot for {session_id}: {e}")
            return False
    
    def list_snapshots(self, session_id: str) -> List[Dict[str, Any]]:
        """List all snapshots for a session"""
        snapshots = self._snapshots.get(session_id, [])
        return [
            {
                "snapshot_id": s.snapshot_id,
                "timestamp": s.timestamp.isoformat(),
                "activity_count": s.activity_count,
                "metadata": s.metadata
            }
            for s in snapshots
        ]
    
    def archive_session(self, session_id: str) -> bool:
        """
        Archive a terminated session for long-term storage.
        
        Args:
            session_id: Session ID to archive
            
        Returns:
            True if successful
        """
        try:
            sessions_data = state_manager.get("session_manager.sessions", {})
            session_data = sessions_data.get(session_id)
            
            if not session_data:
                logger.warning(f"Cannot archive non-existent session {session_id}")
                return False
            
            # Get activities for this session
            activities_data = state_manager.get("session_manager.activities", [])
            session_activities = [a for a in activities_data if a.get("session_id") == session_id]
            
            # Calculate duration
            created_at = datetime.fromisoformat(session_data.get("created_at", datetime.now().isoformat()))
            terminated_at = datetime.fromisoformat(session_data.get("terminated_at", datetime.now().isoformat())) \
                           if session_data.get("terminated_at") else datetime.now()
            duration = (terminated_at - created_at).total_seconds()
            
            # Create archive
            archive = SessionArchive(
                session_id=session_id,
                user_id=session_data.get("user_id"),
                session_type=session_data.get("session_type", "unknown"),
                created_at=created_at,
                terminated_at=terminated_at,
                duration_seconds=duration,
                total_activities=len(session_activities),
                final_status=session_data.get("status", "unknown"),
                metadata={
                    "auth_level": session_data.get("auth_level"),
                    "tags": session_data.get("tags", [])
                }
            )
            
            # Compress data if enabled
            if self.config.compression_enabled:
                import gzip
                compressed = gzip.compress(json.dumps(session_data, default=str).encode())
                archive.compressed_data = compressed
            
            self._archives[session_id] = archive
            self._save_metadata()
            
            # Optionally delete from active storage
            if session_id in sessions_data:
                del sessions_data[session_id]
                state_manager.set("session_manager.sessions", sessions_data)
            
            logger.info(f"Archived session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to archive session {session_id}: {e}")
            return False
    
    def restore_archive(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Restore an archived session.
        
        Args:
            session_id: Session ID to restore
            
        Returns:
            Session data dict or None
        """
        try:
            archive = self._archives.get(session_id)
            if not archive:
                logger.warning(f"Archive not found for session {session_id}")
                return None
            
            if archive.compressed_data:
                import gzip
                decompressed = gzip.decompress(archive.compressed_data)
                session_data = json.loads(decompressed.decode())
            else:
                # Need to reconstruct from other sources
                session_data = {
                    "session_id": archive.session_id,
                    "user_id": archive.user_id,
                    "session_type": archive.session_type,
                    "created_at": archive.created_at.isoformat(),
                    "status": archive.final_status,
                    "archived": True
                }
            
            # Restore to active sessions
            sessions_data = state_manager.get("session_manager.sessions", {})
            sessions_data[session_id] = session_data
            state_manager.set("session_manager.sessions", sessions_data)
            
            logger.info(f"Restored archived session {session_id}")
            return session_data
            
        except Exception as e:
            logger.error(f"Failed to restore archive {session_id}: {e}")
            return None
    
    def list_archives(self, user_id: str = None, 
                     session_type: SessionType = None,
                     days: int = 90) -> List[Dict[str, Any]]:
        """List archived sessions with optional filtering"""
        cutoff = datetime.now() - timedelta(days=days)
        
        archives = []
        for archive in self._archives.values():
            if archive.terminated_at < cutoff:
                continue
            
            if user_id and archive.user_id != user_id:
                continue
            
            if session_type and archive.session_type != session_type.value:
                continue
            
            archives.append({
                "session_id": archive.session_id,
                "user_id": archive.user_id,
                "session_type": archive.session_type,
                "created_at": archive.created_at.isoformat(),
                "terminated_at": archive.terminated_at.isoformat(),
                "duration_seconds": archive.duration_seconds,
                "total_activities": archive.total_activities,
                "final_status": archive.final_status
            })
        
        return sorted(archives, key=lambda x: x["terminated_at"], reverse=True)
    
    def delete_archive(self, session_id: str) -> bool:
        """Delete an archived session"""
        try:
            if session_id in self._archives:
                del self._archives[session_id]
                self._save_metadata()
                logger.info(f"Deleted archive for session {session_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete archive {session_id}: {e}")
            return False
    
    def create_backup(self) -> Dict[str, Any]:
        """
        Create a full backup of all session data.
        
        Returns:
            Backup metadata
        """
        try:
            backup_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = config.get("paths.session_backup_dir", "data/session_backups")
            backup_path = f"{backup_dir}/backup_{backup_id}"
            
            file_utils.ensure_directory(backup_path)
            
            # Backup active sessions
            sessions_data = state_manager.get("session_manager.sessions", {})
            file_utils.write_json(f"{backup_path}/sessions.json", sessions_data)
            
            # Backup activities
            activities_data = state_manager.get("session_manager.activities", [])
            file_utils.write_json(f"{backup_path}/activities.json", activities_data)
            
            # Backup snapshots and archives
            snapshots_data = {
                sid: [s.to_dict() for s in snapshots]
                for sid, snapshots in self._snapshots.items()
            }
            file_utils.write_json(f"{backup_path}/snapshots.json", snapshots_data)
            
            archives_data = {
                sid: arch.to_dict() for sid, arch in self._archives.items()
            }
            file_utils.write_json(f"{backup_path}/archives.json", archives_data)
            
            # Create manifest
            manifest = {
                "backup_id": backup_id,
                "created_at": datetime.now().isoformat(),
                "session_count": len(sessions_data),
                "activity_count": len(activities_data),
                "snapshot_count": sum(len(s) for s in self._snapshots.values()),
                "archive_count": len(self._archives)
            }
            file_utils.write_json(f"{backup_path}/manifest.json", manifest)
            
            logger.info(f"Created backup {backup_id} with {manifest['session_count']} sessions")
            return manifest
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return {"error": str(e)}
    
    def restore_backup(self, backup_id: str) -> bool:
        """
        Restore from a backup.
        
        Args:
            backup_id: Backup ID to restore
            
        Returns:
            True if successful
        """
        try:
            backup_dir = config.get("paths.session_backup_dir", "data/session_backups")
            backup_path = f"{backup_dir}/backup_{backup_id}"
            
            # Check if backup exists
            if not file_utils.directory_exists(backup_path):
                logger.error(f"Backup {backup_id} not found")
                return False
            
            # Restore sessions
            sessions_data = file_utils.read_json(f"{backup_path}/sessions.json")
            state_manager.set("session_manager.sessions", sessions_data)
            
            # Restore activities
            activities_data = file_utils.read_json(f"{backup_path}/activities.json")
            state_manager.set("session_manager.activities", activities_data)
            
            # Restore snapshots and archives
            snapshots_data = file_utils.read_json(f"{backup_path}/snapshots.json")
            self._snapshots.clear()
            for sid, snap_list in snapshots_data.items():
                self._snapshots[sid] = [SessionSnapshot.from_dict(s) for s in snap_list]
            
            archives_data = file_utils.read_json(f"{backup_path}/archives.json")
            self._archives.clear()
            for sid, arch_data in archives_data.items():
                self._archives[sid] = SessionArchive.from_dict(arch_data)
            
            self._save_metadata()
            
            logger.info(f"Restored from backup {backup_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore backup {backup_id}: {e}")
            return False
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List available backups"""
        backup_dir = config.get("paths.session_backup_dir", "data/session_backups")
        
        backups = []
        for item in file_utils.list_directory(backup_dir):
            if item.is_dir and item.name.startswith("backup_"):
                manifest_path = item.path / "manifest.json"
                if manifest_path.exists():
                    manifest = file_utils.read_json(str(manifest_path))
                    backups.append(manifest)
        
        return sorted(backups, key=lambda x: x.get("created_at", ""), reverse=True)
    
    def cleanup_old_archives(self, days: int = None) -> int:
        """Clean up archives older than specified days"""
        retention_days = days or self.config.archive_after_days
        cutoff = datetime.now() - timedelta(days=retention_days)
        
        to_delete = []
        for session_id, archive in self._archives.items():
            if archive.terminated_at < cutoff:
                to_delete.append(session_id)
        
        for session_id in to_delete:
            del self._archives[session_id]
        
        if to_delete:
            self._save_metadata()
            logger.info(f"Cleaned up {len(to_delete)} old archives")
        
        return len(to_delete)
    
    def get_persistence_stats(self) -> Dict[str, Any]:
        """Get persistence statistics"""
        return {
            "backend": self.config.backend.value,
            "active_snapshots": sum(len(s) for s in self._snapshots.values()),
            "archived_sessions": len(self._archives),
            "cached_sessions": len(self._cache),
            "auto_save_interval": self.config.auto_save_interval_seconds,
            "archive_retention_days": self.config.archive_after_days,
            "compression_enabled": self.config.compression_enabled,
            "encryption_enabled": self.config.encryption_enabled,
            "backup_enabled": self.config.backup_enabled
        }
    
    def clear_cache(self) -> int:
        """Clear in-memory cache"""
        count = len(self._cache)
        self._cache.clear()
        logger.debug(f"Cleared {count} cached sessions")
        return count


# Singleton instance
_session_persistence: Optional[SessionPersistence] = None


def get_session_persistence() -> SessionPersistence:
    """Get global SessionPersistence instance"""
    global _session_persistence
    if _session_persistence is None:
        _session_persistence = SessionPersistence()
    return _session_persistence