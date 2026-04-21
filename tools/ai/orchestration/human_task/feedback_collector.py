"""
Feedback Collector for Human Task Management

Collects, processes, and analyzes feedback from human interactions including:
- Task completion feedback
- Quality ratings and reviews
- Process improvement suggestions
- Human satisfaction metrics
- Learning and training data
- Feedback aggregation and reporting

This implementation provides:

    Multi-Type Feedback Collection: Task completion, quality ratings, satisfaction, suggestions, issue reports, training data
    Feedback Lifecycle Management: Submitted → Acknowledged → Reviewed → Actioned → Resolved
    Severity Levels: INFO, MINOR, MAJOR, CRITICAL, BLOCKER
    Auto-Escalation: Critical issues automatically escalated
    Satisfaction Metrics: Track human satisfaction over time (daily/weekly/monthly)
    Trend Analysis: Analyze feedback trends over time
    Summary Reports: Generate period-based feedback summaries
    High-Impact Detection: Identify critical feedback that needs attention
    Convenience Methods: Easy submission for common feedback types
    Callback System: Notify listeners of new or escalated feedback

Persistence: Uses shared state manager for storage (no separate persistence layer)
"""

import uuid
import threading
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, Counter

from ...shared.logger import get_logger
from ...shared.state_manager import state_manager
from ...shared.config import config

logger = get_logger(__name__)


class FeedbackType(Enum):
    """Types of feedback that can be collected"""
    TASK_COMPLETION = "task_completion"      # Task completed successfully
    QUALITY_RATING = "quality_rating"        # Rating of output quality
    SATISFACTION = "satisfaction"            # Human satisfaction score
    SUGGESTION = "suggestion"                # Process improvement suggestion
    ISSUE_REPORT = "issue_report"            # Problem or bug report
    CLARIFICATION = "clarification"          # Need for clarification
    PRAISE = "praise"                        # Positive feedback
    CRITIQUE = "critique"                    # Constructive criticism
    TRAINING_DATA = "training_data"          # Data for model training
    CORRECTION = "correction"                # Correction of previous output


class FeedbackSeverity(Enum):
    """Severity levels for feedback"""
    INFO = "info"          # Informational
    MINOR = "minor"        # Minor issue or suggestion
    MAJOR = "major"        # Significant issue
    CRITICAL = "critical"  # Critical problem
    BLOCKER = "blocker"    # Blocks further work


class FeedbackStatus(Enum):
    """Status of feedback processing"""
    SUBMITTED = "submitted"
    ACKNOWLEDGED = "acknowledged"
    REVIEWED = "reviewed"
    ACTIONED = "actioned"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


@dataclass
class Feedback:
    """Represents a feedback entry"""
    feedback_id: str
    type: FeedbackType
    source: str  # Human ID or system component
    target: str  # Task ID, Workflow ID, or Component
    content: str
    rating: Optional[int] = None  # 1-5 stars
    severity: FeedbackSeverity = FeedbackSeverity.INFO
    status: FeedbackStatus = FeedbackStatus.SUBMITTED
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "feedback_id": self.feedback_id,
            "type": self.type.value,
            "source": self.source,
            "target": self.target,
            "content": self.content,
            "rating": self.rating,
            "severity": self.severity.value,
            "status": self.status.value,
            "tags": self.tags,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolution_notes": self.resolution_notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Feedback":
        return cls(
            feedback_id=data["feedback_id"],
            type=FeedbackType(data["type"]),
            source=data["source"],
            target=data["target"],
            content=data["content"],
            rating=data.get("rating"),
            severity=FeedbackSeverity(data.get("severity", "info")),
            status=FeedbackStatus(data.get("status", "submitted")),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            acknowledged_at=datetime.fromisoformat(data["acknowledged_at"]) if data.get("acknowledged_at") else None,
            resolved_at=datetime.fromisoformat(data["resolved_at"]) if data.get("resolved_at") else None,
            resolution_notes=data.get("resolution_notes")
        )


