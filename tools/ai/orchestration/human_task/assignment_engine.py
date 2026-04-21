"""
Assignment Engine for Human Task Management

Manages assignment of human tasks to appropriate team members based on:
- Skill matching and proficiency
- Current workload and availability
- Task priority and deadlines
- Team member preferences
- Historical performance

This implementation provides:

    Human Resource Management: Register/unregister humans with skills, capacity, and preferences
    Task Submission: Submit human tasks with skill requirements, priority, deadlines
    Multiple Assignment Strategies: Skill match, round-robin, least busy, priority-based, deadline-aware, preference-based, hybrid
    Score-Based Matching: Calculate assignment scores based on weighted criteria
    Assignment Lifecycle: Track assignments through pending → assigned → accepted/declined → completed/expired
    Timeout Handling: Auto-expire and reassign stale assignments
    Decline Management: Handle declined assignments with reassignment delay
    Performance Tracking: Track human success rates and response times
    Priority Queues: Process higher priority tasks first
    Persistence: Save all data to state manager
"""

import uuid
import threading
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict
from queue import PriorityQueue

from ...shared.logger import get_logger
from ...shared.state_manager import state_manager
from ...shared.config import config

logger = get_logger(__name__)


class AssignmentStrategy(Enum):
    """Strategies for assigning tasks to humans"""
    SKILL_MATCH = "skill_match"           # Best skill match
    ROUND_ROBIN = "round_robin"           # Even distribution
    LEAST_BUSY = "least_busy"             # Least current workload
    PRIORITY_BASED = "priority_based"     # Priority-driven
    DEADLINE_AWARE = "deadline_aware"     # Deadline-driven
    PREFERENCE_BASED = "preference_based" # Consider human preferences
    HYBRID = "hybrid"                     # Weighted combination


