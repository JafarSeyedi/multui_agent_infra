"""
Skill Gap Analyzer for Human-in-the-Loop Operations

Analyzes skill requirements vs. available human expertise to:
- Identify missing skills for tasks
- Suggest skill development or external help
- Match tasks to appropriate human experts
- Track skill proficiency levels
- Recommend training or documentation needs

This implementation provides:

    Skill Management: Track skills with proficiency levels (Novice → Expert)
    Expert Registry: Manage human experts with their skills and availability
    Task Requirements: Define required and preferred skills for tasks
    Gap Detection: Identify skill gaps with severity assessment (LOW → CRITICAL)
    Impact Scoring: Calculate impact scores (0-100) based on gap size and task priority
    Expert Matching: Find best experts for tasks with match scoring
    Training Needs: Identify training requirements with estimated hours
    Hiring Suggestions: Recommend hiring for critical missing skills
    Team Profiling: Analyze overall team skill strengths and weaknesses
    Persistence: Save to state_manager with history tracking

The analyzer integrates with your human-in-the-loop system to ensure tasks are assigned to appropriately skilled humans.
"""

import json
import math
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, Counter

from ....shared.logger import get_logger
from ....shared.state_manager import state_manager
from ....shared.config import config

logger = get_logger(__name__)


class SkillLevel(Enum):
    """Proficiency levels for skills"""
    NOVICE = 1
    BEGINNER = 2
    INTERMEDIATE = 3
    ADVANCED = 4
    EXPERT = 5
    
    def __str__(self):
        return self.name.lower()
    
    @classmethod
    def from_string(cls, value: str) -> "SkillLevel":
        mapping = {
            "novice": cls.NOVICE,
            "beginner": cls.BEGINNER,
            "intermediate": cls.INTERMEDIATE,
            "advanced": cls.ADVANCED,
            "expert": cls.EXPERT
        }
        return mapping.get(value.lower(), cls.BEGINNER)


class SkillCategory(Enum):
    """Categories of skills"""
    ARCHITECTURE = "architecture"
    CODING = "coding"
    TESTING = "testing"
    DEVOPS = "devops"
    SECURITY = "security"
    PERFORMANCE = "performance"
    DOCUMENTATION = "documentation"
    UX = "ux"
    DOMAIN_KNOWLEDGE = "domain_knowledge"
    CODE_REVIEW = "code_review"
    DEBUGGING = "debugging"
    DATABASE = "database"
    API_DESIGN = "api_design"
    PROJECT_MANAGEMENT = "project_management"
    COMMUNICATION = "communication"


class GapSeverity(Enum):
    """Severity of skill gaps"""
    LOW = "low"          # Nice to have, can work around
    MEDIUM = "medium"    # Important, may cause delays
    HIGH = "high"        # Critical, blocks progress
    CRITICAL = "critical" # Impossible to proceed without


@dataclass
class Skill:
    """Represents a skill with proficiency level"""
    name: str
    category: SkillCategory
    level: SkillLevel
    last_used: Optional[datetime] = None
    years_experience: float = 0.0
    certifications: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category.value,
            "level": self.level.value,
            "level_name": str(self.level),
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "years_experience": self.years_experience,
            "certifications": self.certifications
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Skill":
        return cls(
            name=data["name"],
            category=SkillCategory(data["category"]),
            level=SkillLevel(data["level"]),
            last_used=datetime.fromisoformat(data["last_used"]) if data.get("last_used") else None,
            years_experience=data.get("years_experience", 0.0),
            certifications=data.get("certifications", [])
        )


@dataclass
class HumanExpert:
    """Represents a human expert with their skills"""
    id: str
    name: str
    email: str
    skills: Dict[str, Skill] = field(default_factory=dict)
    current_workload: int = 0
    max_workload: int = 5
    availability_score: float = 1.0  # 0-1, 1 = fully available
    preferred_tasks: List[str] = field(default_factory=list)
    timezone: str = "UTC"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "skills": {k: v.to_dict() for k, v in self.skills.items()},
            "current_workload": self.current_workload,
            "max_workload": self.max_workload,
            "availability_score": self.availability_score,
            "preferred_tasks": self.preferred_tasks,
            "timezone": self.timezone
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HumanExpert":
        expert = cls(
            id=data["id"],
            name=data["name"],
            email=data["email"],
            current_workload=data.get("current_workload", 0),
            max_workload=data.get("max_workload", 5),
            availability_score=data.get("availability_score", 1.0),
            preferred_tasks=data.get("preferred_tasks", []),
            timezone=data.get("timezone", "UTC")
        )
        for skill_name, skill_data in data.get("skills", {}).items():
            expert.skills[skill_name] = Skill.from_dict(skill_data)
        return expert