@dataclass
class FeedbackSummary:
    """Aggregated feedback summary for reporting"""
    period_start: datetime
    period_end: datetime
    total_feedback: int
    by_type: Dict[str, int]
    by_severity: Dict[str, int]
    by_status: Dict[str, int]
    average_rating: float
    top_issues: List[Dict[str, Any]]
    resolved_count: int
    pending_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "total_feedback": self.total_feedback,
            "by_type": self.by_type,
            "by_severity": self.by_severity,
            "by_status": self.by_status,
            "average_rating": self.average_rating,
            "top_issues": self.top_issues,
            "resolved_count": self.resolved_count,
            "pending_count": self.pending_count
        }


@dataclass
class HumanSatisfactionMetric:
    """Tracks human satisfaction metrics over time"""
    human_id: str
    period: str  # daily, weekly, monthly
    average_rating: float
    total_responses: int
    positive_percentage: float
    negative_percentage: float
    neutral_percentage: float
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "human_id": self.human_id,
            "period": self.period,
            "average_rating": self.average_rating,
            "total_responses": self.total_responses,
            "positive_percentage": self.positive_percentage,
            "negative_percentage": self.negative_percentage,
            "neutral_percentage": self.neutral_percentage,
            "timestamp": self.timestamp.isoformat()
        }