class AssignmentStatus(Enum):
    """Status of a task assignment"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"
    REASSIGNED = "reassigned"
    COMPLETED = "completed"


@dataclass
class HumanResource:
    """Represents a human resource available for task assignment"""
    id: str
    name: str
    email: str
    skills: Dict[str, int]  # skill_name -> proficiency (1-5)
    current_tasks: List[str] = field(default_factory=list)
    max_concurrent_tasks: int = 3
    preferred_task_types: List[str] = field(default_factory=list)
    blocked_until: Optional[datetime] = None
    timezone: str = "UTC"
    average_response_time: float = 0.0  # hours
    success_rate: float = 1.0  # 0-1
    last_assigned: Optional[datetime] = None
    
    @property
    def current_load(self) -> float:
        """Calculate current load percentage (0-1)"""
        if self.max_concurrent_tasks == 0:
            return 1.0
        return len(self.current_tasks) / self.max_concurrent_tasks
    
    @property
    def is_available(self) -> bool:
        """Check if human is available for new tasks"""
        if self.blocked_until and self.blocked_until > datetime.now():
            return False
        return len(self.current_tasks) < self.max_concurrent_tasks
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "skills": self.skills,
            "current_tasks": self.current_tasks,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "preferred_task_types": self.preferred_task_types,
            "blocked_until": self.blocked_until.isoformat() if self.blocked_until else None,
            "timezone": self.timezone,
            "average_response_time": self.average_response_time,
            "success_rate": self.success_rate,
            "last_assigned": self.last_assigned.isoformat() if self.last_assigned else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HumanResource":
        return cls(
            id=data["id"],
            name=data["name"],
            email=data["email"],
            skills=data.get("skills", {}),
            current_tasks=data.get("current_tasks", []),
            max_concurrent_tasks=data.get("max_concurrent_tasks", 3),
            preferred_task_types=data.get("preferred_task_types", []),
            blocked_until=datetime.fromisoformat(data["blocked_until"]) if data.get("blocked_until") else None,
            timezone=data.get("timezone", "UTC"),
            average_response_time=data.get("average_response_time", 0.0),
            success_rate=data.get("success_rate", 1.0),
            last_assigned=datetime.fromisoformat(data["last_assigned"]) if data.get("last_assigned") else None
        )


@dataclass
class HumanTask:
    """Represents a task that requires human intervention"""
    task_id: str
    title: str
    description: str
    required_skills: Dict[str, int]  # skill_name -> minimum proficiency
    priority: int  # 1 (lowest) to 5 (highest)
    deadline: Optional[datetime] = None
    estimated_duration: float = 1.0  # hours
    created_at: datetime = field(default_factory=datetime.now)
    assigned_to: Optional[str] = None
    assignment_status: AssignmentStatus = AssignmentStatus.PENDING
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "required_skills": self.required_skills,
            "priority": self.priority,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "estimated_duration": self.estimated_duration,
            "created_at": self.created_at.isoformat(),
            "assigned_to": self.assigned_to,
            "assignment_status": self.assignment_status.value,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HumanTask":
        return cls(
            task_id=data["task_id"],
            title=data["title"],
            description=data["description"],
            required_skills=data.get("required_skills", {}),
            priority=data.get("priority", 3),
            deadline=datetime.fromisoformat(data["deadline"]) if data.get("deadline") else None,
            estimated_duration=data.get("estimated_duration", 1.0),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            assigned_to=data.get("assigned_to"),
            assignment_status=AssignmentStatus(data["assignment_status"]) if data.get("assignment_status") else AssignmentStatus.PENDING,
            metadata=data.get("metadata", {})
        )


@dataclass
class Assignment:
    """Records a task assignment to a human"""
    assignment_id: str
    task_id: str
    human_id: str
    strategy: AssignmentStrategy
    score: float
    assigned_at: datetime = field(default_factory=datetime.now)
    accepted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: AssignmentStatus = AssignmentStatus.ASSIGNED
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "assignment_id": self.assignment_id,
            "task_id": self.task_id,
            "human_id": self.human_id,
            "strategy": self.strategy.value,
            "score": self.score,
            "assigned_at": self.assigned_at.isoformat(),
            "accepted_at": self.accepted_at.isoformat() if self.accepted_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status.value
        }


class AssignmentEngine:
    """
    Manages assignment of human tasks to appropriate team members.
    
    Features:
    - Skill-based matching
    - Load balancing
    - Priority-aware assignment
    - Deadline management
    - Assignment history tracking
    - Reassignment on decline/timeout
    """
    
    def __init__(self, storage_key: str = "assignment_engine"):
        self.storage_key = storage_key
        self.humans: Dict[str, HumanResource] = {}
        self.tasks: Dict[str, HumanTask] = {}
        self.assignments: Dict[str, Assignment] = {}
        self.assignment_history: List[Assignment] = []
        
        # Queues for different priorities
        self.task_queues: Dict[int, List[str]] = {
            1: [],  # Low
            2: [],  # Medium-Low
            3: [],  # Medium
            4: [],  # Medium-High
            5: []   # High
        }
        
        self._lock = threading.RLock()
        self._assignment_timeout = config.get("human_task.assignment_timeout_hours", 24)
        self._reassignment_delay = config.get("human_task.reassignment_delay_minutes", 30)
        
        # Load data
        self._load_data()
        
        # Start background workers
        self._start_workers()
        
        logger.info("AssignmentEngine initialized")
    
    def _load_data(self) -> None:
        """Load persisted data"""
        try:
            humans_data = state_manager.get(f"{self.storage_key}.humans", {})
            for hid, hdata in humans_data.items():
                self.humans[hid] = HumanResource.from_dict(hdata)
            
            tasks_data = state_manager.get(f"{self.storage_key}.tasks", {})
            for tid, tdata in tasks_data.items():
                self.tasks[tid] = HumanTask.from_dict(tdata)
            
            assignments_data = state_manager.get(f"{self.storage_key}.assignments", {})
            for aid, adata in assignments_data.items():
                self.assignments[aid] = Assignment(**adata)
            
            history_data = state_manager.get(f"{self.storage_key}.history", [])
            for hdata in history_data:
                self.assignment_history.append(Assignment(**hdata))
                
        except Exception as e:
            logger.warning(f"Failed to load assignment data: {e}")
    
    def _save_data(self) -> None:
        """Save data to persistence"""
        try:
            state_manager.set(f"{self.storage_key}.humans", 
                            {hid: h.to_dict() for hid, h in self.humans.items()})
            state_manager.set(f"{self.storage_key}.tasks",
                            {tid: t.to_dict() for tid, t in self.tasks.items()})
            state_manager.set(f"{self.storage_key}.assignments",
                            {aid: a.to_dict() for aid, a in self.assignments.items()})
            
            # Keep last 1000 assignments in history
            history = [a.to_dict() for a in self.assignment_history[-1000:]]
            state_manager.set(f"{self.storage_key}.history", history)
            
        except Exception as e:
            logger.error(f"Failed to save assignment data: {e}")
    
    def _start_workers(self) -> None:
        """Start background workers for assignment processing"""
        import threading
        
        def assignment_worker():
            while True:
                try:
                    self._process_assignments()
                    self._check_expired_assignments()
                except Exception as e:
                    logger.error(f"Assignment worker error: {e}")
                threading.Event().wait(30)  # Check every 30 seconds
        
        worker = threading.Thread(target=assignment_worker, daemon=True)
        worker.start()
    
    def _process_assignments(self) -> None:
        """Process pending assignments from queues"""
        with self._lock:
            # Process higher priority queues first
            for priority in [5, 4, 3, 2, 1]:
                task_ids = self.task_queues[priority]
                if not task_ids:
                    continue
                
                # Process up to 5 tasks per priority per cycle
                for task_id in task_ids[:5]:
                    if task_id not in self.tasks:
                        task_ids.remove(task_id)
                        continue
                    
                    task = self.tasks[task_id]
                    if task.assignment_status == AssignmentStatus.PENDING:
                        assignment = self._assign_task(task)
                        if assignment:
                            task_ids.remove(task_id)
                            task.assigned_to = assignment.human_id
                            task.assignment_status = AssignmentStatus.ASSIGNED
                            self.assignments[assignment.assignment_id] = assignment
                            self._save_data()
    
    def _assign_task(self, task: HumanTask, 
                    strategy: AssignmentStrategy = AssignmentStrategy.HYBRID) -> Optional[Assignment]:
        """Assign a task to the best available human"""
        # Get available humans
        available = [h for h in self.humans.values() if h.is_available]
        
        if not available:
            logger.warning(f"No available humans for task {task.task_id}")
            return None
        
        # Score each human
        scored = []
        for human in available:
            score = self._calculate_score(task, human, strategy)
            if score > 0:
                scored.append((human, score))
        
        if not scored:
            logger.warning(f"No suitable human found for task {task.task_id}")
            return None
        
        # Select best human
        best_human, best_score = max(scored, key=lambda x: x[1])
        
        # Create assignment
        assignment = Assignment(
            assignment_id=str(uuid.uuid4()),
            task_id=task.task_id,
            human_id=best_human.id,
            strategy=strategy,
            score=best_score
        )
        
        # Update human's task list
        best_human.current_tasks.append(task.task_id)
        best_human.last_assigned = datetime.now()
        
        logger.info(f"Assigned task {task.task_id} to {best_human.name} with score {best_score:.2f}")
        
        return assignment
    
    def _calculate_score(self, task: HumanTask, human: HumanResource,
                        strategy: AssignmentStrategy) -> float:
        """Calculate assignment score for a human-task pair"""
        scores = {}
        
        # 1. Skill match score (0-100)
        skill_score = self._calculate_skill_match(task.required_skills, human.skills)
        scores["skill"] = skill_score
        
        # 2. Load balance score (0-100)
        load_score = (1 - human.current_load) * 100
        scores["load"] = load_score
        
        # 3. Priority score (0-100)
        priority_score = (task.priority / 5) * 100
        scores["priority"] = priority_score
        
        # 4. Deadline urgency score (0-100)
        deadline_score = self._calculate_deadline_score(task)
        scores["deadline"] = deadline_score
        
        # 5. Preference score (0-100)
        preference_score = self._calculate_preference_score(task, human)
        scores["preference"] = preference_score
        
        # 6. Performance score (0-100)
        performance_score = human.success_rate * 100
        scores["performance"] = performance_score
        
        # 7. Recency score (0-100) - avoid assigning same person repeatedly
        recency_score = self._calculate_recency_score(human)
        scores["recency"] = recency_score
        
        # Weighted combination based on strategy
        weights = self._get_strategy_weights(strategy)
        
        total_score = sum(scores.get(key, 0) * weight for key, weight in weights.items())
        
        return total_score
    
    def _calculate_skill_match(self, required: Dict[str, int], 
                              available: Dict[str, int]) -> float:
        """Calculate skill match percentage (0-100)"""
        if not required:
            return 100.0
        
        total_required = len(required)
        total_score = 0
        
        for skill, required_level in required.items():
            available_level = available.get(skill, 0)
            if available_level >= required_level:
                total_score += 100
            else:
                # Partial credit for close levels
                total_score += (available_level / required_level) * 100
        
        return total_score / total_required
    
    def _calculate_deadline_score(self, task: HumanTask) -> float:
        """Calculate deadline urgency score (0-100)"""
        if not task.deadline:
            return 50.0
        
        now = datetime.now()
        time_left = (task.deadline - now).total_seconds() / 3600  # hours
        
        if time_left <= 0:
            return 100.0  # Urgent
        elif time_left <= 1:
            return 90.0
        elif time_left <= 4:
            return 70.0
        elif time_left <= 12:
            return 50.0
        elif time_left <= 24:
            return 30.0
        else:
            return 10.0
    
    def _calculate_preference_score(self, task: HumanTask, 
                                   human: HumanResource) -> float:
        """Calculate preference score based on human preferences"""
        if not human.preferred_task_types:
            return 50.0
        
        task_type = task.metadata.get("task_type", "")
        if task_type in human.preferred_task_types:
            return 100.0
        
        return 50.0
    
    def _calculate_recency_score(self, human: HumanResource) -> float:
        """Calculate recency score to ensure fair distribution"""
        if not human.last_assigned:
            return 100.0
        
        hours_since = (datetime.now() - human.last_assigned).total_seconds() / 3600
        
        if hours_since >= 8:  # Been a while
            return 100.0
        elif hours_since >= 4:
            return 70.0
        elif hours_since >= 1:
            return 40.0
        else:
            return 20.0
    
    def _get_strategy_weights(self, strategy: AssignmentStrategy) -> Dict[str, float]:
        """Get weight distribution for assignment strategies"""
        weights = {
            AssignmentStrategy.SKILL_MATCH: {"skill": 1.0},
            AssignmentStrategy.ROUND_ROBIN: {"recency": 0.6, "load": 0.4},
            AssignmentStrategy.LEAST_BUSY: {"load": 1.0},
            AssignmentStrategy.PRIORITY_BASED: {"priority": 0.6, "skill": 0.4},
            AssignmentStrategy.DEADLINE_AWARE: {"deadline": 0.7, "skill": 0.3},
            AssignmentStrategy.PREFERENCE_BASED: {"preference": 0.5, "skill": 0.5},
            AssignmentStrategy.HYBRID: {
                "skill": 0.30,
                "load": 0.20,
                "priority": 0.15,
                "deadline": 0.15,
                "preference": 0.10,
                "performance": 0.10
            }
        }
        return weights.get(strategy, weights[AssignmentStrategy.HYBRID])
    
    def _check_expired_assignments(self) -> None:
        """Check for expired assignments and reassign"""
        timeout_hours = self._assignment_timeout
        
        with self._lock:
            for assignment in list(self.assignments.values()):
                if assignment.status == AssignmentStatus.ASSIGNED:
                    time_since = (datetime.now() - assignment.assigned_at).total_seconds() / 3600
                    
                    if time_since > timeout_hours:
                        logger.warning(f"Assignment {assignment.assignment_id} expired")
                        assignment.status = AssignmentStatus.EXPIRED
                        
                        # Reassign task
                        task = self.tasks.get(assignment.task_id)
                        if task:
                            task.assignment_status = AssignmentStatus.PENDING
                            task.assigned_to = None
                            self._add_to_queue(task)
                            
                            # Remove from human's tasks
                            human = self.humans.get(assignment.human_id)
                            if human and assignment.task_id in human.current_tasks:
                                human.current_tasks.remove(assignment.task_id)
                        
                        self._save_data()
    
    def _add_to_queue(self, task: HumanTask) -> None:
        """Add task to priority queue"""
        with self._lock:
            if task.task_id not in self.task_queues[task.priority]:
                self.task_queues[task.priority].append(task.task_id)
    
    def register_human(self, human: HumanResource) -> str:
        """Register a human resource"""
        with self._lock:
            self.humans[human.id] = human
            self._save_data()
            logger.info(f"Registered human: {human.name} ({human.id})")
            return human.id
    
    def unregister_human(self, human_id: str) -> bool:
        """Unregister a human resource"""
        with self._lock:
            if human_id in self.humans:
                # Reassign their tasks
                human = self.humans[human_id]
                for task_id in human.current_tasks:
                    task = self.tasks.get(task_id)
                    if task and task.assignment_status == AssignmentStatus.ASSIGNED:
                        task.assignment_status = AssignmentStatus.PENDING
                        task.assigned_to = None
                        self._add_to_queue(task)
                
                del self.humans[human_id]
                self._save_data()
                logger.info(f"Unregistered human: {human_id}")
                return True
        return False
    
    def submit_task(self, task: HumanTask) -> str:
        """Submit a task for assignment"""
        with self._lock:
            self.tasks[task.task_id] = task
            self._add_to_queue(task)
            self._save_data()
            logger.info(f"Submitted task: {task.title} ({task.task_id})")
            return task.task_id
    
    def accept_assignment(self, assignment_id: str, human_id: str) -> bool:
        """Accept a task assignment"""
        with self._lock:
            assignment = self.assignments.get(assignment_id)
            if not assignment or assignment.human_id != human_id:
                return False
            
            if assignment.status == AssignmentStatus.ASSIGNED:
                assignment.status = AssignmentStatus.ACCEPTED
                assignment.accepted_at = datetime.now()
                
                task = self.tasks.get(assignment.task_id)
                if task:
                    task.assignment_status = AssignmentStatus.ACCEPTED
                
                self._save_data()
                logger.info(f"Assignment {assignment_id} accepted by {human_id}")
                return True
        return False
    
    def decline_assignment(self, assignment_id: str, human_id: str, 
                          reason: str = None) -> bool:
        """Decline a task assignment"""
        with self._lock:
            assignment = self.assignments.get(assignment_id)
            if not assignment or assignment.human_id != human_id:
                return False
            
            if assignment.status == AssignmentStatus.ASSIGNED:
                assignment.status = AssignmentStatus.DECLINED
                
                # Reassign task
                task = self.tasks.get(assignment.task_id)
                if task:
                    task.assignment_status = AssignmentStatus.PENDING
                    task.assigned_to = None
                    
                    # Add delay before reassigning
                    reassign_time = datetime.now() + timedelta(minutes=self._reassignment_delay)
                    task.metadata["reassign_after"] = reassign_time.isoformat()
                    self._add_to_queue(task)
                
                # Remove from human's tasks
                human = self.humans.get(human_id)
                if human and assignment.task_id in human.current_tasks:
                    human.current_tasks.remove(assignment.task_id)
                
                self._save_data()
                logger.info(f"Assignment {assignment_id} declined by {human_id}: {reason}")
                return True
        return False
    
    def complete_task(self, task_id: str, human_id: str, 
                     result: Dict[str, Any] = None) -> bool:
        """Mark a task as completed"""
        with self._lock:
            task = self.tasks.get(task_id)
            if not task or task.assigned_to != human_id:
                return False
            
            # Find assignment
            assignment = None
            for a in self.assignments.values():
                if a.task_id == task_id and a.human_id == human_id:
                    assignment = a
                    break
            
            if assignment:
                assignment.status = AssignmentStatus.COMPLETED
                assignment.completed_at = datetime.now()
                
                # Move to history
                self.assignment_history.append(assignment)
                if len(self.assignment_history) > 1000:
                    self.assignment_history.pop(0)
            
            task.assignment_status = AssignmentStatus.COMPLETED
            
            # Update human's performance
            human = self.humans.get(human_id)
            if human:
                if task_id in human.current_tasks:
                    human.current_tasks.remove(task_id)
                
                # Update success rate
                total_completed = sum(1 for a in self.assignment_history 
                                    if a.human_id == human_id and a.status == AssignmentStatus.COMPLETED)
                total_assigned = sum(1 for a in self.assignment_history 
                                   if a.human_id == human_id)
                human.success_rate = total_completed / total_assigned if total_assigned > 0 else 1.0
            
            self._save_data()
            logger.info(f"Task {task_id} completed by {human_id}")
            return True
    
    def reassign_task(self, task_id: str, new_human_id: str = None) -> Optional[Assignment]:
        """Force reassignment of a task"""
        with self._lock:
            task = self.tasks.get(task_id)
            if not task:
                return None
            
            # Remove old assignment
            old_human_id = task.assigned_to
            if old_human_id:
                old_human = self.humans.get(old_human_id)
                if old_human and task_id in old_human.current_tasks:
                    old_human.current_tasks.remove(task_id)
            
            # Create new assignment
            if new_human_id:
                new_human = self.humans.get(new_human_id)
                if not new_human or not new_human.is_available:
                    return None
                
                assignment = Assignment(
                    assignment_id=str(uuid.uuid4()),
                    task_id=task_id,
                    human_id=new_human_id,
                    strategy=AssignmentStrategy.HYBRID,
                    score=100.0,
                    status=AssignmentStatus.ASSIGNED
                )
                
                task.assigned_to = new_human_id
                task.assignment_status = AssignmentStatus.ASSIGNED
                new_human.current_tasks.append(task_id)
                
            else:
                # Auto-assign
                assignment = self._assign_task(task)
                if not assignment:
                    return None
            
            self.assignments[assignment.assignment_id] = assignment
            self._save_data()
            
            logger.info(f"Task {task_id} reassigned to {assignment.human_id}")
            return assignment
    
    def get_human_tasks(self, human_id: str) -> List[Dict[str, Any]]:
        """Get all tasks assigned to a human"""
        with self._lock:
            human = self.humans.get(human_id)
            if not human:
                return []
            
            tasks = []
            for task_id in human.current_tasks:
                task = self.tasks.get(task_id)
                if task:
                    tasks.append({
                        "task_id": task.task_id,
                        "title": task.title,
                        "description": task.description,
                        "priority": task.priority,
                        "deadline": task.deadline.isoformat() if task.deadline else None,
                        "status": task.assignment_status.value,
                        "estimated_duration": task.estimated_duration
                    })
            return tasks
    
    def get_pending_tasks(self) -> List[Dict[str, Any]]:
        """Get all pending tasks awaiting assignment"""
        with self._lock:
            pending = []
            for task in self.tasks.values():
                if task.assignment_status == AssignmentStatus.PENDING:
                    pending.append({
                        "task_id": task.task_id,
                        "title": task.title,
                        "priority": task.priority,
                        "required_skills": task.required_skills,
                        "deadline": task.deadline.isoformat() if task.deadline else None,
                        "created_at": task.created_at.isoformat()
                    })
            return sorted(pending, key=lambda t: -t["priority"])
    
    def get_available_humans(self) -> List[Dict[str, Any]]:
        """Get all available humans"""
        with self._lock:
            return [
                {
                    "id": h.id,
                    "name": h.name,
                    "skills": h.skills,
                    "current_load": h.current_load,
                    "current_tasks": len(h.current_tasks),
                    "max_tasks": h.max_concurrent_tasks,
                    "success_rate": h.success_rate
                }
                for h in self.humans.values() if h.is_available
            ]
    
    def update_human_skill(self, human_id: str, skill_name: str, 
                          proficiency: int) -> bool:
        """Update a human's skill proficiency"""
        with self._lock:
            human = self.humans.get(human_id)
            if not human:
                return False
            
            human.skills[skill_name] = max(1, min(5, proficiency))
            self._save_data()
            return True
    
    def get_assignment_statistics(self) -> Dict[str, Any]:
        """Get assignment statistics"""
        with self._lock:
            total_assignments = len(self.assignment_history) + len(self.assignments)
            completed = sum(1 for a in self.assignment_history if a.status == AssignmentStatus.COMPLETED)
            declined = sum(1 for a in self.assignment_history if a.status == AssignmentStatus.DECLINED)
            expired = sum(1 for a in self.assignment_history if a.status == AssignmentStatus.EXPIRED)
            
            # Average assignment score
            avg_score = sum(a.score for a in self.assignments.values()) / len(self.assignments) if self.assignments else 0
            
            return {
                "total_humans": len(self.humans),
                "available_humans": len([h for h in self.humans.values() if h.is_available]),
                "pending_tasks": len([t for t in self.tasks.values() if t.assignment_status == AssignmentStatus.PENDING]),
                "assigned_tasks": len([t for t in self.tasks.values() if t.assignment_status == AssignmentStatus.ASSIGNED]),
                "total_assignments": total_assignments,
                "completed_assignments": completed,
                "declined_assignments": declined,
                "expired_assignments": expired,
                "average_assignment_score": avg_score,
                "tasks_by_priority": {
                    p: len(q) for p, q in self.task_queues.items()
                }
            }


# Singleton instance
_assignment_engine: Optional[AssignmentEngine] = None


def get_assignment_engine() -> AssignmentEngine:
    """Get global AssignmentEngine instance"""
    global _assignment_engine
    if _assignment_engine is None:
        _assignment_engine = AssignmentEngine()
    return _assignment_engine