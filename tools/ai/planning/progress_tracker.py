#!/usr/bin/env python3
"""
Progress Tracker - AI Development Framework
Tracks implementation progress across modules, tasks, and epics.

Part of the Level 1 Planning tools (t1_1_4_1_progress_tracker.py)
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, DefaultDict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict
import subprocess

from ..shared.llm_client import LLMClient
from ..shared.state_manager import StateManager
from ..shared.logger import get_logger
from ..shared.git_utils import GitUtils

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class TaskStatus(str, Enum):
    """Status of a task."""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    REVIEW = "review"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class EpicStatus(str, Enum):
    """Status of an epic."""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Priority(str, Enum):
    """Task priority."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class HealthStatus(str, Enum):
    """Project health status."""
    ON_TRACK = "on_track"
    AT_RISK = "at_risk"
    DELAYED = "delayed"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class Task:
    """A single implementation task."""
    id: str
    title: str
    description: str
    module_name: str
    priority: Priority = Priority.MEDIUM
    status: TaskStatus = TaskStatus.PLANNED
    estimated_hours: float = 1.0
    actual_hours: float = 0.0
    assignee: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    blocked_by: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_updated: datetime = field(default_factory=datetime.now)
    notes: List[Dict[str, Any]] = field(default_factory=list)
    code_files: List[str] = field(default_factory=list)
    test_files: List[str] = field(default_factory=list)
    pull_request: Optional[str] = None
    commits: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_overdue(self) -> bool:
        """Check if task is overdue."""
        if self.status in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
            return False
        if not self.started_at:
            return False
        expected_completion = self.started_at + timedelta(hours=self.estimated_hours * 1.5)
        return datetime.now() > expected_completion
    
    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage."""
        if self.status == TaskStatus.COMPLETED:
            return 100.0
        if self.status == TaskStatus.REVIEW:
            return 90.0
        if self.status == TaskStatus.IN_PROGRESS:
            if self.estimated_hours > 0:
                return min(80.0, (self.actual_hours / self.estimated_hours) * 100)
            return 50.0
        return 0.0


@dataclass
class Epic:
    """A collection of related tasks forming a feature/epic."""
    id: str
    title: str
    description: str
    status: EpicStatus = EpicStatus.PLANNED
    priority: Priority = Priority.MEDIUM
    tasks: List[str] = field(default_factory=list)  # Task IDs
    dependencies: List[str] = field(default_factory=list)  # Epic IDs
    target_completion: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    owner: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def calculate_progress(self, tasks: Dict[str, Task]) -> float:
        """Calculate epic progress based on tasks."""
        if not self.tasks:
            return 0.0
        
        total_progress = sum(
            tasks[task_id].progress_percentage
            for task_id in self.tasks
            if task_id in tasks
        )
        return total_progress / len(self.tasks)
    
    @property
    def is_overdue(self) -> bool:
        """Check if epic is overdue."""
        if self.status in [EpicStatus.COMPLETED, EpicStatus.CANCELLED]:
            return False
        if not self.target_completion:
            return False
        return datetime.now() > self.target_completion


@dataclass
class Module:
    """A code module being developed."""
    name: str
    description: str
    path: Path
    tasks: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PLANNED
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    lines_of_code: int = 0
    test_coverage: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def calculate_progress(self, tasks: Dict[str, Task]) -> float:
        """Calculate module progress based on tasks."""
        if not self.tasks:
            return 0.0 if self.status != TaskStatus.COMPLETED else 100.0
        
        total_progress = sum(
            tasks[task_id].progress_percentage
            for task_id in self.tasks
            if task_id in tasks
        )
        return total_progress / len(self.tasks)


@dataclass
class Milestone:
    """A project milestone."""
    id: str
    title: str
    description: str
    target_date: datetime
    epics: List[str] = field(default_factory=list)
    status: str = "pending"
    achieved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_overdue(self) -> bool:
        """Check if milestone is overdue."""
        if self.status == "achieved":
            return False
        return datetime.now() > self.target_date


@dataclass
class DailySnapshot:
    """Snapshot of progress at a point in time."""
    date: datetime
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    blocked_tasks: int
    total_epics: int
    completed_epics: int
    total_modules: int
    completed_modules: int
    overall_progress: float
    lines_of_code: int
    test_coverage: float
    open_issues: int
    closed_issues: int
    commits_count: int
    velocity: float  # Tasks completed per week


@dataclass
class ProgressReport:
    """Complete progress report."""
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    summary: Dict[str, Any]
    tasks: Dict[str, Task]
    epics: Dict[str, Epic]
    modules: Dict[str, Module]
    milestones: Dict[str, Milestone]
    snapshots: List[DailySnapshot]
    health: HealthStatus
    recommendations: List[str]
    metrics: Dict[str, Any]


# ============================================================
# MAIN TRACKER CLASS
# ============================================================

class ProgressTracker:
    """
    Tracks implementation progress across the entire project.
    
    Features:
    - Task and epic management
    - Module-level progress tracking
    - Milestone tracking
    - Daily snapshots for historical analysis
    - Velocity calculation
    - Health monitoring and alerts
    - Burndown/burnup chart generation
    - Integration with git for automatic updates
    - AI-powered status reports and recommendations
    - Export to various formats (JSON, Markdown, HTML)
    """
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.llm = LLMClient()
        self.git = GitUtils(project_root)
        self.state = StateManager(project_root / ".ai_state" / "progress_tracker.json")
        
        # Data storage
        self.tasks: Dict[str, Task] = {}
        self.epics: Dict[str, Epic] = {}
        self.modules: Dict[str, Module] = {}
        self.milestones: Dict[str, Milestone] = {}
        self.snapshots: List[DailySnapshot] = []
        
        # Load existing state
        self._load_state()
        
        # Configuration
        self.work_hours_per_day = 8
        self.work_days_per_week = 5
    
    # ============================================================
    # STATE MANAGEMENT
    # ============================================================
    
    def _load_state(self):
        """Load persisted state."""
        data = self.state.get_all()
        
        # Load tasks
        for task_data in data.get('tasks', {}).values():
            task = self._deserialize_task(task_data)
            self.tasks[task.id] = task
        
        # Load epics
        for epic_data in data.get('epics', {}).values():
            epic = self._deserialize_epic(epic_data)
            self.epics[epic.id] = epic
        
        # Load modules
        for module_data in data.get('modules', {}).values():
            module = self._deserialize_module(module_data)
            self.modules[module.name] = module
        
        # Load milestones
        for milestone_data in data.get('milestones', {}).values():
            milestone = self._deserialize_milestone(milestone_data)
            self.milestones[milestone.id] = milestone
        
        # Load snapshots
        for snapshot_data in data.get('snapshots', []):
            self.snapshots.append(self._deserialize_snapshot(snapshot_data))
        
        logger.info(f"Loaded state: {len(self.tasks)} tasks, {len(self.epics)} epics, {len(self.modules)} modules")
    
    def _save_state(self):
        """Persist current state."""
        data = {
            'tasks': {tid: self._serialize_task(t) for tid, t in self.tasks.items()},
            'epics': {eid: self._serialize_epic(e) for eid, e in self.epics.items()},
            'modules': {mname: self._serialize_module(m) for mname, m in self.modules.items()},
            'milestones': {mid: self._serialize_milestone(m) for mid, m in self.milestones.items()},
            'snapshots': [self._serialize_snapshot(s) for s in self.snapshots[-30:]],  # Keep last 30
            'last_saved': datetime.now().isoformat()
        }
        self.state.set_all(data)
        self.state.save()
        logger.debug("State saved")
    
    def _serialize_task(self, task: Task) -> Dict[str, Any]:
        """Serialize task to dict."""
        return {
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'module_name': task.module_name,
            'priority': task.priority.value,
            'status': task.status.value,
            'estimated_hours': task.estimated_hours,
            'actual_hours': task.actual_hours,
            'assignee': task.assignee,
            'dependencies': task.dependencies,
            'blocked_by': task.blocked_by,
            'tags': task.tags,
            'created_at': task.created_at.isoformat() if task.created_at else None,
            'started_at': task.started_at.isoformat() if task.started_at else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
            'last_updated': task.last_updated.isoformat() if task.last_updated else None,
            'notes': task.notes,
            'code_files': task.code_files,
            'test_files': task.test_files,
            'pull_request': task.pull_request,
            'commits': task.commits,
            'metadata': task.metadata
        }
    
    def _deserialize_task(self, data: Dict[str, Any]) -> Task:
        """Deserialize task from dict."""
        return Task(
            id=data['id'],
            title=data['title'],
            description=data['description'],
            module_name=data['module_name'],
            priority=Priority(data['priority']),
            status=TaskStatus(data['status']),
            estimated_hours=data['estimated_hours'],
            actual_hours=data['actual_hours'],
            assignee=data.get('assignee'),
            dependencies=data.get('dependencies', []),
            blocked_by=data.get('blocked_by', []),
            tags=data.get('tags', []),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
            started_at=datetime.fromisoformat(data['started_at']) if data.get('started_at') else None,
            completed_at=datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None,
            last_updated=datetime.fromisoformat(data['last_updated']) if data.get('last_updated') else datetime.now(),
            notes=data.get('notes', []),
            code_files=data.get('code_files', []),
            test_files=data.get('test_files', []),
            pull_request=data.get('pull_request'),
            commits=data.get('commits', []),
            metadata=data.get('metadata', {})
        )
    
    def _serialize_epic(self, epic: Epic) -> Dict[str, Any]:
        """Serialize epic to dict."""
        return {
            'id': epic.id,
            'title': epic.title,
            'description': epic.description,
            'status': epic.status.value,
            'priority': epic.priority.value,
            'tasks': epic.tasks,
            'dependencies': epic.dependencies,
            'target_completion': epic.target_completion.isoformat() if epic.target_completion else None,
            'created_at': epic.created_at.isoformat() if epic.created_at else None,
            'started_at': epic.started_at.isoformat() if epic.started_at else None,
            'completed_at': epic.completed_at.isoformat() if epic.completed_at else None,
            'owner': epic.owner,
            'tags': epic.tags,
            'metadata': epic.metadata
        }
    
    def _deserialize_epic(self, data: Dict[str, Any]) -> Epic:
        """Deserialize epic from dict."""
        return Epic(
            id=data['id'],
            title=data['title'],
            description=data['description'],
            status=EpicStatus(data['status']),
            priority=Priority(data['priority']),
            tasks=data.get('tasks', []),
            dependencies=data.get('dependencies', []),
            target_completion=datetime.fromisoformat(data['target_completion']) if data.get('target_completion') else None,
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
            started_at=datetime.fromisoformat(data['started_at']) if data.get('started_at') else None,
            completed_at=datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None,
            owner=data.get('owner'),
            tags=data.get('tags', []),
            metadata=data.get('metadata', {})
        )
    
    def _serialize_module(self, module: Module) -> Dict[str, Any]:
        """Serialize module to dict."""
        return {
            'name': module.name,
            'description': module.description,
            'path': str(module.path),
            'tasks': module.tasks,
            'dependencies': module.dependencies,
            'status': module.status.value,
            'created_at': module.created_at.isoformat() if module.created_at else None,
            'completed_at': module.completed_at.isoformat() if module.completed_at else None,
            'lines_of_code': module.lines_of_code,
            'test_coverage': module.test_coverage,
            'metadata': module.metadata
        }
    
    def _deserialize_module(self, data: Dict[str, Any]) -> Module:
        """Deserialize module from dict."""
        return Module(
            name=data['name'],
            description=data['description'],
            path=Path(data['path']),
            tasks=data.get('tasks', []),
            dependencies=data.get('dependencies', []),
            status=TaskStatus(data['status']),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
            completed_at=datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None,
            lines_of_code=data.get('lines_of_code', 0),
            test_coverage=data.get('test_coverage', 0.0),
            metadata=data.get('metadata', {})
        )
    
    def _serialize_milestone(self, milestone: Milestone) -> Dict[str, Any]:
        """Serialize milestone to dict."""
        return {
            'id': milestone.id,
            'title': milestone.title,
            'description': milestone.description,
            'target_date': milestone.target_date.isoformat(),
            'epics': milestone.epics,
            'status': milestone.status,
            'achieved_at': milestone.achieved_at.isoformat() if milestone.achieved_at else None,
            'metadata': milestone.metadata
        }
    
    def _deserialize_milestone(self, data: Dict[str, Any]) -> Milestone:
        """Deserialize milestone from dict."""
        return Milestone(
            id=data['id'],
            title=data['title'],
            description=data['description'],
            target_date=datetime.fromisoformat(data['target_date']),
            epics=data.get('epics', []),
            status=data.get('status', 'pending'),
            achieved_at=datetime.fromisoformat(data['achieved_at']) if data.get('achieved_at') else None,
            metadata=data.get('metadata', {})
        )
    
    def _serialize_snapshot(self, snapshot: DailySnapshot) -> Dict[str, Any]:
        """Serialize snapshot to dict."""
        return {
            'date': snapshot.date.isoformat(),
            'total_tasks': snapshot.total_tasks,
            'completed_tasks': snapshot.completed_tasks,
            'in_progress_tasks': snapshot.in_progress_tasks,
            'blocked_tasks': snapshot.blocked_tasks,
            'total_epics': snapshot.total_epics,
            'completed_epics': snapshot.completed_epics,
            'total_modules': snapshot.total_modules,
            'completed_modules': snapshot.completed_modules,
            'overall_progress': snapshot.overall_progress,
            'lines_of_code': snapshot.lines_of_code,
            'test_coverage': snapshot.test_coverage,
            'open_issues': snapshot.open_issues,
            'closed_issues': snapshot.closed_issues,
            'commits_count': snapshot.commits_count,
            'velocity': snapshot.velocity
        }
    
    def _deserialize_snapshot(self, data: Dict[str, Any]) -> DailySnapshot:
        """Deserialize snapshot from dict."""
        return DailySnapshot(
            date=datetime.fromisoformat(data['date']),
            total_tasks=data['total_tasks'],
            completed_tasks=data['completed_tasks'],
            in_progress_tasks=data['in_progress_tasks'],
            blocked_tasks=data['blocked_tasks'],
            total_epics=data['total_epics'],
            completed_epics=data['completed_epics'],
            total_modules=data['total_modules'],
            completed_modules=data['completed_modules'],
            overall_progress=data['overall_progress'],
            lines_of_code=data['lines_of_code'],
            test_coverage=data['test_coverage'],
            open_issues=data['open_issues'],
            closed_issues=data['closed_issues'],
            commits_count=data['commits_count'],
            velocity=data['velocity']
        )
    
    # ============================================================
    # TASK MANAGEMENT
    # ============================================================
    
    def create_task(self, 
                    title: str,
                    module_name: str,
                    description: str = "",
                    priority: Priority = Priority.MEDIUM,
                    estimated_hours: float = 1.0,
                    dependencies: List[str] = None,
                    tags: List[str] = None) -> Task:
        """Create a new task."""
        task_id = self._generate_task_id(title, module_name)
        
        task = Task(
            id=task_id,
            title=title,
            description=description,
            module_name=module_name,
            priority=priority,
            estimated_hours=estimated_hours,
            dependencies=dependencies or [],
            tags=tags or []
        )
        
        self.tasks[task_id] = task
        
        # Add to module
        if module_name in self.modules:
            self.modules[module_name].tasks.append(task_id)
        
        self._save_state()
        logger.info(f"Created task: {task_id}")
        return task
    
    def _generate_task_id(self, title: str, module_name: str) -> str:
        """Generate unique task ID."""
        base = f"{module_name}_{title}".lower().replace(' ', '_').replace('-', '_')
        base = ''.join(c for c in base if c.isalnum() or c == '_')
        
        # Ensure uniqueness
        task_id = base
        counter = 1
        while task_id in self.tasks:
            task_id = f"{base}_{counter}"
            counter += 1
        
        return task_id
    
    def update_task_status(self, task_id: str, status: TaskStatus, note: str = "") -> Task:
        """Update task status with optional note."""
        if task_id not in self.tasks:
            raise ValueError(f"Task not found: {task_id}")
        
        task = self.tasks[task_id]
        old_status = task.status
        task.status = status
        task.last_updated = datetime.now()
        
        if note:
            task.notes.append({
                'timestamp': datetime.now().isoformat(),
                'old_status': old_status.value,
                'new_status': status.value,
                'note': note
            })
        
        if status == TaskStatus.IN_PROGRESS and not task.started_at:
            task.started_at = datetime.now()
        elif status == TaskStatus.COMPLETED:
            task.completed_at = datetime.now()
        
        # Update parent epic progress
        self._update_epic_from_tasks(task)
        
        self._save_state()
        logger.info(f"Updated task {task_id}: {old_status.value} -> {status.value}")
        return task
    
    def log_time(self, task_id: str, hours: float, note: str = "") -> Task:
        """Log time spent on a task."""
        if task_id not in self.tasks:
            raise ValueError(f"Task not found: {task_id}")
        
        task = self.tasks[task_id]
        task.actual_hours += hours
        task.last_updated = datetime.now()
        
        if note:
            task.notes.append({
                'timestamp': datetime.now().isoformat(),
                'type': 'time_log',
                'hours': hours,
                'note': note
            })
        
        self._save_state()
        logger.info(f"Logged {hours}h on task {task_id}")
        return task
    
    def block_task(self, task_id: str, reason: str, blocked_by: List[str] = None) -> Task:
        """Mark a task as blocked."""
        if task_id not in self.tasks:
            raise ValueError(f"Task not found: {task_id}")
        
        task = self.tasks[task_id]
        task.status = TaskStatus.BLOCKED
        task.blocked_by = blocked_by or []
        task.last_updated = datetime.now()
        
        task.notes.append({
            'timestamp': datetime.now().isoformat(),
            'type': 'blocked',
            'reason': reason,
            'blocked_by': task.blocked_by
        })
        
        self._save_state()
        logger.info(f"Blocked task {task_id}: {reason}")
        return task
    
    def unblock_task(self, task_id: str, note: str = "") -> Task:
        """Unblock a task."""
        if task_id not in self.tasks:
            raise ValueError(f"Task not found: {task_id}")
        
        task = self.tasks[task_id]
        task.status = TaskStatus.IN_PROGRESS
        task.blocked_by = []
        task.last_updated = datetime.now()
        
        if note:
            task.notes.append({
                'timestamp': datetime.now().isoformat(),
                'type': 'unblocked',
                'note': note
            })
        
        self._save_state()
        logger.info(f"Unblocked task {task_id}")
        return task
    
    def get_ready_tasks(self) -> List[Task]:
        """Get all tasks that are ready to be worked on."""
        ready = []
        
        for task in self.tasks.values():
            if task.status != TaskStatus.PLANNED:
                continue
            
            if task.blocked_by:
                continue
            
            # Check dependencies
            deps_met = all(
                dep_id in self.tasks and self.tasks[dep_id].status == TaskStatus.COMPLETED
                for dep_id in task.dependencies
            )
            
            if deps_met:
                ready.append(task)
        
        return sorted(ready, key=lambda t: (t.priority.value, t.created_at))
    
    def get_blocked_tasks(self) -> List[Task]:
        """Get all blocked tasks."""
        return [t for t in self.tasks.values() if t.status == TaskStatus.BLOCKED]
    
    def get_overdue_tasks(self) -> List[Task]:
        """Get all overdue tasks."""
        return [t for t in self.tasks.values() if t.is_overdue]
    
    # ============================================================
    # EPIC MANAGEMENT
    # ============================================================
    
    def create_epic(self,
                    title: str,
                    description: str = "",
                    priority: Priority = Priority.MEDIUM,
                    target_completion: Optional[datetime] = None,
                    owner: Optional[str] = None,
                    tags: List[str] = None) -> Epic:
        """Create a new epic."""
        epic_id = self._generate_epic_id(title)
        
        epic = Epic(
            id=epic_id,
            title=title,
            description=description,
            priority=priority,
            target_completion=target_completion,
            owner=owner,
            tags=tags or []
        )
        
        self.epics[epic_id] = epic
        self._save_state()
        logger.info(f"Created epic: {epic_id}")
        return epic
    
    def _generate_epic_id(self, title: str) -> str:
        """Generate unique epic ID."""
        base = f"EPIC_{title}".lower().replace(' ', '_').replace('-', '_')
        base = ''.join(c for c in base if c.isalnum() or c == '_')
        
        epic_id = base
        counter = 1
        while epic_id in self.epics:
            epic_id = f"{base}_{counter}"
            counter += 1
        
        return epic_id
    
    def add_task_to_epic(self, epic_id: str, task_id: str):
        """Add a task to an epic."""
        if epic_id not in self.epics:
            raise ValueError(f"Epic not found: {epic_id}")
        if task_id not in self.tasks:
            raise ValueError(f"Task not found: {task_id}")
        
        epic = self.epics[epic_id]
        if task_id not in epic.tasks:
            epic.tasks.append(task_id)
        
        self._save_state()
        logger.info(f"Added task {task_id} to epic {epic_id}")
    
    def update_epic_status(self, epic_id: str, status: EpicStatus) -> Epic:
        """Update epic status."""
        if epic_id not in self.epics:
            raise ValueError(f"Epic not found: {epic_id}")
        
        epic = self.epics[epic_id]
        epic.status = status
        
        if status == EpicStatus.IN_PROGRESS and not epic.started_at:
            epic.started_at = datetime.now()
        elif status == EpicStatus.COMPLETED:
            epic.completed_at = datetime.now()
        
        self._save_state()
        logger.info(f"Updated epic {epic_id}: {status.value}")
        return epic
    
    def _update_epic_from_tasks(self, task: Task):
        """Update epic status based on task changes."""
        for epic in self.epics.values():
            if task.id in epic.tasks:
                # Recalculate epic progress
                progress = epic.calculate_progress(self.tasks)
                
                if progress >= 100 and epic.status != EpicStatus.COMPLETED:
                    epic.status = EpicStatus.COMPLETED
                    epic.completed_at = datetime.now()
                elif progress > 0 and epic.status == EpicStatus.PLANNED:
                    epic.status = EpicStatus.IN_PROGRESS
                    epic.started_at = datetime.now()
                
                break
    
    # ============================================================
    # MODULE MANAGEMENT
    # ============================================================
    
    def register_module(self,
                        name: str,
                        path: Path,
                        description: str = "",
                        dependencies: List[str] = None) -> Module:
        """Register a code module for tracking."""
        if name in self.modules:
            return self.modules[name]
        
        module = Module(
            name=name,
            description=description,
            path=path,
            dependencies=dependencies or []
        )
        
        self.modules[name] = module
        self._save_state()
        logger.info(f"Registered module: {name}")
        return module
    
    def update_module_metrics(self, module_name: str, 
                               lines_of_code: int = None,
                               test_coverage: float = None):
        """Update module code metrics."""
        if module_name not in self.modules:
            return
        
        module = self.modules[module_name]
        if lines_of_code is not None:
            module.lines_of_code = lines_of_code
        if test_coverage is not None:
            module.test_coverage = test_coverage
        
        self._save_state()
    
    def mark_module_complete(self, module_name: str) -> Module:
        """Mark a module as complete."""
        if module_name not in self.modules:
            raise ValueError(f"Module not found: {module_name}")
        
        module = self.modules[module_name]
        module.status = TaskStatus.COMPLETED
        module.completed_at = datetime.now()
        
        self._save_state()
        logger.info(f"Marked module {module_name} as complete")
        return module
    
    # ============================================================
    # MILESTONE MANAGEMENT
    # ============================================================
    
    def create_milestone(self,
                         title: str,
                         target_date: datetime,
                         description: str = "",
                         epics: List[str] = None) -> Milestone:
        """Create a new milestone."""
        milestone_id = self._generate_milestone_id(title)
        
        milestone = Milestone(
            id=milestone_id,
            title=title,
            description=description,
            target_date=target_date,
            epics=epics or []
        )
        
        self.milestones[milestone_id] = milestone
        self._save_state()
        logger.info(f"Created milestone: {milestone_id}")
        return milestone
    
    def _generate_milestone_id(self, title: str) -> str:
        """Generate unique milestone ID."""
        base = f"MS_{title}".lower().replace(' ', '_').replace('-', '_')
        base = ''.join(c for c in base if c.isalnum() or c == '_')
        
        milestone_id = base
        counter = 1
        while milestone_id in self.milestones:
            milestone_id = f"{base}_{counter}"
            counter += 1
        
        return milestone_id
    
    def check_milestone_progress(self, milestone_id: str) -> float:
        """Calculate progress towards a milestone."""
        if milestone_id not in self.milestones:
            raise ValueError(f"Milestone not found: {milestone_id}")
        
        milestone = self.milestones[milestone_id]
        if not milestone.epics:
            return 0.0
        
        total_progress = 0.0
        for epic_id in milestone.epics:
            if epic_id in self.epics:
                total_progress += self.epics[epic_id].calculate_progress(self.tasks)
        
        return total_progress / len(milestone.epics)
    
    # ============================================================
    # SNAPSHOT AND METRICS
    # ============================================================
    
    def take_snapshot(self) -> DailySnapshot:
        """Take a daily snapshot of current progress."""
        # Count tasks
        total_tasks = len(self.tasks)
        completed_tasks = sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED)
        in_progress_tasks = sum(1 for t in self.tasks.values() if t.status == TaskStatus.IN_PROGRESS)
        blocked_tasks = sum(1 for t in self.tasks.values() if t.status == TaskStatus.BLOCKED)
        
        # Count epics
        total_epics = len(self.epics)
        completed_epics = sum(1 for e in self.epics.values() if e.status == EpicStatus.COMPLETED)
        
        # Count modules
        total_modules = len(self.modules)
        completed_modules = sum(1 for m in self.modules.values() if m.status == TaskStatus.COMPLETED)
        
        # Calculate overall progress
        if total_tasks > 0:
            overall_progress = sum(t.progress_percentage for t in self.tasks.values()) / total_tasks
        else:
            overall_progress = 0.0
        
        # Sum lines of code
        total_loc = sum(m.lines_of_code for m in self.modules.values())
        
        # Average test coverage
        if total_modules > 0:
            avg_coverage = sum(m.test_coverage for m in self.modules.values()) / total_modules
        else:
            avg_coverage = 0.0
        
        # Git metrics
        commits_count = len(self.git.get_recent_commits(days=1))
        
        # Calculate velocity (completed tasks in last 7 days)
        one_week_ago = datetime.now() - timedelta(days=7)
        recent_completions = sum(
            1 for t in self.tasks.values()
            if t.status == TaskStatus.COMPLETED and t.completed_at and t.completed_at >= one_week_ago
        )
        velocity = recent_completions / 7.0
        
        snapshot = DailySnapshot(
            date=datetime.now(),
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            in_progress_tasks=in_progress_tasks,
            blocked_tasks=blocked_tasks,
            total_epics=total_epics,
            completed_epics=completed_epics,
            total_modules=total_modules,
            completed_modules=completed_modules,
            overall_progress=overall_progress,
            lines_of_code=total_loc,
            test_coverage=avg_coverage,
            open_issues=0,  # Could integrate with GitHub issues
            closed_issues=0,
            commits_count=commits_count,
            velocity=velocity
        )
        
        self.snapshots.append(snapshot)
        self._save_state()
        logger.info(f"Took snapshot: {snapshot.date.date()}")
        return snapshot
    
    def get_velocity(self, weeks: int = 4) -> float:
        """Calculate average velocity over recent weeks."""
        if len(self.snapshots) < 7:
            return 0.0
        
        recent_snapshots = self.snapshots[-weeks * 7:]
        if not recent_snapshots:
            return 0.0
        
        total_velocity = sum(s.velocity for s in recent_snapshots)
        return total_velocity / len(recent_snapshots)