@dataclass
class SkillRequirement:
    """Skill requirements for a task or workflow"""
    task_id: str
    task_type: str
    required_skills: Dict[str, SkillLevel]  # skill_name -> minimum level
    preferred_skills: Dict[str, SkillLevel] = field(default_factory=dict)
    estimated_duration_minutes: int = 60
    priority: int = 1  # 1-5, 5 highest
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "required_skills": {k: v.value for k, v in self.required_skills.items()},
            "preferred_skills": {k: v.value for k, v in self.preferred_skills.items()},
            "estimated_duration_minutes": self.estimated_duration_minutes,
            "priority": self.priority
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SkillRequirement":
        return cls(
            task_id=data["task_id"],
            task_type=data["task_type"],
            required_skills={k: SkillLevel(v) for k, v in data.get("required_skills", {}).items()},
            preferred_skills={k: SkillLevel(v) for k, v in data.get("preferred_skills", {}).items()},
            estimated_duration_minutes=data.get("estimated_duration_minutes", 60),
            priority=data.get("priority", 1)
        )


@dataclass
class SkillGap:
    """Represents a detected skill gap"""
    task_id: str
    skill_name: str
    required_level: SkillLevel
    available_level: SkillLevel
    severity: GapSeverity
    impact_score: float  # 0-100
    suggested_action: str
    potential_experts: List[str] = field(default_factory=list)  # Expert IDs
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "skill_name": self.skill_name,
            "required_level": self.required_level.value,
            "required_level_name": str(self.required_level),
            "available_level": self.available_level.value,
            "available_level_name": str(self.available_level),
            "severity": self.severity.value,
            "impact_score": self.impact_score,
            "suggested_action": self.suggested_action,
            "potential_experts": self.potential_experts
        }


@dataclass
class SkillGapReport:
    """Comprehensive skill gap analysis report"""
    timestamp: datetime
    total_tasks_analyzed: int
    total_gaps_found: int
    gaps_by_severity: Dict[str, int]
    gaps_by_category: Dict[str, int]
    missing_skills: List[str]
    recommendations: List[str]
    training_needs: List[Dict[str, Any]]
    hiring_suggestions: List[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "total_tasks_analyzed": self.total_tasks_analyzed,
            "total_gaps_found": self.total_gaps_found,
            "gaps_by_severity": self.gaps_by_severity,
            "gaps_by_category": self.gaps_by_category,
            "missing_skills": self.missing_skills,
            "recommendations": self.recommendations,
            "training_needs": self.training_needs,
            "hiring_suggestions": self.hiring_suggestions
        }


