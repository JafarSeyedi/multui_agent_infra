"""
Session Manager for Orchestration

Manages user and agent sessions across the entire system including:
- CLI sessions (interactive command sessions)
- API sessions (REST/WebSocket API access)
- IDE plugin sessions (VS Code, PyCharm, etc.)
- Bot sessions (Discord, Slack, etc.)
- Human-in-the-loop sessions
- Workflow execution sessions

Sessions provide:
- Authentication and authorization context
- Cross-workflow state persistence
- User preferences and settings
- Activity tracking and audit logs
- Session lifecycle management (create, expire, renew)
"""

import uuid
import threading
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict

from ...shared.logger import get_logger
from ...shared.state_manager import state_manager
from ...shared.config import config

logger = get_logger(__name__)


class SessionType(Enum):
    """Types of sessions supported"""
    CLI = "cli"                      # Command-line interface session
    API = "api"                      # REST/GraphQL API session
    IDE = "ide"                      # IDE plugin session (VS Code, PyCharm)
    WEB = "web"                      # Web interface session
    BOT = "bot"                      # Chat bot session (Discord, Slack)
    HUMAN_TASK = "human_task"        # Human-in-the-loop task session
    WORKFLOW = "workflow"            # Workflow execution session
    SERVICE = "service"              # Service-to-service session
    SYSTEM = "system"                # System internal session


class SessionStatus(Enum):
    """Status of a session"""
    ACTIVE = "active"                # Session is active
    IDLE = "idle"                    # Session is idle but valid
    EXPIRED = "expired"              # Session has expired
    TERMINATED = "terminated"        # Session explicitly terminated
    SUSPENDED = "suspended"          # Session temporarily suspended


class SessionAuthLevel(Enum):
    """Authentication/Authorization levels"""
    ANONYMOUS = 0                    # No authentication
    AUTHENTICATED = 1                # Basic authentication
    VERIFIED = 2                     # Email/2FA verified
    ADMIN = 3                        # Administrator
    SYSTEM = 4                       # System-level access


@dataclass
class SessionContext:
    """Context data associated with a session"""
    active_workflows: List[str] = field(default_factory=list)   # Workflow execution IDs
    active_tasks: List[str] = field(default_factory=list)       # Task IDs
    human_assignments: List[str] = field(default_factory=list)  # Assigned human task IDs
    preferences: Dict[str, Any] = field(default_factory=dict)    # User preferences
    metadata: Dict[str, Any] = field(default_factory=dict)       # Additional metadata
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "active_workflows": self.active_workflows,
            "active_tasks": self.active_tasks,
            "human_assignments": self.human_assignments,
            "preferences": self.preferences,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionContext":
        return cls(
            active_workflows=data.get("active_workflows", []),
            active_tasks=data.get("active_tasks", []),
            human_assignments=data.get("human_assignments", []),
            preferences=data.get("preferences", {}),
            metadata=data.get("metadata", {})
        )


@dataclass
class Session:
    """Represents a user/agent session"""
    session_id: str
    session_type: SessionType
    user_id: Optional[str] = None          # User ID (if authenticated)
    user_name: Optional[str] = None        # User name
    auth_level: SessionAuthLevel = SessionAuthLevel.ANONYMOUS
    status: SessionStatus = SessionStatus.ACTIVE
    context: SessionContext = field(default_factory=SessionContext)
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    client_info: Dict[str, Any] = field(default_factory=dict)   # Client IP, user agent, etc.
    tags: List[str] = field(default_factory=list)
    
    @property
    def is_expired(self) -> bool:
        """Check if session has expired"""
        if self.expires_at:
            return datetime.now() > self.expires_at
        return False
    
    @property
    def idle_minutes(self) -> float:
        """Calculate idle time in minutes"""
        return (datetime.now() - self.last_activity).total_seconds() / 60
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "session_type": self.session_type.value,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "auth_level": self.auth_level.value,
            "status": self.status.value,
            "context": self.context.to_dict(),
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "client_info": self.client_info,
            "tags": self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Session":
        return cls(
            session_id=data["session_id"],
            session_type=SessionType(data["session_type"]),
            user_id=data.get("user_id"),
            user_name=data.get("user_name"),
            auth_level=SessionAuthLevel(data.get("auth_level", 0)),
            status=SessionStatus(data.get("status", "active")),
            context=SessionContext.from_dict(data.get("context", {})),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            last_activity=datetime.fromisoformat(data["last_activity"]) if data.get("last_activity") else datetime.now(),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            client_info=data.get("client_info", {}),
            tags=data.get("tags", [])
        )