class FeedbackCollector:
    """
    Collects and processes feedback from human interactions.
    
    Features:
    - Multi-type feedback collection
    - Rating and sentiment analysis
    - Feedback aggregation and reporting
    - Trend analysis
    - Escalation for critical issues
    - Integration with improvement workflows
    """
    
    def __init__(self, storage_key: str = "feedback_collector"):
        self.storage_key = storage_key
        self.feedback: Dict[str, Feedback] = {}
        self.feedback_history: List[Feedback] = []
        self.satisfaction_metrics: List[HumanSatisfactionMetric] = []
        
        # Aggregated data
        self._feedback_cache: Dict[str, Any] = {}
        self._lock = threading.RLock()
        
        # Configuration
        self.escalation_threshold = config.get("feedback.escalation_threshold", 4)  # Rating <= this escalates
        self.auto_acknowledge = config.get("feedback.auto_acknowledge", True)
        self.retention_days = config.get("feedback.retention_days", 90)
        
        # Callbacks
        self._on_feedback_received: List[Any] = []
        self._on_feedback_escalated: List[Any] = []
        
        # Load data
        self._load_data()
        
        logger.info("FeedbackCollector initialized")
    
    def _load_data(self) -> None:
        """Load feedback data from state manager"""
        try:
            feedback_data = state_manager.get(f"{self.storage_key}.feedback", {})
            for fid, fdata in feedback_data.items():
                if isinstance(fdata, dict):
                    self.feedback[fid] = Feedback.from_dict(fdata)
            
            history_data = state_manager.get(f"{self.storage_key}.history", [])
            for hdata in history_data[-1000:]:  # Keep last 1000
                if isinstance(hdata, dict):
                    self.feedback_history.append(Feedback.from_dict(hdata))
            
            metrics_data = state_manager.get(f"{self.storage_key}.satisfaction", [])
            for mdata in metrics_data:
                if isinstance(mdata, dict):
                    self.satisfaction_metrics.append(HumanSatisfactionMetric(**mdata))
                    
        except Exception as e:
            logger.warning(f"Failed to load feedback data: {e}")
    
    def _save_data(self) -> None:
        """Save feedback data to state manager"""
        try:
            state_manager.set(f"{self.storage_key}.feedback", 
                            {fid: f.to_dict() for fid, f in self.feedback.items()})
            
            # Keep last 1000 in history
            history = [f.to_dict() for f in self.feedback_history[-1000:]]
            state_manager.set(f"{self.storage_key}.history", history)
            
            metrics = [m.to_dict() for m in self.satisfaction_metrics[-1000:]]
            state_manager.set(f"{self.storage_key}.satisfaction", metrics)
            
        except Exception as e:
            logger.error(f"Failed to save feedback data: {e}")
    
    def submit_feedback(self, feedback: Feedback) -> str:
        """
        Submit new feedback.
        
        Args:
            feedback: Feedback object
            
        Returns:
            Feedback ID
        """
        with self._lock:
            self.feedback[feedback.feedback_id] = feedback
            
            # Auto-acknowledge if configured
            if self.auto_acknowledge:
                feedback.status = FeedbackStatus.ACKNOWLEDGED
                feedback.acknowledged_at = datetime.now()
            
            # Check if needs escalation
            if self._needs_escalation(feedback):
                feedback.status = FeedbackStatus.ESCALATED
                self._notify_escalated(feedback)
            
            # Add to history
            self.feedback_history.append(feedback)
            
            # Update cache
            self._update_cache(feedback)
            
            self._save_data()
            
            # Notify listeners
            self._notify_feedback_received(feedback)
            
            logger.info(f"Feedback {feedback.feedback_id} submitted: {feedback.type.value}")
            
            return feedback.feedback_id
    
    def _needs_escalation(self, feedback: Feedback) -> bool:
        """Check if feedback needs escalation"""
        if feedback.severity in [FeedbackSeverity.CRITICAL, FeedbackSeverity.BLOCKER]:
            return True
        
        if feedback.rating and feedback.rating <= self.escalation_threshold:
            return True
        
        return False
    
    def submit_task_feedback(self, task_id: str, human_id: str,
                            rating: int, comment: str,
                            tags: List[str] = None) -> str:
        """
        Convenience method for task completion feedback.
        
        Args:
            task_id: Task being rated
            human_id: Human providing feedback
            rating: Rating 1-5
            comment: Feedback comment
            tags: Optional tags
            
        Returns:
            Feedback ID
        """
        severity = FeedbackSeverity.CRITICAL if rating <= 2 else FeedbackSeverity.MINOR if rating <= 3 else FeedbackSeverity.INFO
        
        feedback = Feedback(
            feedback_id=str(uuid.uuid4()),
            type=FeedbackType.TASK_COMPLETION,
            source=human_id,
            target=task_id,
            content=comment,
            rating=rating,
            severity=severity,
            tags=tags or [],
            metadata={"task_type": "human_task"}
        )
        
        return self.submit_feedback(feedback)
    
    def submit_quality_rating(self, target_id: str, source: str,
                             rating: int, comment: str,
                             target_type: str = "workflow") -> str:
        """
        Submit quality rating for a workflow or task output.
        
        Args:
            target_id: ID of workflow/task being rated
            source: Human ID providing feedback
            rating: Rating 1-5
            comment: Feedback comment
            target_type: Type of target (workflow, task, agent_output)
            
        Returns:
            Feedback ID
        """
        feedback = Feedback(
            feedback_id=str(uuid.uuid4()),
            type=FeedbackType.QUALITY_RATING,
            source=source,
            target=target_id,
            content=comment,
            rating=rating,
            severity=FeedbackSeverity.MAJOR if rating <= 2 else FeedbackSeverity.INFO,
            tags=[target_type],
            metadata={"target_type": target_type}
        )
        
        return self.submit_feedback(feedback)
    
    def submit_suggestion(self, human_id: str, suggestion: str,
                         category: str = "improvement") -> str:
        """
        Submit a process improvement suggestion.
        
        Args:
            human_id: Human providing suggestion
            suggestion: Suggestion text
            category: Suggestion category
            
        Returns:
            Feedback ID
        """
        feedback = Feedback(
            feedback_id=str(uuid.uuid4()),
            type=FeedbackType.SUGGESTION,
            source=human_id,
            target="system",
            content=suggestion,
            severity=FeedbackSeverity.INFO,
            tags=[category],
            metadata={"category": category}
        )
        
        return self.submit_feedback(feedback)
    
    def submit_issue_report(self, human_id: str, issue: str,
                           severity: FeedbackSeverity,
                           component: str = None) -> str:
        """
        Submit an issue or bug report.
        
        Args:
            human_id: Human reporting issue
            issue: Issue description
            severity: Issue severity
            component: Affected component
            
        Returns:
            Feedback ID
        """
        feedback = Feedback(
            feedback_id=str(uuid.uuid4()),
            type=FeedbackType.ISSUE_REPORT,
            source=human_id,
            target=component or "system",
            content=issue,
            severity=severity,
            tags=["bug", component] if component else ["bug"],
            metadata={"component": component}
        )
        
        return self.submit_feedback(feedback)
    
    def submit_training_data(self, human_id: str, task_id: str,
                            input_data: Dict, output_data: Dict,
                            quality_rating: int) -> str:
        """
        Submit training data for model improvement.
        
        Args:
            human_id: Human providing data
            task_id: Task this data relates to
            input_data: Input that was provided
            output_data: Output that was produced
            quality_rating: Rating of output quality
            
        Returns:
            Feedback ID
        """
        feedback = Feedback(
            feedback_id=str(uuid.uuid4()),
            type=FeedbackType.TRAINING_DATA,
            source=human_id,
            target=task_id,
            content="Training data submission",
            rating=quality_rating,
            tags=["training"],
            metadata={
                "input": input_data,
                "output": output_data
            }
        )
        
        return self.submit_feedback(feedback)
    
    def acknowledge_feedback(self, feedback_id: str, 
                            reviewer: str = "system") -> bool:
        """Mark feedback as acknowledged"""
        with self._lock:
            feedback = self.feedback.get(feedback_id)
            if not feedback:
                return False
            
            feedback.status = FeedbackStatus.ACKNOWLEDGED
            feedback.acknowledged_at = datetime.now()
            feedback.metadata["reviewed_by"] = reviewer
            
            self._save_data()
            return True
    
    def resolve_feedback(self, feedback_id: str, 
                        resolution_notes: str,
                        resolver: str = "system") -> bool:
        """Mark feedback as resolved with resolution notes"""
        with self._lock:
            feedback = self.feedback.get(feedback_id)
            if not feedback:
                return False
            
            feedback.status = FeedbackStatus.RESOLVED
            feedback.resolved_at = datetime.now()
            feedback.resolution_notes = resolution_notes
            feedback.metadata["resolved_by"] = resolver
            
            self._save_data()
            return True
    
    def dismiss_feedback(self, feedback_id: str, reason: str) -> bool:
        """Dismiss feedback without action"""
        with self._lock:
            feedback = self.feedback.get(feedback_id)
            if not feedback:
                return False
            
            feedback.status = FeedbackStatus.DISMISSED
            feedback.resolution_notes = f"Dismissed: {reason}"
            feedback.resolved_at = datetime.now()
            
            self._save_data()
            return True
    
    def get_feedback(self, feedback_id: str) -> Optional[Dict[str, Any]]:
        """Get feedback by ID"""
        with self._lock:
            feedback = self.feedback.get(feedback_id)
            if feedback:
                return feedback.to_dict()
            return None
    
    def get_feedback_for_target(self, target_id: str, 
                               limit: int = 50) -> List[Dict[str, Any]]:
        """Get all feedback for a specific target"""
        with self._lock:
            results = []
            for feedback in self.feedback.values():
                if feedback.target == target_id:
                    results.append(feedback.to_dict())
                    if len(results) >= limit:
                        break
            return results
    
    def get_feedback_from_source(self, source: str,
                                 limit: int = 50) -> List[Dict[str, Any]]:
        """Get all feedback from a specific source (human)"""
        with self._lock:
            results = []
            for feedback in self.feedback.values():
                if feedback.source == source:
                    results.append(feedback.to_dict())
                    if len(results) >= limit:
                        break
            return results
    
    def get_feedback_by_type(self, feedback_type: FeedbackType,
                            limit: int = 50) -> List[Dict[str, Any]]:
        """Get feedback by type"""
        with self._lock:
            results = []
            for feedback in self.feedback.values():
                if feedback.type == feedback_type:
                    results.append(feedback.to_dict())
                    if len(results) >= limit:
                        break
            return results
    
    def get_pending_feedback(self) -> List[Dict[str, Any]]:
        """Get all pending (unresolved) feedback"""
        with self._lock:
            return [
                f.to_dict() for f in self.feedback.values()
                if f.status not in [FeedbackStatus.RESOLVED, FeedbackStatus.DISMISSED]
            ]
    
    def get_escalated_feedback(self) -> List[Dict[str, Any]]:
        """Get all escalated feedback"""
        with self._lock:
            return [
                f.to_dict() for f in self.feedback.values()
                if f.status == FeedbackStatus.ESCALATED
            ]
    
    def generate_summary(self, days: int = 30) -> FeedbackSummary:
        """
        Generate feedback summary for a time period.
        
        Args:
            days: Number of days to summarize
            
        Returns:
            FeedbackSummary object
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        with self._lock:
            # Filter feedback in date range
            filtered = [
                f for f in self.feedback_history + list(self.feedback.values())
                if start_date <= f.created_at <= end_date
            ]
            
            # Aggregate by type
            by_type = Counter(f.type.value for f in filtered)
            
            # Aggregate by severity
            by_severity = Counter(f.severity.value for f in filtered)
            
            # Aggregate by status
            by_status = Counter(f.status.value for f in filtered)
            
            # Calculate average rating
            ratings = [f.rating for f in filtered if f.rating is not None]
            avg_rating = sum(ratings) / len(ratings) if ratings else 0.0
            
            # Find top issues (most mentioned tags)
            issue_tags = []
            for f in filtered:
                if f.type in [FeedbackType.ISSUE_REPORT, FeedbackType.CRITIQUE]:
                    issue_tags.extend(f.tags)
            top_issues = Counter(issue_tags).most_common(10)
            
            # Count resolved
            resolved = sum(1 for f in filtered if f.status == FeedbackStatus.RESOLVED)
            pending = sum(1 for f in filtered if f.status not in [FeedbackStatus.RESOLVED, FeedbackStatus.DISMISSED])
            
            return FeedbackSummary(
                period_start=start_date,
                period_end=end_date,
                total_feedback=len(filtered),
                by_type=dict(by_type),
                by_severity=dict(by_severity),
                by_status=dict(by_status),
                average_rating=avg_rating,
                top_issues=[{"tag": tag, "count": count} for tag, count in top_issues],
                resolved_count=resolved,
                pending_count=pending
            )
    
    def calculate_human_satisfaction(self, human_id: str, 
                                    period: str = "weekly") -> HumanSatisfactionMetric:
        """
        Calculate satisfaction metrics for a human.
        
        Args:
            human_id: Human ID
            period: Time period (daily, weekly, monthly)
            
        Returns:
            HumanSatisfactionMetric
        """
        now = datetime.now()
        
        if period == "daily":
            start_date = now - timedelta(days=1)
        elif period == "weekly":
            start_date = now - timedelta(days=7)
        elif period == "monthly":
            start_date = now - timedelta(days=30)
        else:
            start_date = now - timedelta(days=7)
        
        with self._lock:
            # Get feedback from this human
            feedbacks = [
                f for f in self.feedback_history + list(self.feedback.values())
                if f.source == human_id and f.rating is not None and start_date <= f.created_at <= now
            ]
            
            if not feedbacks:
                return HumanSatisfactionMetric(
                    human_id=human_id,
                    period=period,
                    average_rating=0.0,
                    total_responses=0,
                    positive_percentage=0.0,
                    negative_percentage=0.0,
                    neutral_percentage=0.0
                )
            
            ratings = [f.rating for f in feedbacks if f.rating]
            avg_rating = sum(ratings) / len(ratings)
            
            # Positive: rating >= 4, Negative: rating <= 2, Neutral: rating == 3
            positive = sum(1 for r in ratings if r >= 4)
            negative = sum(1 for r in ratings if r <= 2)
            neutral = sum(1 for r in ratings if r == 3)
            
            total = len(ratings)
            
            metric = HumanSatisfactionMetric(
                human_id=human_id,
                period=period,
                average_rating=avg_rating,
                total_responses=total,
                positive_percentage=(positive / total) * 100,
                negative_percentage=(negative / total) * 100,
                neutral_percentage=(neutral / total) * 100
            )
            
            self.satisfaction_metrics.append(metric)
            self._save_data()
            
            return metric
    
    def get_trend_analysis(self, feedback_type: FeedbackType = None,
                          days: int = 90) -> Dict[str, Any]:
        """
        Analyze trends in feedback over time.
        
        Args:
            feedback_type: Specific feedback type to analyze
            days: Number of days to analyze
            
        Returns:
            Trend analysis dictionary
        """
        start_date = datetime.now() - timedelta(days=days)
        
        with self._lock:
            # Filter feedback
            filtered = [
                f for f in self.feedback_history + list(self.feedback.values())
                if start_date <= f.created_at
            ]
            
            if feedback_type:
                filtered = [f for f in filtered if f.type == feedback_type]
            
            # Group by week
            weekly_data = defaultdict(lambda: {"count": 0, "avg_rating": 0, "ratings": []})
            
            for f in filtered:
                week_key = f.created_at.strftime("%Y-W%W")
                weekly_data[week_key]["count"] += 1
                if f.rating:
                    weekly_data[week_key]["ratings"].append(f.rating)
            
            # Calculate weekly averages
            for week, data in weekly_data.items():
                if data["ratings"]:
                    data["avg_rating"] = sum(data["ratings"]) / len(data["ratings"])
                del data["ratings"]
            
            # Calculate trend direction
            weeks = sorted(weekly_data.keys())
            if len(weeks) >= 2:
                first_week = weeks[0]
                last_week = weeks[-1]
                
                count_trend = weekly_data[last_week]["count"] - weekly_data[first_week]["count"]
                rating_trend = weekly_data[last_week].get("avg_rating", 0) - weekly_data[first_week].get("avg_rating", 0)
                
                trend_direction = "increasing" if count_trend > 0 else "decreasing" if count_trend < 0 else "stable"
                rating_direction = "improving" if rating_trend > 0 else "declining" if rating_trend < 0 else "stable"
            else:
                trend_direction = "insufficient_data"
                rating_direction = "insufficient_data"
            
            return {
                "period_days": days,
                "feedback_type": feedback_type.value if feedback_type else "all",
                "total_feedback": len(filtered),
                "weekly_data": dict(weekly_data),
                "trend_direction": trend_direction,
                "rating_trend": rating_direction,
                "weeks_analyzed": len(weeks)
            }
    
    def get_high_impact_feedback(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get high impact feedback (critical severity or low rating)"""
        with self._lock:
            high_impact = []
            for f in self.feedback.values():
                if f.severity in [FeedbackSeverity.CRITICAL, FeedbackSeverity.BLOCKER]:
                    high_impact.append(f)
                elif f.rating and f.rating <= 2:
                    high_impact.append(f)
            
            # Sort by severity and rating
            high_impact.sort(key=lambda x: (
                x.severity == FeedbackSeverity.BLOCKER,
                x.severity == FeedbackSeverity.CRITICAL,
                x.rating if x.rating else 5
            ))
            
            return [f.to_dict() for f in high_impact[:limit]]
    
    def get_feedback_statistics(self) -> Dict[str, Any]:
        """Get overall feedback statistics"""
        with self._lock:
            total = len(self.feedback)
            resolved = sum(1 for f in self.feedback.values() if f.status == FeedbackStatus.RESOLVED)
            escalated = sum(1 for f in self.feedback.values() if f.status == FeedbackStatus.ESCALATED)
            pending_review = sum(1 for f in self.feedback.values() if f.status == FeedbackStatus.SUBMITTED)
            
            ratings = [f.rating for f in self.feedback.values() if f.rating is not None]
            
            # Feedback by source
            by_source = Counter(f.source for f in self.feedback.values())
            
            # Feedback by target
            by_target = Counter(f.target for f in self.feedback.values())
            
            return {
                "total_feedback": total,
                "resolved": resolved,
                "escalated": escalated,
                "pending_review": pending_review,
                "resolution_rate": (resolved / total * 100) if total > 0 else 0,
                "average_rating": sum(ratings) / len(ratings) if ratings else 0,
                "feedback_by_source": dict(by_source.most_common(10)),
                "feedback_by_target": dict(by_target.most_common(10)),
                "unique_sources": len(by_source),
                "unique_targets": len(by_target)
            }
    
    def _update_cache(self, feedback: Feedback) -> None:
        """Update internal cache for quick access"""
        # Update target cache
        if feedback.target not in self._feedback_cache:
            self._feedback_cache[feedback.target] = []
        self._feedback_cache[feedback.target].append(feedback)
        
        # Keep cache manageable
        if len(self._feedback_cache[feedback.target]) > 100:
            self._feedback_cache[feedback.target] = self._feedback_cache[feedback.target][-100:]
    
    def on_feedback_received(self, callback: Any) -> None:
        """Register callback for feedback received events"""
        self._on_feedback_received.append(callback)
    
    def on_feedback_escalated(self, callback: Any) -> None:
        """Register callback for feedback escalated events"""
        self._on_feedback_escalated.append(callback)
    
    def _notify_feedback_received(self, feedback: Feedback) -> None:
        """Notify callbacks of new feedback"""
        for callback in self._on_feedback_received:
            try:
                callback(feedback)
            except Exception as e:
                logger.error(f"Error in feedback received callback: {e}")
    
    def _notify_escalated(self, feedback: Feedback) -> None:
        """Notify callbacks of escalated feedback"""
        for callback in self._on_feedback_escalated:
            try:
                callback(feedback)
            except Exception as e:
                logger.error(f"Error in feedback escalated callback: {e}")
    
    def cleanup_old_feedback(self) -> int:
        """Remove feedback older than retention period"""
        cutoff = datetime.now() - timedelta(days=self.retention_days)
        
        with self._lock:
            to_remove = []
            for fid, feedback in self.feedback.items():
                if feedback.created_at < cutoff and feedback.status in [FeedbackStatus.RESOLVED, FeedbackStatus.DISMISSED]:
                    to_remove.append(fid)
            
            for fid in to_remove:
                del self.feedback[fid]
            
            self._save_data()
            
            logger.info(f"Cleaned up {len(to_remove)} old feedback entries")
            return len(to_remove)
    
    def export_feedback(self, format: str = "json") -> Dict[str, Any]:
        """Export all feedback for analysis"""
        with self._lock:
            return {
                "export_time": datetime.now().isoformat(),
                "total_feedback": len(self.feedback),
                "feedback": [f.to_dict() for f in self.feedback.values()],
                "statistics": self.get_feedback_statistics()
            }


# Singleton instance
_feedback_collector: Optional[FeedbackCollector] = None


def get_feedback_collector() -> FeedbackCollector:
    """Get global FeedbackCollector instance"""
    global _feedback_collector
    if _feedback_collector is None:
        _feedback_collector = FeedbackCollector()
    return _feedback_collector