class SkillGapAnalyzer:
    """
    Analyzes skill gaps between task requirements and human expertise.
    
    Features:
    - Skill inventory management
    - Task skill requirement analysis
    - Gap detection and severity assessment
    - Expert matching and recommendation
    - Training needs identification
    """
    
    def __init__(self, storage_key: str = "skill_gap_analyzer"):
        self.storage_key = storage_key
        self.experts: Dict[str, HumanExpert] = {}
        self.skill_requirements: Dict[str, SkillRequirement] = {}
        self.skill_gaps: List[SkillGap] = []
        
        # Skill taxonomy and dependencies
        self.skill_hierarchy: Dict[str, List[str]] = {}  # parent -> children
        self.skill_prerequisites: Dict[str, List[str]] = {}  # skill -> prerequisites
        
        # Historical tracking
        self.gap_history: List[Dict[str, Any]] = []
        
        # Load data from state manager
        self._load_data()
        
        # Initialize default skill taxonomy
        self._initialize_skill_taxonomy()
        
        logger.info(f"SkillGapAnalyzer initialized with {len(self.experts)} experts")
    
    def _load_data(self) -> None:
        """Load experts and requirements from state manager"""
        try:
            # Load experts
            experts_data = state_manager.get(f"{self.storage_key}.experts", {})
            for expert_id, expert_data in experts_data.items():
                self.experts[expert_id] = HumanExpert.from_dict(expert_data)
            
            # Load skill requirements
            requirements_data = state_manager.get(f"{self.storage_key}.requirements", {})
            for task_id, req_data in requirements_data.items():
                self.skill_requirements[task_id] = SkillRequirement.from_dict(req_data)
            
            # Load gap history
            self.gap_history = state_manager.get(f"{self.storage_key}.history", [])
            
        except Exception as e:
            logger.warning(f"Failed to load data: {e}")
    
    def _save_data(self) -> None:
        """Save experts and requirements to state manager"""
        try:
            experts_data = {eid: expert.to_dict() for eid, expert in self.experts.items()}
            state_manager.set(f"{self.storage_key}.experts", experts_data)
            
            requirements_data = {tid: req.to_dict() for tid, req in self.skill_requirements.items()}
            state_manager.set(f"{self.storage_key}.requirements", requirements_data)
            
        except Exception as e:
            logger.error(f"Failed to save data: {e}")
    
    def _initialize_skill_taxonomy(self) -> None:
        """Initialize skill hierarchy and prerequisites"""
        # Skill hierarchy
        self.skill_hierarchy = {
            "programming": ["python", "javascript", "java", "c++", "go", "rust"],
            "python_ecosystem": ["python", "pandas", "numpy", "pytest", "fastapi", "django"],
            "web_development": ["javascript", "typescript", "react", "vue", "html", "css"],
            "devops": ["docker", "kubernetes", "ci_cd", "terraform", "aws", "azure", "gcp"],
            "database": ["sql", "nosql", "postgresql", "mongodb", "redis"],
            "testing": ["unit_testing", "integration_testing", "e2e_testing", "performance_testing"],
        }
        
        # Skill prerequisites
        self.skill_prerequisites = {
            "python": [],
            "pandas": ["python"],
            "numpy": ["python"],
            "pytest": ["python"],
            "fastapi": ["python"],
            "django": ["python"],
            "javascript": [],
            "typescript": ["javascript"],
            "react": ["javascript"],
            "docker": [],
            "kubernetes": ["docker"],
            "sql": [],
            "nosql": [],
        }
    
    def register_expert(self, expert: HumanExpert) -> None:
        """Register or update a human expert"""
        self.experts[expert.id] = expert
        self._save_data()
        logger.info(f"Registered expert: {expert.name} ({expert.id})")
    
    def unregister_expert(self, expert_id: str) -> bool:
        """Remove an expert from the registry"""
        if expert_id in self.experts:
            del self.experts[expert_id]
            self._save_data()
            logger.info(f"Unregistered expert: {expert_id}")
            return True
        return False
    
    def add_skill_to_expert(self, expert_id: str, skill: Skill) -> bool:
        """Add a skill to an expert's profile"""
        if expert_id not in self.experts:
            logger.warning(f"Expert {expert_id} not found")
            return False
        
        self.experts[expert_id].skills[skill.name] = skill
        self._save_data()
        logger.debug(f"Added skill {skill.name} to expert {expert_id}")
        return True
    
    def update_skill_level(self, expert_id: str, skill_name: str, 
                          new_level: SkillLevel) -> bool:
        """Update an expert's skill level"""
        if expert_id not in self.experts:
            return False
        
        if skill_name not in self.experts[expert_id].skills:
            return False
        
        self.experts[expert_id].skills[skill_name].level = new_level
        self.experts[expert_id].skills[skill_name].last_used = datetime.now()
        self._save_data()
        return True
    
    def register_task_requirements(self, requirement: SkillRequirement) -> None:
        """Register skill requirements for a task"""
        self.skill_requirements[requirement.task_id] = requirement
        self._save_data()
        logger.debug(f"Registered requirements for task: {requirement.task_id}")
    
    def analyze_skill_gaps(self, task_id: str) -> List[SkillGap]:
        """
        Analyze skill gaps for a specific task.
        
        Returns:
            List of SkillGap objects
        """
        if task_id not in self.skill_requirements:
            logger.warning(f"No requirements found for task {task_id}")
            return []
        
        requirement = self.skill_requirements[task_id]
        gaps = []
        
        # Check each required skill
        for skill_name, required_level in requirement.required_skills.items():
            # Find best available skill level across all experts
            best_level = self._get_best_skill_level(skill_name)
            
            if best_level.value < required_level.value:
                severity = self._calculate_gap_severity(required_level, best_level)
                impact = self._calculate_impact_score(required_level, best_level, requirement.priority)
                
                # Find potential experts who could help
                potential_experts = self._find_experts_for_skill(skill_name, required_level)
                
                gap = SkillGap(
                    task_id=task_id,
                    skill_name=skill_name,
                    required_level=required_level,
                    available_level=best_level,
                    severity=severity,
                    impact_score=impact,
                    suggested_action=self._suggest_action(skill_name, required_level, best_level),
                    potential_experts=potential_experts
                )
                gaps.append(gap)
        
        # Store gaps
        self.skill_gaps.extend(gaps)
        
        # Record in history
        self._record_gap_analysis(task_id, gaps)
        
        return gaps
    
    def _get_best_skill_level(self, skill_name: str) -> SkillLevel:
        """Find the highest skill level available across all experts"""
        best_level = SkillLevel.NOVICE
        
        for expert in self.experts.values():
            if skill_name in expert.skills:
                level = expert.skills[skill_name].level
                if level.value > best_level.value:
                    best_level = level
        
        # Check for related skills (skill hierarchy)
        for parent, children in self.skill_hierarchy.items():
            if skill_name in children:
                # Check parent skill
                parent_level = self._get_best_skill_level(parent)
                if parent_level.value > best_level.value:
                    best_level = parent_level
        
        return best_level
    
    def _calculate_gap_severity(self, required: SkillLevel, 
                               available: SkillLevel) -> GapSeverity:
        """Calculate severity of a skill gap"""
        gap_size = required.value - available.value
        
        if gap_size >= 4:
            return GapSeverity.CRITICAL
        elif gap_size >= 3:
            return GapSeverity.HIGH
        elif gap_size >= 2:
            return GapSeverity.MEDIUM
        else:
            return GapSeverity.LOW
    
    def _calculate_impact_score(self, required: SkillLevel, 
                               available: SkillLevel,
                               priority: int) -> float:
        """Calculate impact score (0-100) for a skill gap"""
        gap_size = required.value - available.value
        max_gap = 4  # Expert - Novice = 4
        
        # Base impact from gap size
        base_impact = (gap_size / max_gap) * 100
        
        # Adjust for priority (1-5 -> 0.2-1.0 multiplier)
        priority_multiplier = 0.6 + (priority * 0.1)
        
        # Adjust for required level (harder skills have higher impact)
        level_multiplier = required.value / 5.0
        
        impact = base_impact * priority_multiplier * level_multiplier
        
        return min(100, impact)
    
    def _find_experts_for_skill(self, skill_name: str, 
                               required_level: SkillLevel) -> List[str]:
        """Find experts who have a skill at or above required level"""
        experts = []
        
        for expert_id, expert in self.experts.items():
            if skill_name in expert.skills:
                if expert.skills[skill_name].level.value >= required_level.value:
                    # Check availability
                    if expert.current_workload < expert.max_workload:
                        experts.append(expert_id)
        
        # Sort by skill level and availability
        experts.sort(key=lambda eid: (
            -self.experts[eid].skills[skill_name].level.value,
            self.experts[eid].current_workload
        ))
        
        return experts[:5]  # Top 5 experts
    
    def _suggest_action(self, skill_name: str, required: SkillLevel, 
                        available: SkillLevel) -> str:
        """Generate suggested action to address skill gap"""
        gap_size = required.value - available.value
        
        if gap_size >= 3:
            return f"HIRE: No internal expertise for {skill_name} at {required} level. Consider hiring or contracting."
        elif gap_size >= 2:
            return f"TRAIN: Significant gap in {skill_name}. Provide intensive training or pair with expert."
        elif gap_size >= 1:
            return f"MENTOR: Small gap in {skill_name}. Pair with someone who has {required} level for mentorship."
        else:
            return f"COACH: Minor improvement needed for {skill_name}. Provide documentation or quick training."
    
    def _record_gap_analysis(self, task_id: str, gaps: List[SkillGap]) -> None:
        """Record gap analysis in history"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id,
            "gaps_found": len(gaps),
            "gaps": [g.to_dict() for g in gaps]
        }
        
        self.gap_history.append(record)
        
        # Keep last 1000 records
        if len(self.gap_history) > 1000:
            self.gap_history = self.gap_history[-1000:]
        
        try:
            state_manager.set(f"{self.storage_key}.history", self.gap_history)
        except Exception as e:
            logger.error(f"Failed to save history: {e}")
    
    def analyze_all_pending_tasks(self) -> SkillGapReport:
        """Analyze skill gaps for all pending tasks"""
        all_gaps = []
        tasks_analyzed = 0
        
        for task_id in self.skill_requirements:
            gaps = self.analyze_skill_gaps(task_id)
            all_gaps.extend(gaps)
            tasks_analyzed += 1
        
        # Aggregate statistics
        gaps_by_severity = defaultdict(int)
        gaps_by_category = defaultdict(int)
        missing_skills = set()
        
        for gap in all_gaps:
            gaps_by_severity[gap.severity.value] += 1
            
            # Determine category
            category = self._get_skill_category(gap.skill_name)
            gaps_by_category[category.value] += 1
            
            if gap.available_level == SkillLevel.NOVICE:
                missing_skills.add(gap.skill_name)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(all_gaps)
        
        # Identify training needs
        training_needs = self._identify_training_needs(all_gaps)
        
        # Suggest hiring
        hiring_suggestions = self._suggest_hiring(all_gaps)
        
        report = SkillGapReport(
            timestamp=datetime.now(),
            total_tasks_analyzed=tasks_analyzed,
            total_gaps_found=len(all_gaps),
            gaps_by_severity=dict(gaps_by_severity),
            gaps_by_category=dict(gaps_by_category),
            missing_skills=list(missing_skills),
            recommendations=recommendations,
            training_needs=training_needs,
            hiring_suggestions=hiring_suggestions
        )
        
        # Save report
        self._save_report(report)
        
        return report
    
    def _get_skill_category(self, skill_name: str) -> SkillCategory:
        """Determine category for a skill"""
        # Simple mapping - can be expanded
        category_mapping = {
            "python": SkillCategory.CODING,
            "javascript": SkillCategory.CODING,
            "react": SkillCategory.CODING,
            "docker": SkillCategory.DEVOPS,
            "kubernetes": SkillCategory.DEVOPS,
            "pytest": SkillCategory.TESTING,
            "security": SkillCategory.SECURITY,
            "performance": SkillCategory.PERFORMANCE,
            "documentation": SkillCategory.DOCUMENTATION,
        }
        
        return category_mapping.get(skill_name.lower(), SkillCategory.CODING)
    
    def _generate_recommendations(self, gaps: List[SkillGap]) -> List[str]:
        """Generate high-level recommendations"""
        recommendations = []
        
        # Group gaps by severity
        critical_gaps = [g for g in gaps if g.severity == GapSeverity.CRITICAL]
        high_gaps = [g for g in gaps if g.severity == GapSeverity.HIGH]
        
        if critical_gaps:
            recommendations.append(f"CRITICAL: Address {len(critical_gaps)} critical skill gaps immediately - consider hiring or outsourcing")
        
        if high_gaps:
            recommendations.append(f"HIGH: Prioritize training for {len(high_gaps)} high-severity gaps")
        
        # Check for recurring gaps
        skill_counts = Counter([g.skill_name for g in gaps])
        recurring = [(skill, count) for skill, count in skill_counts.items() if count > 3]
        
        if recurring:
            skills_list = ", ".join([f"{skill} ({count}x)" for skill, count in recurring[:3]])
            recommendations.append(f"RECURRING: Skills {skills_list} appear in multiple tasks - invest in team upskilling")
        
        # Suggest cross-training
        if len(self.experts) > 1:
            recommendations.append("CROSS-TRAIN: Consider knowledge sharing sessions between experts")
        
        return recommendations
    
    def _identify_training_needs(self, gaps: List[SkillGap]) -> List[Dict[str, Any]]:
        """Identify specific training needs"""
        training_needs = []
        
        # Group gaps by skill
        skill_groups = defaultdict(list)
        for gap in gaps:
            if gap.severity in [GapSeverity.MEDIUM, GapSeverity.HIGH]:
                skill_groups[gap.skill_name].append(gap)
        
        for skill_name, skill_gaps in skill_groups.items():
            # Determine training level needed
            max_required = max(g.required_level.value for g in skill_gaps)
            current_best = max(g.available_level.value for g in skill_gaps)
            
            training_needs.append({
                "skill": skill_name,
                "current_level": SkillLevel(current_best).value,
                "target_level": SkillLevel(max_required).value,
                "affected_tasks": len(skill_gaps),
                "estimated_training_hours": self._estimate_training_hours(current_best, max_required),
                "priority": "high" if any(g.severity == GapSeverity.HIGH for g in skill_gaps) else "medium"
            })
        
        return sorted(training_needs, key=lambda x: x["priority"] == "high", reverse=True)
    
    def _estimate_training_hours(self, current_level: int, target_level: int) -> int:
        """Estimate training hours needed to close gap"""
        # Rough estimates: 10 hours per level gap
        gap = target_level - current_level
        base_hours = gap * 10
        
        # Additional hours for expert level
        if target_level >= 4:  # Advanced or Expert
            base_hours += 20
        
        return base_hours
    
    def _suggest_hiring(self, gaps: List[SkillGap]) -> List[Dict[str, Any]]:
        """Suggest hiring needs based on skill gaps"""
        hiring_needs = []
        
        # Focus on critical and high gaps where no expert exists
        severe_gaps = [g for g in gaps if g.severity in [GapSeverity.CRITICAL, GapSeverity.HIGH]]
        
        skill_groups = defaultdict(list)
        for gap in severe_gaps:
            if gap.available_level == SkillLevel.NOVICE:
                skill_groups[gap.skill_name].append(gap)
        
        for skill_name, skill_gaps in skill_groups.items():
            hiring_needs.append({
                "skill": skill_name,
                "required_level": max(g.required_level.value for g in skill_gaps),
                "affected_tasks": len(skill_gaps),
                "urgency": "immediate" if any(g.severity == GapSeverity.CRITICAL for g in skill_gaps) else "soon",
                "suggestion": f"Hire or contract expert in {skill_name}"
            })
        
        return hiring_needs
    
    def _save_report(self, report: SkillGapReport) -> None:
        """Save skill gap report to state manager"""
        try:
            state_manager.set(f"{self.storage_key}.latest_report", report.to_dict())
            
            # Keep report history
            reports = state_manager.get(f"{self.storage_key}.reports", [])
            reports.append(report.to_dict())
            if len(reports) > 50:
                reports = reports[-50:]
            state_manager.set(f"{self.storage_key}.reports", reports)
            
        except Exception as e:
            logger.error(f"Failed to save report: {e}")
    
    def get_expert_match_score(self, task_id: str, expert_id: str) -> float:
        """
        Calculate match score between a task and an expert (0-100).
        
        Higher score = better match
        """
        if task_id not in self.skill_requirements:
            return 0.0
        
        if expert_id not in self.experts:
            return 0.0
        
        requirement = self.skill_requirements[task_id]
        expert = self.experts[expert_id]
        
        total_score = 0.0
        max_possible = 0.0
        
        # Score required skills
        for skill_name, required_level in requirement.required_skills.items():
            weight = 2.0  # Required skills are weighted double
            max_possible += weight * required_level.value
            
            if skill_name in expert.skills:
                expert_level = expert.skills[skill_name].level
                # Score based on how well expert meets requirement
                score = min(expert_level.value, required_level.value) / required_level.value
                total_score += weight * score * required_level.value
            else:
                total_score += 0
        
        # Score preferred skills (lower weight)
        for skill_name, preferred_level in requirement.preferred_skills.items():
            weight = 1.0
            max_possible += weight * preferred_level.value
            
            if skill_name in expert.skills:
                expert_level = expert.skills[skill_name].level
                score = min(expert_level.value, preferred_level.value) / preferred_level.value
                total_score += weight * score * preferred_level.value
        
        # Adjust for workload
        workload_factor = 1.0 - (expert.current_workload / expert.max_workload)
        
        # Calculate final score (0-100)
        if max_possible > 0:
            raw_score = (total_score / max_possible) * 100
            final_score = raw_score * workload_factor
            return min(100, final_score)
        
        return 0.0
    
    def find_best_expert(self, task_id: str, limit: int = 3) -> List[Tuple[str, float]]:
        """Find best experts for a task"""
        matches = []
        
        for expert_id in self.experts:
            score = self.get_expert_match_score(task_id, expert_id)
            if score > 0:
                matches.append((expert_id, score))
        
        # Sort by score descending
        matches.sort(key=lambda x: x[1], reverse=True)
        
        return matches[:limit]
    
    def get_team_skill_profile(self) -> Dict[str, Any]:
        """Get overall team skill profile"""
        if not self.experts:
            return {"status": "no_experts"}
        
        all_skills = []
        skill_levels = defaultdict(list)
        
        for expert in self.experts.values():
            for skill_name, skill in expert.skills.items():
                all_skills.append(skill_name)
                skill_levels[skill_name].append(skill.level.value)
        
        # Calculate team strength for each skill
        team_strength = {}
        for skill_name, levels in skill_levels.items():
            team_strength[skill_name] = {
                "avg_level": sum(levels) / len(levels),
                "max_level": max(levels),
                "experts_count": len(levels),
                "strength": "strong" if max(levels) >= 4 else "moderate" if max(levels) >= 3 else "weak"
            }
        
        return {
            "total_experts": len(self.experts),
            "total_skills": len(set(all_skills)),
            "unique_skills": list(set(all_skills)),
            "team_strength": team_strength,
            "strongest_skills": sorted(team_strength.items(), 
                                      key=lambda x: x[1]["max_level"], 
                                      reverse=True)[:10],
            "weakest_skills": sorted(team_strength.items(),
                                    key=lambda x: x[1]["max_level"])[:10]
        }
    
    def get_gap_summary(self) -> Dict[str, Any]:
        """Get summary of current skill gaps"""
        if not self.skill_gaps:
            return {"status": "no_gaps_detected"}
        
        return {
            "total_gaps": len(self.skill_gaps),
            "critical_gaps": len([g for g in self.skill_gaps if g.severity == GapSeverity.CRITICAL]),
            "high_gaps": len([g for g in self.skill_gaps if g.severity == GapSeverity.HIGH]),
            "most_missing_skills": Counter([g.skill_name for g in self.skill_gaps]).most_common(5),
            "most_affected_tasks": Counter([g.task_id for g in self.skill_gaps]).most_common(5)
        }
    
    def clear_gaps(self) -> None:
        """Clear all detected skill gaps"""
        self.skill_gaps.clear()
        logger.info("Skill gaps cleared")
    
    def export_analysis(self) -> Dict[str, Any]:
        """Export complete skill gap analysis"""
        return {
            "timestamp": datetime.now().isoformat(),
            "experts": {eid: expert.to_dict() for eid, expert in self.experts.items()},
            "requirements": {tid: req.to_dict() for tid, req in self.skill_requirements.items()},
            "gaps": [g.to_dict() for g in self.skill_gaps],
            "team_profile": self.get_team_skill_profile(),
            "gap_summary": self.get_gap_summary()
        }


# Singleton instance
_skill_gap_analyzer: Optional[SkillGapAnalyzer] = None


def get_skill_gap_analyzer() -> SkillGapAnalyzer:
    """Get global SkillGapAnalyzer instance"""
    global _skill_gap_analyzer
    if _skill_gap_analyzer is None:
        _skill_gap_analyzer = SkillGapAnalyzer()
    return _skill_gap_analyzer