@dataclass
class SessionActivity:
    """Records activity within a session"""
    activity_id: str
    session_id: str
    action: str
    target_type: str  # workflow, task, human_task, etc.
    target_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "activity_id": self.activity_id,
            "session_id": self.session_id,
            "action": self.action,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }


class SessionManager:
    """
    Central session management for all interaction types.
    
    Features:
    - Multi-type session support (CLI, API, IDE, BOT, Human Task, Workflow)
    - Authentication and authorization
    - Session lifecycle management
    - Activity tracking and audit logging
    - Auto-expiration and cleanup
    - Cross-session state sharing
    - Session context persistence
    """
    
    def __init__(self, storage_key: str = "session_manager"):
        self.storage_key = storage_key
        self.sessions: Dict[str, Session] = {}
        self.activities: List[SessionActivity] = []
        self._lock = threading.RLock()
        
        # Configuration
        self.default_timeout_minutes = config.get("session.default_timeout_minutes", 60)
        self.max_sessions_per_user = config.get("session.max_sessions_per_user", 10)
        self.cleanup_interval_minutes = config.get("session.cleanup_interval_minutes", 15)
        self.audit_retention_days = config.get("session.audit_retention_days", 30)
        
        # Callbacks
        self._on_session_created: List[Any] = []
        self._on_session_terminated: List[Any] = []
        self._on_session_expired: List[Any] = []
        
        # Load data
        self._load_data()
        
        # Start cleanup worker
        self._start_cleanup_worker()
        
        logger.info("SessionManager initialized")
    
    def _load_data(self) -> None:
        """Load sessions from state manager"""
        try:
            sessions_data = state_manager.get(f"{self.storage_key}.sessions", {})
            for sid, sdata in sessions_data.items():
                if isinstance(sdata, dict):
                    session = Session.from_dict(sdata)
                    # Don't load expired or terminated sessions
                    if session.status not in [SessionStatus.EXPIRED, SessionStatus.TERMINATED]:
                        if not session.is_expired:
                            self.sessions[sid] = session
            
            activities_data = state_manager.get(f"{self.storage_key}.activities", [])
            for adata in activities_data[-10000:]:  # Keep last 10000 activities
                if isinstance(adata, dict):
                    self.activities.append(SessionActivity(**adata))
                    
        except Exception as e:
            logger.warning(f"Failed to load session data: {e}")
    
    def _save_data(self) -> None:
        """Save sessions to state manager"""
        try:
            sessions_data = {sid: s.to_dict() for sid, s in self.sessions.items()}
            state_manager.set(f"{self.storage_key}.sessions", sessions_data)
            
            # Keep last 10000 activities
            activities_data = [a.to_dict() for a in self.activities[-10000:]]
            state_manager.set(f"{self.storage_key}.activities", activities_data)
            
        except Exception as e:
            logger.error(f"Failed to save session data: {e}")
    
    def _start_cleanup_worker(self) -> None:
        """Start background cleanup worker"""
        def cleanup_worker():
            while True:
                try:
                    self._cleanup_expired_sessions()
                    self._cleanup_old_activities()
                except Exception as e:
                    logger.error(f"Cleanup worker error: {e}")
                threading.Event().wait(self.cleanup_interval_minutes * 60)
        
        worker = threading.Thread(target=cleanup_worker, daemon=True)
        worker.start()
    
    def _cleanup_expired_sessions(self) -> None:
        """Remove expired and terminated sessions"""
        with self._lock:
            expired = []
            for sid, session in self.sessions.items():
                if session.is_expired:
                    session.status = SessionStatus.EXPIRED
                    expired.append(sid)
                    self._notify_session_expired(session)
                elif session.status == SessionStatus.TERMINATED:
                    expired.append(sid)
            
            for sid in expired:
                del self.sessions[sid]
            
            if expired:
                self._save_data()
                logger.info(f"Cleaned up {len(expired)} expired/terminated sessions")
    
    def _cleanup_old_activities(self) -> None:
        """Remove activity records older than retention period"""
        cutoff = datetime.now() - timedelta(days=self.audit_retention_days)
        
        with self._lock:
            original_count = len(self.activities)
            self.activities = [a for a in self.activities if a.timestamp > cutoff]
            
            if len(self.activities) != original_count:
                self._save_data()
                logger.debug(f"Cleaned up {original_count - len(self.activities)} old activities")
    
    def create_session(self, session_type: SessionType,
                      user_id: str = None,
                      user_name: str = None,
                      auth_level: SessionAuthLevel = SessionAuthLevel.ANONYMOUS,
                      client_info: Dict[str, Any] = None,
                      timeout_minutes: int = None,
                      tags: List[str] = None) -> Session:
        """
        Create a new session.
        
        Args:
            session_type: Type of session
            user_id: User identifier (if authenticated)
            user_name: User name
            auth_level: Authentication level
            client_info: Client information (IP, user agent, etc.)
            timeout_minutes: Session timeout in minutes
            tags: Session tags for categorization
            
        Returns:
            Created Session object
        """
        # Check max sessions per user
        if user_id:
            user_sessions = [s for s in self.sessions.values() if s.user_id == user_id]
            if len(user_sessions) >= self.max_sessions_per_user:
                # Terminate oldest session
                oldest = min(user_sessions, key=lambda s: s.created_at)
                self.terminate_session(oldest.session_id)
        
        session_id = str(uuid.uuid4())
        expires_at = datetime.now() + timedelta(minutes=timeout_minutes or self.default_timeout_minutes)
        
        session = Session(
            session_id=session_id,
            session_type=session_type,
            user_id=user_id,
            user_name=user_name,
            auth_level=auth_level,
            status=SessionStatus.ACTIVE,
            expires_at=expires_at,
            client_info=client_info or {},
            tags=tags or []
        )
        
        with self._lock:
            self.sessions[session_id] = session
            self._save_data()
        
        # Record activity
        self._record_activity(
            session_id=session_id,
            action="session_created",
            target_type="session",
            details={
                "session_type": session_type.value,
                "auth_level": auth_level.value,
                "user_id": user_id
            }
        )
        
        self._notify_session_created(session)
        
        logger.info(f"Created {session_type.value} session {session_id} for user {user_id or 'anonymous'}")
        
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID"""
        with self._lock:
            session = self.sessions.get(session_id)
            if session and not session.is_expired:
                return session
            return None
    
    def validate_session(self, session_id: str) -> bool:
        """
        Validate a session (check if active and not expired).
        
        Args:
            session_id: Session ID
            
        Returns:
            True if session is valid
        """
        with self._lock:
            session = self.sessions.get(session_id)
            if not session:
                return False
            
            if session.is_expired:
                session.status = SessionStatus.EXPIRED
                self._save_data()
                return False
            
            if session.status != SessionStatus.ACTIVE:
                return False
            
            # Update last activity
            session.last_activity = datetime.now()
            self._save_data()
            
            return True
    
    def update_activity(self, session_id: str, action: str,
                       target_type: str = None,
                       target_id: str = None,
                       details: Dict[str, Any] = None) -> bool:
        """
        Update session activity and record action.
        
        Args:
            session_id: Session ID
            action: Action being performed
            target_type: Type of target (workflow, task, etc.)
            target_id: Target identifier
            details: Additional details
            
        Returns:
            True if successful
        """
        with self._lock:
            session = self.sessions.get(session_id)
            if not session or session.status != SessionStatus.ACTIVE:
                return False
            
            # Update last activity
            session.last_activity = datetime.now()
            
            # Record activity
            self._record_activity(session_id, action, target_type, target_id, details)
            
            self._save_data()
            return True
    
    def _record_activity(self, session_id: str, action: str,
                        target_type: str = None,
                        target_id: str = None,
                        details: Dict[str, Any] = None) -> None:
        """Internal method to record activity"""
        activity = SessionActivity(
            activity_id=str(uuid.uuid4()),
            session_id=session_id,
            action=action,
            target_type=target_type or "session",
            target_id=target_id,
            details=details or {}
        )
        self.activities.append(activity)
    
    def touch_session(self, session_id: str) -> bool:
        """
        Refresh session expiration (touch).
        
        Args:
            session_id: Session ID
            
        Returns:
            True if successful
        """
        with self._lock:
            session = self.sessions.get(session_id)
            if not session or session.status != SessionStatus.ACTIVE:
                return False
            
            session.last_activity = datetime.now()
            session.expires_at = datetime.now() + timedelta(minutes=self.default_timeout_minutes)
            
            self._save_data()
            return True
    
    def terminate_session(self, session_id: str) -> bool:
        """
        Explicitly terminate a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if successful
        """
        with self._lock:
            session = self.sessions.get(session_id)
            if not session:
                return False
            
            session.status = SessionStatus.TERMINATED
            
            self._record_activity(
                session_id=session_id,
                action="session_terminated",
                target_type="session"
            )
            
            self._save_data()
            
            self._notify_session_terminated(session)
            
            logger.info(f"Terminated session {session_id}")
            return True
    
    def renew_session(self, session_id: str, 
                     timeout_minutes: int = None) -> Optional[Session]:
        """
        Renew a session (reset expiration).
        
        Args:
            session_id: Session ID
            timeout_minutes: New timeout in minutes
            
        Returns:
            Renewed Session or None
        """
        with self._lock:
            session = self.sessions.get(session_id)
            if not session:
                return None
            
            session.last_activity = datetime.now()
            session.expires_at = datetime.now() + timedelta(
                minutes=timeout_minutes or self.default_timeout_minutes
            )
            
            if session.status == SessionStatus.EXPIRED:
                session.status = SessionStatus.ACTIVE
            
            self._record_activity(
                session_id=session_id,
                action="session_renewed",
                target_type="session",
                details={"timeout_minutes": timeout_minutes or self.default_timeout_minutes}
            )
            
            self._save_data()
            
            logger.info(f"Renewed session {session_id}")
            return session
    
    def attach_workflow(self, session_id: str, workflow_execution_id: str) -> bool:
        """
        Attach a workflow execution to a session.
        
        Args:
            session_id: Session ID
            workflow_execution_id: Workflow execution ID
            
        Returns:
            True if successful
        """
        with self._lock:
            session = self.sessions.get(session_id)
            if not session:
                return False
            
            if workflow_execution_id not in session.context.active_workflows:
                session.context.active_workflows.append(workflow_execution_id)
            
            self._record_activity(
                session_id=session_id,
                action="workflow_attached",
                target_type="workflow",
                target_id=workflow_execution_id
            )
            
            self._save_data()
            return True
    
    def detach_workflow(self, session_id: str, workflow_execution_id: str) -> bool:
        """
        Detach a workflow execution from a session.
        
        Args:
            session_id: Session ID
            workflow_execution_id: Workflow execution ID
            
        Returns:
            True if successful
        """
        with self._lock:
            session = self.sessions.get(session_id)
            if not session:
                return False
            
            if workflow_execution_id in session.context.active_workflows:
                session.context.active_workflows.remove(workflow_execution_id)
            
            self._save_data()
            return True
    
    def attach_human_task(self, session_id: str, task_id: str) -> bool:
        """
        Attach a human task assignment to a session.
        
        Args:
            session_id: Session ID
            task_id: Human task ID
            
        Returns:
            True if successful
        """
        with self._lock:
            session = self.sessions.get(session_id)
            if not session:
                return False
            
            if task_id not in session.context.human_assignments:
                session.context.human_assignments.append(task_id)
            
            self._save_data()
            return True
    
    def detach_human_task(self, session_id: str, task_id: str) -> bool:
        """
        Detach a human task from a session.
        
        Args:
            session_id: Session ID
            task_id: Human task ID
            
        Returns:
            True if successful
        """
        with self._lock:
            session = self.sessions.get(session_id)
            if not session:
                return False
            
            if task_id in session.context.human_assignments:
                session.context.human_assignments.remove(task_id)
            
            self._save_data()
            return True
    
    def set_preference(self, session_id: str, key: str, value: Any) -> bool:
        """
        Set a user preference for the session.
        
        Args:
            session_id: Session ID
            key: Preference key
            value: Preference value
            
        Returns:
            True if successful
        """
        with self._lock:
            session = self.sessions.get(session_id)
            if not session:
                return False
            
            session.context.preferences[key] = value
            self._save_data()
            return True
    
    def get_preference(self, session_id: str, key: str, default: Any = None) -> Any:
        """Get a user preference"""
        with self._lock:
            session = self.sessions.get(session_id)
            if not session:
                return default
            return session.context.preferences.get(key, default)
    
    def get_session_workflows(self, session_id: str) -> List[str]:
        """Get all workflow executions attached to a session"""
        with self._lock:
            session = self.sessions.get(session_id)
            if not session:
                return []
            return session.context.active_workflows.copy()
    
    def get_session_tasks(self, session_id: str) -> List[str]:
        """Get all tasks attached to a session"""
        with self._lock:
            session = self.sessions.get(session_id)
            if not session:
                return []
            return session.context.active_tasks.copy()
    
    def get_session_human_tasks(self, session_id: str) -> List[str]:
        """Get all human tasks assigned to this session"""
        with self._lock:
            session = self.sessions.get(session_id)
            if not session:
                return []
            return session.context.human_assignments.copy()
    
    def get_user_sessions(self, user_id: str) -> List[Session]:
        """Get all active sessions for a user"""
        with self._lock:
            return [
                s for s in self.sessions.values()
                if s.user_id == user_id and s.status == SessionStatus.ACTIVE
            ]
    
    def get_sessions_by_type(self, session_type: SessionType) -> List[Session]:
        """Get all sessions of a specific type"""
        with self._lock:
            return [
                s for s in self.sessions.values()
                if s.session_type == session_type and s.status == SessionStatus.ACTIVE
            ]
    
    def get_session_activity(self, session_id: str, 
                            limit: int = 100) -> List[Dict[str, Any]]:
        """Get activity history for a session"""
        with self._lock:
            activities = [
                a.to_dict() for a in self.activities
                if a.session_id == session_id
            ]
            return activities[-limit:]
    
    def get_active_sessions_count(self) -> Dict[str, int]:
        """Get count of active sessions by type"""
        with self._lock:
            counts = defaultdict(int)
            for session in self.sessions.values():
                if session.status == SessionStatus.ACTIVE:
                    counts[session.session_type.value] += 1
            return dict(counts)
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """Get comprehensive session statistics"""
        with self._lock:
            active = [s for s in self.sessions.values() if s.status == SessionStatus.ACTIVE]
            idle = [s for s in self.sessions.values() if s.status == SessionStatus.IDLE]
            expired = [s for s in self.sessions.values() if s.status == SessionStatus.EXPIRED]
            
            # Average session duration for completed sessions
            completed_sessions = [s for s in self.sessions.values() 
                                 if s.status in [SessionStatus.TERMINATED, SessionStatus.EXPIRED]]
            avg_duration = 0
            for s in completed_sessions:
                duration = (s.last_activity - s.created_at).total_seconds() / 60
                avg_duration += duration
            avg_duration = avg_duration / len(completed_sessions) if completed_sessions else 0
            
            # Sessions by auth level
            by_auth = defaultdict(int)
            for s in self.sessions.values():
                by_auth[s.auth_level.name] += 1
            
            return {
                "total_sessions": len(self.sessions),
                "active_sessions": len(active),
                "idle_sessions": len(idle),
                "expired_sessions": len(expired),
                "terminated_sessions": len([s for s in self.sessions.values() 
                                           if s.status == SessionStatus.TERMINATED]),
                "average_session_duration_minutes": avg_duration,
                "sessions_by_type": self.get_active_sessions_count(),
                "sessions_by_auth": dict(by_auth),
                "total_activities": len(self.activities),
                "activities_last_24h": len([a for a in self.activities 
                                           if a.timestamp > datetime.now() - timedelta(hours=24)])
            }
    
    def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed summary of a session"""
        with self._lock:
            session = self.sessions.get(session_id)
            if not session:
                return None
            
            recent_activities = self.get_session_activity(session_id, limit=20)
            
            return {
                "session": session.to_dict(),
                "recent_activities": recent_activities,
                "workflow_count": len(session.context.active_workflows),
                "human_task_count": len(session.context.human_assignments),
                "idle_minutes": session.idle_minutes
            }
    
    def on_session_created(self, callback: Any) -> None:
        """Register callback for session creation"""
        self._on_session_created.append(callback)
    
    def on_session_terminated(self, callback: Any) -> None:
        """Register callback for session termination"""
        self._on_session_terminated.append(callback)
    
    def on_session_expired(self, callback: Any) -> None:
        """Register callback for session expiration"""
        self._on_session_expired.append(callback)
    
    def _notify_session_created(self, session: Session) -> None:
        """Notify session creation callbacks"""
        for callback in self._on_session_created:
            try:
                callback(session)
            except Exception as e:
                logger.error(f"Error in session created callback: {e}")
    
    def _notify_session_terminated(self, session: Session) -> None:
        """Notify session termination callbacks"""
        for callback in self._on_session_terminated:
            try:
                callback(session)
            except Exception as e:
                logger.error(f"Error in session terminated callback: {e}")
    
    def _notify_session_expired(self, session: Session) -> None:
        """Notify session expiration callbacks"""
        for callback in self._on_session_expired:
            try:
                callback(session)
            except Exception as e:
                logger.error(f"Error in session expired callback: {e}")
    
    def cleanup_all_expired(self) -> int:
        """Manually trigger cleanup of all expired sessions"""
        self._cleanup_expired_sessions()
        return len([s for s in self.sessions.values() if s.status == SessionStatus.EXPIRED])
    
    def shutdown(self) -> None:
        """Shutdown session manager (terminate all sessions)"""
        with self._lock:
            for session in list(self.sessions.values()):
                session.status = SessionStatus.TERMINATED
            self._save_data()
        logger.info("SessionManager shutdown complete")


# Singleton instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get global SessionManager instance"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager