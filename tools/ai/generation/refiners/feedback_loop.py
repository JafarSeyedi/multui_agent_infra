#!/usr/bin/env python3
"""
Feedback Loop - AI Development Framework
Manages continuous improvement through feedback collection and learning.

Part of the Level 3 Generation tools (refiners/feedback_loop.py)

This feedback_loop.py provides:

1. Multi-Source Feedback Collection - Validation errors, test failures, performance issues, code reviews, user feedback
2. Pattern Learning - Automatically identifies recurring issues from feedback history
3. Persistent Storage - SQLite database for feedback and learned patterns
4. Pattern Matching - Finds similar issues using normalized signatures
5. Fix Suggestions - Suggests fixes based on learned patterns or LLM
6. Auto-Fix Application - Optionally auto-applies high-confidence fixes
7. Session Management - Groups feedback into logical sessions
8. Feedback Analytics - Statistics, resolution rates, improvement metrics
9. Pattern Confidence Scoring - Patterns gain confidence with more occurrences
10. LLM-Powered Analysis - Uses AI for pattern description and fix generation
11. Data Pruning - Automatic cleanup of old feedback and low-confidence patterns
12. Export Capabilities - Export feedback and patterns to JSON

The feedback loop creates a continuous improvement cycle, learning from past issues to prevent future ones and automatically suggesting or applying fixes.
"""

import json
import hashlib
import sqlite3
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict
import numpy as np

from ....shared.llm_client import LLMClient
from ....shared.state_manager import StateManager
from ....shared.logger import get_logger
from .iterative_refiner import ValidationError, ErrorCategory, RefinementSession

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class FeedbackType(str, Enum):
    """Type of feedback."""
    VALIDATION_ERROR = "validation_error"
    TEST_FAILURE = "test_failure"
    PERFORMANCE_ISSUE = "performance_issue"
    CODE_REVIEW = "code_review"
    USER_FEEDBACK = "user_feedback"
    LLM_SUGGESTION = "llm_suggestion"
    METRIC_VIOLATION = "metric_violation"
    STYLE_VIOLATION = "style_violation"
    SECURITY_ISSUE = "security_issue"
    DOCUMENTATION_GAP = "documentation_gap"


class FeedbackSeverity(str, Enum):
    """Severity of feedback."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class LearningMode(str, Enum):
    """Mode of learning from feedback."""
    IMMEDIATE = "immediate"
    BATCH = "batch"
    SCHEDULED = "scheduled"
    MANUAL = "manual"


class PatternType(str, Enum):
    """Type of learned pattern."""
    ERROR_PATTERN = "error_pattern"
    FIX_PATTERN = "fix_pattern"
    STYLE_PATTERN = "style_pattern"
    OPTIMIZATION_PATTERN = "optimization_pattern"
    ANTI_PATTERN = "anti_pattern"
    BEST_PRACTICE = "best_practice"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class FeedbackItem:
    """Single piece of feedback."""
    id: str
    feedback_type: FeedbackType
    severity: FeedbackSeverity
    code_snippet: Optional[str] = None
    error_message: Optional[str] = None
    suggested_fix: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    source: str = "unknown"
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolution: Optional[str] = None
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.id:
            self.id = self._generate_id()
    
    def _generate_id(self) -> str:
        content = f"{self.feedback_type.value}:{self.error_message}:{self.code_snippet}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


@dataclass
class LearnedPattern:
    """Pattern learned from feedback history."""
    id: str
    pattern_type: PatternType
    description: str
    pattern_signature: str
    fix_template: Optional[str] = None
    occurrences: int = 1
    success_rate: float = 1.0
    last_seen: datetime = field(default_factory=datetime.now)
    examples: List[str] = field(default_factory=list)
    related_errors: List[str] = field(default_factory=list)
    confidence: float = 0.5
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.id:
            self.id = hashlib.sha256(self.pattern_signature.encode()).hexdigest()[:16]


@dataclass
class FeedbackSession:
    """Session for collecting and processing feedback."""
    session_id: str
    learning_mode: LearningMode
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    feedback_items: List[FeedbackItem] = field(default_factory=list)
    patterns_learned: List[LearnedPattern] = field(default_factory=list)
    improvements_applied: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FeedbackLoopConfig:
    """Configuration for feedback loop."""
    learning_mode: LearningMode = LearningMode.IMMEDIATE
    store_feedback: bool = True
    learn_patterns: bool = True
    auto_apply_fixes: bool = False
    min_confidence_to_apply: float = 0.8
    max_patterns_to_store: int = 1000
    pattern_similarity_threshold: float = 0.85
    database_path: Optional[Path] = None
    use_llm: bool = True
    llm_model: str = "deepseek-chat"
    collect_metrics: bool = True
    anonymize_code: bool = False
    feedback_ttl_days: int = 90


# ============================================================
# FEEDBACK STORAGE
# ============================================================

class FeedbackStorage:
    """Persistent storage for feedback and learned patterns."""
    
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Path(".ai_state/feedback.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database."""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id TEXT PRIMARY KEY,
                feedback_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                code_snippet TEXT,
                error_message TEXT,
                suggested_fix TEXT,
                context TEXT,
                source TEXT,
                timestamp TEXT NOT NULL,
                resolved INTEGER DEFAULT 0,
                resolution TEXT,
                resolved_at TEXT,
                metadata TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patterns (
                id TEXT PRIMARY KEY,
                pattern_type TEXT NOT NULL,
                description TEXT,
                pattern_signature TEXT UNIQUE NOT NULL,
                fix_template TEXT,
                occurrences INTEGER DEFAULT 1,
                success_rate REAL DEFAULT 1.0,
                last_seen TEXT NOT NULL,
                examples TEXT,
                related_errors TEXT,
                confidence REAL DEFAULT 0.5,
                metadata TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                learning_mode TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                feedback_count INTEGER DEFAULT 0,
                patterns_count INTEGER DEFAULT 0,
                metadata TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_feedback_type ON feedback(feedback_type)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_feedback_severity ON feedback(severity)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_feedback_timestamp ON feedback(timestamp)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_pattern_type ON patterns(pattern_type)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_pattern_confidence ON patterns(confidence)
        ''')
        
        self.conn.commit()
    
    def save_feedback(self, feedback: FeedbackItem):
        """Save feedback item to database."""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO feedback 
            (id, feedback_type, severity, code_snippet, error_message, suggested_fix, 
             context, source, timestamp, resolved, resolution, resolved_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            feedback.id,
            feedback.feedback_type.value,
            feedback.severity.value,
            feedback.code_snippet,
            feedback.error_message,
            feedback.suggested_fix,
            json.dumps(feedback.context),
            feedback.source,
            feedback.timestamp.isoformat(),
            1 if feedback.resolved else 0,
            feedback.resolution,
            feedback.resolved_at.isoformat() if feedback.resolved_at else None,
            json.dumps(feedback.metadata)
        ))
        self.conn.commit()
    
    def get_feedback(self, feedback_id: str) -> Optional[FeedbackItem]:
        """Retrieve feedback by ID."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM feedback WHERE id = ?', (feedback_id,))
        row = cursor.fetchone()
        
        if row:
            return self._row_to_feedback(row)
        return None
    
    def get_feedback_by_type(self, feedback_type: FeedbackType, limit: int = 100) -> List[FeedbackItem]:
        """Get feedback items by type."""
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT * FROM feedback WHERE feedback_type = ? ORDER BY timestamp DESC LIMIT ?',
            (feedback_type.value, limit)
        )
        return [self._row_to_feedback(row) for row in cursor.fetchall()]
    
    def get_feedback_by_pattern(self, error_message: str, limit: int = 10) -> List[FeedbackItem]:
        """Get similar feedback by error message pattern."""
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT * FROM feedback WHERE error_message LIKE ? ORDER BY timestamp DESC LIMIT ?',
            (f'%{error_message}%', limit)
        )
        return [self._row_to_feedback(row) for row in cursor.fetchall()]
    
    def save_pattern(self, pattern: LearnedPattern):
        """Save learned pattern to database."""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO patterns 
            (id, pattern_type, description, pattern_signature, fix_template, 
             occurrences, success_rate, last_seen, examples, related_errors, confidence, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            pattern.id,
            pattern.pattern_type.value,
            pattern.description,
            pattern.pattern_signature,
            pattern.fix_template,
            pattern.occurrences,
            pattern.success_rate,
            pattern.last_seen.isoformat(),
            json.dumps(pattern.examples),
            json.dumps(pattern.related_errors),
            pattern.confidence,
            json.dumps(pattern.metadata)
        ))
        self.conn.commit()
    
    def get_pattern(self, pattern_id: str) -> Optional[LearnedPattern]:
        """Retrieve pattern by ID."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM patterns WHERE id = ?', (pattern_id,))
        row = cursor.fetchone()
        
        if row:
            return self._row_to_pattern(row)
        return None
    
    def get_pattern_by_signature(self, signature: str) -> Optional[LearnedPattern]:
        """Get pattern by signature."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM patterns WHERE pattern_signature = ?', (signature,))
        row = cursor.fetchone()
        
        if row:
            return self._row_to_pattern(row)
        return None
    
    def get_patterns_by_type(self, pattern_type: PatternType, min_confidence: float = 0.0) -> List[LearnedPattern]:
        """Get patterns by type with minimum confidence."""
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT * FROM patterns WHERE pattern_type = ? AND confidence >= ? ORDER BY confidence DESC',
            (pattern_type.value, min_confidence)
        )
        return [self._row_to_pattern(row) for row in cursor.fetchall()]
    
    def save_session(self, session: FeedbackSession):
        """Save feedback session."""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO sessions 
            (session_id, learning_mode, start_time, end_time, feedback_count, patterns_count, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            session.session_id,
            session.learning_mode.value,
            session.start_time.isoformat(),
            session.end_time.isoformat() if session.end_time else None,
            len(session.feedback_items),
            len(session.patterns_learned),
            json.dumps(session.metadata)
        ))
        self.conn.commit()
    
    def _row_to_feedback(self, row) -> FeedbackItem:
        """Convert database row to FeedbackItem."""
        return FeedbackItem(
            id=row['id'],
            feedback_type=FeedbackType(row['feedback_type']),
            severity=FeedbackSeverity(row['severity']),
            code_snippet=row['code_snippet'],
            error_message=row['error_message'],
            suggested_fix=row['suggested_fix'],
            context=json.loads(row['context']) if row['context'] else {},
            source=row['source'],
            timestamp=datetime.fromisoformat(row['timestamp']),
            resolved=bool(row['resolved']),
            resolution=row['resolution'],
            resolved_at=datetime.fromisoformat(row['resolved_at']) if row['resolved_at'] else None,
            metadata=json.loads(row['metadata']) if row['metadata'] else {}
        )
    
    def _row_to_pattern(self, row) -> LearnedPattern:
        """Convert database row to LearnedPattern."""
        return LearnedPattern(
            id=row['id'],
            pattern_type=PatternType(row['pattern_type']),
            description=row['description'],
            pattern_signature=row['pattern_signature'],
            fix_template=row['fix_template'],
            occurrences=row['occurrences'],
            success_rate=row['success_rate'],
            last_seen=datetime.fromisoformat(row['last_seen']),
            examples=json.loads(row['examples']) if row['examples'] else [],
            related_errors=json.loads(row['related_errors']) if row['related_errors'] else [],
            confidence=row['confidence'],
            metadata=json.loads(row['metadata']) if row['metadata'] else {}
        )
    
    def close(self):
        """Close database connection."""
        self.conn.close()


# ============================================================
# PATTERN LEARNER
# ============================================================

class PatternLearner:
    """Learn patterns from feedback history."""
    
    def __init__(self, config: FeedbackLoopConfig, storage: FeedbackStorage):
        self.config = config
        self.storage = storage
        self.llm = LLMClient() if config.use_llm else None
    
    def learn_from_feedback(self, feedback_items: List[FeedbackItem]) -> List[LearnedPattern]:
        """Learn patterns from a batch of feedback."""
        patterns = []
        
        grouped = self._group_similar_feedback(feedback_items)
        
        for signature, group in grouped.items():
            if len(group) >= 2:
                pattern = self._extract_pattern(group)
                if pattern:
                    patterns.append(pattern)
        
        for pattern in patterns:
            self.storage.save_pattern(pattern)
        
        return patterns
    
    def _group_similar_feedback(self, items: List[FeedbackItem]) -> Dict[str, List[FeedbackItem]]:
        """Group similar feedback items."""
        groups = defaultdict(list)
        
        for item in items:
            signature = self._generate_signature(item)
            groups[signature].append(item)
        
        return groups
    
    def _generate_signature(self, item: FeedbackItem) -> str:
        """Generate signature for feedback grouping."""
        parts = [item.feedback_type.value]
        
        if item.error_message:
            normalized = self._normalize_error_message(item.error_message)
            parts.append(normalized)
        
        if item.code_snippet:
            normalized = self._normalize_code_snippet(item.code_snippet)
            parts.append(normalized)
        
        return hashlib.sha256('|'.join(parts).encode()).hexdigest()[:32]
    
    def _normalize_error_message(self, message: str) -> str:
        """Normalize error message for comparison."""
        import re
        message = message.lower()
        message = re.sub(r'\d+', '<NUM>', message)
        message = re.sub(r"'[^']*'", '<STR>', message)
        message = re.sub(r'"[^"]*"', '<STR>', message)
        message = re.sub(r'\s+', ' ', message)
        return message.strip()
    
    def _normalize_code_snippet(self, code: str) -> str:
        """Normalize code snippet for comparison."""
        import re
        code = code.strip()
        code = re.sub(r'#.*$', '', code, flags=re.MULTILINE)
        code = re.sub(r'\d+', '<NUM>', code)
        code = re.sub(r"'[^']*'", '<STR>', code)
        code = re.sub(r'"[^"]*"', '<STR>', code)
        code = re.sub(r'\s+', ' ', code)
        return code.strip()
    
    def _extract_pattern(self, feedback_group: List[FeedbackItem]) -> Optional[LearnedPattern]:
        """Extract pattern from a group of similar feedback."""
        if not feedback_group:
            return None
        
        first = feedback_group[0]
        
        pattern_type = self._classify_pattern_type(first)
        
        signature = self._generate_signature(first)
        
        existing = self.storage.get_pattern_by_signature(signature)
        if existing:
            existing.occurrences += len(feedback_group)
            existing.last_seen = datetime.now()
            existing.confidence = min(1.0, existing.confidence + 0.05)
            return existing
        
        description = self._generate_description(feedback_group)
        fix_template = self._generate_fix_template(feedback_group)
        
        examples = []
        for item in feedback_group[:5]:
            if item.code_snippet:
                examples.append(item.code_snippet)
        
        related_errors = list(set(item.error_message for item in feedback_group if item.error_message))
        
        confidence = min(1.0, 0.5 + (len(feedback_group) * 0.1))
        
        return LearnedPattern(
            pattern_type=pattern_type,
            description=description,
            pattern_signature=signature,
            fix_template=fix_template,
            occurrences=len(feedback_group),
            examples=examples,
            related_errors=related_errors,
            confidence=confidence
        )
    
    def _classify_pattern_type(self, item: FeedbackItem) -> PatternType:
        """Classify feedback into pattern type."""
        if item.feedback_type == FeedbackType.VALIDATION_ERROR:
            if 'type' in str(item.error_message).lower():
                return PatternType.ERROR_PATTERN
            return PatternType.ERROR_PATTERN
        elif item.feedback_type == FeedbackType.STYLE_VIOLATION:
            return PatternType.STYLE_PATTERN
        elif item.feedback_type == FeedbackType.PERFORMANCE_ISSUE:
            return PatternType.OPTIMIZATION_PATTERN
        elif item.suggested_fix:
            return PatternType.FIX_PATTERN
        return PatternType.ERROR_PATTERN
    
    def _generate_description(self, group: List[FeedbackItem]) -> str:
        """Generate human-readable description of pattern."""
        if self.llm and len(group) >= 3:
            return self._llm_generate_description(group)
        
        first = group[0]
        if first.error_message:
            return f"Pattern: {first.error_message[:100]}"
        return f"Pattern from {len(group)} similar issues"
    
    def _llm_generate_description(self, group: List[FeedbackItem]) -> str:
        """Use LLM to generate pattern description."""
        prompt = f"""
        Summarize this common code issue pattern:
        
        Error messages:
        {chr(10).join(item.error_message for item in group[:3] if item.error_message)}
        
        Code snippets:
        {chr(10).join(item.code_snippet for item in group[:3] if item.code_snippet)}
        
        Provide a concise one-sentence description of the pattern.
        """
        
        try:
            return self.llm.complete(prompt).strip()
        except:
            return f"Pattern from {len(group)} similar issues"
    
    def _generate_fix_template(self, group: List[FeedbackItem]) -> Optional[str]:
        """Generate fix template from successful resolutions."""
        resolved = [item for item in group if item.resolved and item.resolution]
        
        if resolved:
            return resolved[0].resolution
        
        if self.llm and len(group) >= 2:
            return self._llm_generate_fix(group)
        
        return None
    
    def _llm_generate_fix(self, group: List[FeedbackItem]) -> Optional[str]:
        """Use LLM to generate fix template."""
        prompt = f"""
        Generate a fix template for this common issue:
        
        Error: {group[0].error_message}
        Code: {group[0].code_snippet}
        
        Provide a concise fix as a code snippet.
        Output only the fix code, no explanations.
        """
        
        try:
            return self.llm.complete(prompt).strip()
        except:
            return None


# ============================================================
# MAIN FEEDBACK LOOP
# ============================================================

class FeedbackLoop:
    """
    Manages continuous improvement through feedback collection and learning.
    
    Features:
    - Collect feedback from multiple sources
    - Learn patterns from feedback history
    - Suggest fixes based on learned patterns
    - Auto-apply high-confidence fixes
    - Track improvement metrics
    - Persistent storage with SQLite
    - LLM-powered pattern analysis
    - Session management
    - Feedback analytics
    """
    
    def __init__(self, config: Optional[FeedbackLoopConfig] = None):
        self.config = config or FeedbackLoopConfig()
        self.storage = FeedbackStorage(self.config.database_path)
        self.pattern_learner = PatternLearner(self.config, self.storage)
        self.llm = LLMClient() if self.config.use_llm else None
        
        self.current_session: Optional[FeedbackSession] = None
        
        logger.info("FeedbackLoop initialized")
    
    # ============================================================
    # SESSION MANAGEMENT
    # ============================================================
    
    def start_session(self, learning_mode: Optional[LearningMode] = None) -> str:
        """Start a new feedback session."""
        learning_mode = learning_mode or self.config.learning_mode
        
        session_id = self._generate_session_id()
        
        self.current_session = FeedbackSession(
            session_id=session_id,
            learning_mode=learning_mode
        )
        
        logger.info(f"Started feedback session {session_id}")
        return session_id
    
    def end_session(self) -> Optional[FeedbackSession]:
        """End current feedback session."""
        if not self.current_session:
            return None
        
        self.current_session.end_time = datetime.now()
        
        if self.current_session.learning_mode == LearningMode.BATCH:
            patterns = self.pattern_learner.learn_from_feedback(self.current_session.feedback_items)
            self.current_session.patterns_learned = patterns
        
        self.storage.save_session(self.current_session)
        
        session = self.current_session
        self.current_session = None
        
        logger.info(f"Ended feedback session {session.session_id}")
        return session
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"feedback_{timestamp}"
    
    # ============================================================
    # FEEDBACK COLLECTION
    # ============================================================
    
    def add_feedback(self,
                     feedback_type: FeedbackType,
                     severity: FeedbackSeverity,
                     code_snippet: Optional[str] = None,
                     error_message: Optional[str] = None,
                     suggested_fix: Optional[str] = None,
                     context: Optional[Dict[str, Any]] = None,
                     source: str = "unknown") -> str:
        """Add a feedback item."""
        if self.config.anonymize_code and code_snippet:
            code_snippet = self._anonymize_code(code_snippet)
        
        item = FeedbackItem(
            id="",
            feedback_type=feedback_type,
            severity=severity,
            code_snippet=code_snippet,
            error_message=error_message,
            suggested_fix=suggested_fix,
            context=context or {},
            source=source
        )
        
        if self.config.store_feedback:
            self.storage.save_feedback(item)
        
        if self.current_session:
            self.current_session.feedback_items.append(item)
        
        if self.config.learning_mode == LearningMode.IMMEDIATE:
            patterns = self.pattern_learner.learn_from_feedback([item])
            if self.current_session:
                self.current_session.patterns_learned.extend(patterns)
            
            if self.config.auto_apply_fixes and suggested_fix:
                self._apply_fix(item, suggested_fix)
        
        logger.debug(f"Added feedback: {item.id} ({feedback_type.value})")
        return item.id
    
    def add_validation_errors(self, errors: List[ValidationError], source: str = "validator"):
        """Add multiple validation errors as feedback."""
        for error in errors:
            self.add_feedback(
                feedback_type=FeedbackType.VALIDATION_ERROR,
                severity=self._map_severity(error.severity),
                error_message=error.message,
                code_snippet=error.context,
                suggested_fix=error.suggestion,
                context={
                    'error_code': error.code,
                    'line': error.line,
                    'category': error.category.value
                },
                source=source
            )
    
    def add_from_refinement_session(self, session: RefinementSession):
        """Add feedback from a refinement session."""
        for errors in session.errors_history:
            self.add_validation_errors(errors, source="refiner")
        
        for i, score in enumerate(session.quality_scores):
            if i > 0 and score < session.quality_scores[i-1]:
                self.add_feedback(
                    feedback_type=FeedbackType.METRIC_VIOLATION,
                    severity=FeedbackSeverity.MEDIUM,
                    context={'quality_score': score, 'iteration': i},
                    source="refiner"
                )
    
    def _map_severity(self, severity: str) -> FeedbackSeverity:
        """Map validation severity to feedback severity."""
        mapping = {
            'error': FeedbackSeverity.HIGH,
            'warning': FeedbackSeverity.MEDIUM,
            'info': FeedbackSeverity.LOW
        }
        return mapping.get(severity, FeedbackSeverity.MEDIUM)
    
    def _anonymize_code(self, code: str) -> str:
        """Anonymize code snippet."""
        import re
        code = re.sub(r'"[^"]*"', '"<STRING>"', code)
        code = re.sub(r"'[^']*'", "'<STRING>'", code)
        code = re.sub(r'\b\d+\b', '<NUM>', code)
        code = re.sub(r'#.*$', '# <COMMENT>', code, flags=re.MULTILINE)
        return code
    
    # ============================================================
    # PATTERN MATCHING
    # ============================================================
    
    def find_matching_patterns(self, error_message: str, 
                                code_snippet: Optional[str] = None,
                                min_confidence: float = 0.5) -> List[LearnedPattern]:
        """Find patterns matching an error."""
        signature = self.pattern_learner._generate_signature(
            FeedbackItem(
                id="",
                feedback_type=FeedbackType.VALIDATION_ERROR,
                severity=FeedbackSeverity.MEDIUM,
                error_message=error_message,
                code_snippet=code_snippet
            )
        )
        
        pattern = self.storage.get_pattern_by_signature(signature)
        if pattern and pattern.confidence >= min_confidence:
            return [pattern]
        
        return []
    
    def suggest_fix(self, error_message: str, code_snippet: Optional[str] = None) -> Optional[str]:
        """Suggest fix for an error based on learned patterns."""
        patterns = self.find_matching_patterns(error_message, code_snippet)
        
        if patterns and patterns[0].fix_template:
            return patterns[0].fix_template
        
        if self.llm:
            return self._llm_suggest_fix(error_message, code_snippet)
        
        return None
    
    def _llm_suggest_fix(self, error_message: str, code_snippet: Optional[str] = None) -> Optional[str]:
        """Use LLM to suggest fix."""
        prompt = f"""
        Suggest a fix for this Python code error:
        
        Error: {error_message}
        """
        
        if code_snippet:
            prompt += f"\nCode: {code_snippet}"
        
        prompt += "\nProvide only the fixed code, no explanations."
        
        try:
            return self.llm.complete(prompt).strip()
        except:
            return None
    
    # ============================================================
    # FIX APPLICATION
    # ============================================================
    
    def _apply_fix(self, item: FeedbackItem, fix: str) -> bool:
        """Apply a fix automatically."""
        if not self.config.auto_apply_fixes:
            return False
        
        logger.info(f"Auto-applying fix for {item.id}")
        
        if self.current_session:
            self.current_session.improvements_applied.append(item.id)
        
        item.resolved = True
        item.resolution = fix
        item.resolved_at = datetime.now()
        
        if self.config.store_feedback:
            self.storage.save_feedback(item)
        
        return True
    
    def resolve_feedback(self, feedback_id: str, resolution: str) -> bool:
        """Mark feedback as resolved with resolution."""
        item = self.storage.get_feedback(feedback_id)
        if not item:
            return False
        
        item.resolved = True
        item.resolution = resolution
        item.resolved_at = datetime.now()
        
        self.storage.save_feedback(item)
        
        return True
    
    # ============================================================
    # ANALYTICS
    # ============================================================
    
    def get_feedback_statistics(self, 
                                 start_date: Optional[datetime] = None,
                                 end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get feedback statistics."""
        cursor = self.storage.conn.cursor()
        
        query = 'SELECT feedback_type, severity, COUNT(*) as count FROM feedback'
        params = []
        
        conditions = []
        if start_date:
            conditions.append('timestamp >= ?')
            params.append(start_date.isoformat())
        if end_date:
            conditions.append('timestamp <= ?')
            params.append(end_date.isoformat())
        
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
        
        query += ' GROUP BY feedback_type, severity'
        
        cursor.execute(query, params)
        
        stats = defaultdict(lambda: defaultdict(int))
        for row in cursor.fetchall():
            stats[row['feedback_type']][row['severity']] = row['count']
        
        cursor.execute('SELECT COUNT(*) FROM feedback WHERE resolved = 1')
        resolved_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM feedback')
        total_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT pattern_type) FROM patterns')
        pattern_types = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM patterns')
        total_patterns = cursor.fetchone()[0]
        
        return {
            'total_feedback': total_count,
            'resolved_feedback': resolved_count,
            'resolution_rate': resolved_count / total_count if total_count > 0 else 0,
            'by_type': dict(stats),
            'total_patterns': total_patterns,
            'pattern_types': pattern_types
        }
    
    def get_top_patterns(self, pattern_type: Optional[PatternType] = None, 
                          limit: int = 10) -> List[LearnedPattern]:
        """Get top patterns by confidence and occurrences."""
        cursor = self.storage.conn.cursor()
        
        if pattern_type:
            cursor.execute(
                'SELECT * FROM patterns WHERE pattern_type = ? ORDER BY confidence DESC, occurrences DESC LIMIT ?',
                (pattern_type.value, limit)
            )
        else:
            cursor.execute(
                'SELECT * FROM patterns ORDER BY confidence DESC, occurrences DESC LIMIT ?',
                (limit,)
            )
        
        return [self.storage._row_to_pattern(row) for row in cursor.fetchall()]
    
    def get_improvement_metrics(self) -> Dict[str, Any]:
        """Get improvement metrics over time."""
        cursor = self.storage.conn.cursor()
        
        cursor.execute('''
            SELECT DATE(timestamp) as date, 
                   COUNT(*) as total,
                   SUM(CASE WHEN resolved = 1 THEN 1 ELSE 0 END) as resolved
            FROM feedback 
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
            LIMIT 30
        ''')
        
        daily_stats = []
        for row in cursor.fetchall():
            daily_stats.append({
                'date': row['date'],
                'total': row['total'],
                'resolved': row['resolved'],
                'resolution_rate': row['resolved'] / row['total'] if row['total'] > 0 else 0
            })
        
        cursor.execute('''
            SELECT feedback_type, AVG(CASE WHEN resolved = 1 THEN 1 ELSE 0 END) as resolution_rate
            FROM feedback
            GROUP BY feedback_type
        ''')
        
        type_rates = {}
        for row in cursor.fetchall():
            type_rates[row['feedback_type']] = row['resolution_rate']
        
        return {
            'daily_stats': daily_stats,
            'resolution_rates_by_type': type_rates
        }
    
    # ============================================================
    # CLEANUP
    # ============================================================
    
    def cleanup_old_feedback(self):
        """Remove feedback older than TTL."""
        if not self.config.feedback_ttl_days:
            return
        
        cursor = self.storage.conn.cursor()
        cutoff = datetime.now().timestamp() - (self.config.feedback_ttl_days * 24 * 3600)
        cutoff_str = datetime.fromtimestamp(cutoff).isoformat()
        
        cursor.execute('DELETE FROM feedback WHERE timestamp < ?', (cutoff_str,))
        deleted = cursor.rowcount
        self.storage.conn.commit()
        
        logger.info(f"Cleaned up {deleted} old feedback items")
    
    def prune_patterns(self):
        """Remove low-confidence patterns beyond max limit."""
        cursor = self.storage.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM patterns')
        count = cursor.fetchone()[0]
        
        if count > self.config.max_patterns_to_store:
            cursor.execute('''
                DELETE FROM patterns 
                WHERE id IN (
                    SELECT id FROM patterns 
                    ORDER BY confidence ASC, occurrences ASC 
                    LIMIT ?
                )
            ''', (count - self.config.max_patterns_to_store,))
            
            deleted = cursor.rowcount
            self.storage.conn.commit()
            
            logger.info(f"Pruned {deleted} low-confidence patterns")
    
    # ============================================================
    # EXPORT
    # ============================================================
    
    def export_feedback(self, output_path: Optional[Path] = None) -> str:
        """Export all feedback as JSON."""
        cursor = self.storage.conn.cursor()
        cursor.execute('SELECT * FROM feedback ORDER BY timestamp DESC')
        
        feedback_items = []
        for row in cursor.fetchall():
            item = self.storage._row_to_feedback(row)
            feedback_items.append({
                'id': item.id,
                'feedback_type': item.feedback_type.value,
                'severity': item.severity.value,
                'error_message': item.error_message,
                'resolved': item.resolved,
                'timestamp': item.timestamp.isoformat()
            })
        
        data = {
            'exported_at': datetime.now().isoformat(),
            'total_items': len(feedback_items),
            'items': feedback_items
        }
        
        content = json.dumps(data, indent=2)
        
        if output_path:
            output_path.write_text(content)
        
        return content
    
    def export_patterns(self, output_path: Optional[Path] = None) -> str:
        """Export learned patterns as JSON."""
        cursor = self.storage.conn.cursor()
        cursor.execute('SELECT * FROM patterns ORDER BY confidence DESC')
        
        patterns = []
        for row in cursor.fetchall():
            pattern = self.storage._row_to_pattern(row)
            patterns.append({
                'id': pattern.id,
                'pattern_type': pattern.pattern_type.value,
                'description': pattern.description,
                'occurrences': pattern.occurrences,
                'confidence': pattern.confidence,
                'fix_template': pattern.fix_template
            })
        
        data = {
            'exported_at': datetime.now().isoformat(),
            'total_patterns': len(patterns),
            'patterns': patterns
        }
        
        content = json.dumps(data, indent=2)
        
        if output_path:
            output_path.write_text(content)
        
        return content
    
    def close(self):
        """Clean up resources."""
        if self.current_session:
            self.end_session()
        
        self.cleanup_old_feedback()
        self.prune_patterns()
        self.storage.close()
        
        logger.info("FeedbackLoop closed")


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for feedback loop."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage feedback collection and learning")
    parser.add_argument("--stats", action="store_true", help="Show feedback statistics")
    parser.add_argument("--patterns", action="store_true", help="Show learned patterns")
    parser.add_argument("--export", type=Path, help="Export feedback to file")
    parser.add_argument("--export-patterns", type=Path, help="Export patterns to file")
    parser.add_argument("--cleanup", action="store_true", help="Cleanup old feedback")
    parser.add_argument("--metrics", action="store_true", help="Show improvement metrics")
    
    args = parser.parse_args()
    
    loop = FeedbackLoop()
    
    if args.stats:
        stats = loop.get_feedback_statistics()
        print(json.dumps(stats, indent=2))
    
    if args.patterns:
        patterns = loop.get_top_patterns(limit=20)
        print(f"\nTop Learned Patterns ({len(patterns)}):\n")
        for p in patterns:
            print(f"  [{p.confidence:.0%}] {p.description}")
            if p.fix_template:
                print(f"    Fix: {p.fix_template[:100]}...")
            print()
    
    if args.export:
        loop.export_feedback(args.export)
        print(f"Feedback exported to {args.export}")
    
    if args.export_patterns:
        loop.export_patterns(args.export_patterns)
        print(f"Patterns exported to {args.export_patterns}")
    
    if args.cleanup:
        loop.cleanup_old_feedback()
        loop.prune_patterns()
        print("Cleanup completed")
    
    if args.metrics:
        metrics = loop.get_improvement_metrics()
        print(json.dumps(metrics, indent=2))
    
    loop.close()


if __name__ == "__main__":
    main()