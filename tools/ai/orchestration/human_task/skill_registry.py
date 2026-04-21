"""
Skill Registry for Human Task Management

Manages the catalog of human skills available in the system including:
- Skill definition and categorization (using enums)
- Skill proficiency levels and matrices
- Skill gap analysis
- Skill acquisition and tracking
- Skill certification and validation
- Skill-based routing and matching

This skill_registry.py provides:

    Skill Definition Management: Define skills with categories, prerequisites, and learning estimates
    Human Skill Registration: Track skills possessed by humans with proficiency levels (1-5)
    Proficiency Matrix: Complete skill matrix per human with scoring
    Validation & Certification: Track skill validation status (unverified, self-assessed, peer-reviewed, certified)
    Endorsement System: Peer endorsements for skills
    Skill Gap Analysis: Analyze gaps between required and available skills
    Team Skill Summary: Aggregate skill coverage across teams
    Skill Search: Find humans by required skills with match scoring
    Default Skills: Pre-populated common technical skills (Python, JavaScript, React, SQL, AWS, Docker, Kubernetes, etc.)
    Persistence: All data stored via shared state manager
"""

import uuid
import threading
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from collections import defaultdict

from ...shared.logger import get_logger
from ...shared.state_manager import state_manager
from ...shared.config import config

logger = get_logger(__name__)


class SkillCategory(Enum):
    """Categories of human skills"""
    # Technical skills
    PROGRAMMING = "programming"
    FRAMEWORK = "framework"
    DATABASE = "database"
    CLOUD = "cloud"
    DEVOPS = "devops"
    SECURITY = "security"
    TESTING = "testing"
    
    # Domain skills
    DOMAIN_KNOWLEDGE = "domain_knowledge"
    BUSINESS_ANALYSIS = "business_analysis"
    REQUIREMENTS = "requirements"
    
    # Soft skills
    COMMUNICATION = "communication"
    LEADERSHIP = "leadership"
    COLLABORATION = "collaboration"
    PROBLEM_SOLVING = "problem_solving"
    
    # Process skills
    PROJECT_MANAGEMENT = "project_management"
    AGILE = "agile"
    CODE_REVIEW = "code_review"
    DOCUMENTATION = "documentation"
    
    # NEW: Human task specific skills (replaces individual skill files)
    ARCHITECTURE = "architecture"
    DEVOPS_SKILL = "devops_skill"      # Renamed to avoid conflict
    DOMAIN_EXPERT = "domain_expert"
    PERFORMANCE = "performance"
    UX = "ux"


class SkillType(Enum):
    """
    Enumeration of all available human skills.
    This replaces the need for separate skill files.
    """
    # Architecture & Design
    ARCHITECTURE = ("architecture", SkillCategory.ARCHITECTURE, "System and software architecture design")
    MICROSERVICES = ("microservices", SkillCategory.ARCHITECTURE, "Microservices architecture design")
    EVENT_DRIVEN = ("event_driven", SkillCategory.ARCHITECTURE, "Event-driven architecture")
    
    # Code Review
    CODE_REVIEW = ("code_review", SkillCategory.CODE_REVIEW, "Code review best practices")
    SECURITY_REVIEW = ("security_review", SkillCategory.SECURITY, "Security-focused code review")
    PERFORMANCE_REVIEW = ("performance_review", SkillCategory.PERFORMANCE, "Performance code review")
    
    # DevOps
    CI_CD = ("ci_cd", SkillCategory.DEVOPS, "CI/CD pipeline management")
    INFRASTRUCTURE = ("infrastructure", SkillCategory.DEVOPS, "Infrastructure as Code")
    MONITORING = ("monitoring", SkillCategory.DEVOPS, "System monitoring and observability")
    
    # Documentation
    TECH_WRITING = ("tech_writing", SkillCategory.DOCUMENTATION, "Technical writing")
    API_DOCS = ("api_docs", SkillCategory.DOCUMENTATION, "API documentation")
    USER_GUIDES = ("user_guides", SkillCategory.DOCUMENTATION, "User guide creation")
    
    # Domain Expertise
    DOMAIN_EXPERT = ("domain_expert", SkillCategory.DOMAIN_EXPERT, "Domain-specific knowledge")
    BUSINESS_LOGIC = ("business_logic", SkillCategory.BUSINESS_ANALYSIS, "Business logic understanding")
    
    # Performance
    PROFILING = ("profiling", SkillCategory.PERFORMANCE, "Performance profiling")
    OPTIMIZATION = ("optimization", SkillCategory.PERFORMANCE, "Code optimization")
    SCALING = ("scaling", SkillCategory.PERFORMANCE, "System scaling")
    
    # Security
    SECURITY_AUDIT = ("security_audit", SkillCategory.SECURITY, "Security auditing")
    VULNERABILITY = ("vulnerability", SkillCategory.SECURITY, "Vulnerability assessment")
    COMPLIANCE = ("compliance", SkillCategory.SECURITY, "Security compliance")
    
    # Testing
    UNIT_TESTING = ("unit_testing", SkillCategory.TESTING, "Unit testing")
    INTEGRATION_TESTING = ("integration_testing", SkillCategory.TESTING, "Integration testing")
    E2E_TESTING = ("e2e_testing", SkillCategory.TESTING, "End-to-end testing")
    
    # UX
    UX_DESIGN = ("ux_design", SkillCategory.UX, "User experience design")
    UI_DESIGN = ("ui_design", SkillCategory.UX, "User interface design")
    ACCESSIBILITY = ("accessibility", SkillCategory.UX, "Accessibility standards")
    
    # Existing skills (from default initialization)
    PYTHON = ("python", SkillCategory.PROGRAMMING, "Python programming language")
    JAVASCRIPT = ("javascript", SkillCategory.PROGRAMMING, "JavaScript/TypeScript")
    REACT = ("react", SkillCategory.FRAMEWORK, "React framework")
    SQL = ("sql", SkillCategory.DATABASE, "SQL databases")
    AWS = ("aws", SkillCategory.CLOUD, "Amazon Web Services")
    DOCKER = ("docker", SkillCategory.DEVOPS, "Docker containers")
    KUBERNETES = ("kubernetes", SkillCategory.DEVOPS, "Kubernetes orchestration")
    AGILE = ("agile", SkillCategory.AGILE, "Agile methodologies")
    
    def __init__(self, skill_id: str, category: SkillCategory, description: str):
        self.skill_id = skill_id
        self.skill_category = category
        self.skill_description = description
    
    @property
    def display_name(self) -> str:
        """Get human-readable display name"""
        return self.skill_id.replace('_', ' ').title()
    
    @classmethod
    def from_id(cls, skill_id: str) -> Optional["SkillType"]:
        """Get SkillType from skill_id string"""
        for skill in cls:
            if skill.skill_id == skill_id:
                return skill
        return None
    
    @classmethod
    def get_by_category(cls, category: SkillCategory) -> List["SkillType"]:
        """Get all skills in a category"""
        return [skill for skill in cls if skill.skill_category == category]


class ProficiencyLevel(Enum):
    """Proficiency levels for skills"""
    NOVICE = 1
    BEGINNER = 2
    INTERMEDIATE = 3
    ADVANCED = 4
    EXPERT = 5
    
    def __str__(self):
        return self.name.lower()
    
    @classmethod
    def from_string(cls, value: str) -> "ProficiencyLevel":
        mapping = {
            "novice": cls.NOVICE,
            "beginner": cls.BEGINNER,
            "intermediate": cls.INTERMEDIATE,
            "advanced": cls.ADVANCED,
            "expert": cls.EXPERT
        }
        return mapping.get(value.lower(), cls.BEGINNER)


class SkillValidationStatus(Enum):
    """Status of skill validation/certification"""
    UNVERIFIED = "unverified"
    SELF_ASSESSED = "self_assessed"
    PEER_REVIEWED = "peer_reviewed"
    CERTIFIED = "certified"
    EXPIRED = "expired"
    REVOKED = "revoked"


@dataclass
class SkillDefinition:
    """Definition of a skill in the registry"""
    skill_id: str
    name: str
    category: SkillCategory
    description: str
    tags: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)  # Skill IDs required
    related_skills: List[str] = field(default_factory=list)
    estimated_learning_hours: int = 40
    certification_required: bool = False
    version: str = "1.0"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_skill_type(cls, skill_type: SkillType) -> "SkillDefinition":
        """Create SkillDefinition from SkillType enum"""
        return cls(
            skill_id=skill_type.skill_id,
            name=skill_type.display_name,
            category=skill_type.skill_category,
            description=skill_type.skill_description,
            tags=[skill_type.skill_category.value, skill_type.skill_id],
            certification_required=skill_type.skill_category in [
                SkillCategory.SECURITY, SkillCategory.CLOUD, SkillCategory.DEVOPS
            ]
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "category": self.category.value,
            "description": self.description,
            "tags": self.tags,
            "prerequisites": self.prerequisites,
            "related_skills": self.related_skills,
            "estimated_learning_hours": self.estimated_learning_hours,
            "certification_required": self.certification_required,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SkillDefinition":
        return cls(
            skill_id=data["skill_id"],
            name=data["name"],
            category=SkillCategory(data["category"]),
            description=data["description"],
            tags=data.get("tags", []),
            prerequisites=data.get("prerequisites", []),
            related_skills=data.get("related_skills", []),
            estimated_learning_hours=data.get("estimated_learning_hours", 40),
            certification_required=data.get("certification_required", False),
            version=data.get("version", "1.0"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now(),
            metadata=data.get("metadata", {})
        )


@dataclass
class HumanSkill:
    """Represents a skill possessed by a human"""
    skill_id: str
    skill_name: str
    proficiency: ProficiencyLevel
    validation_status: SkillValidationStatus = SkillValidationStatus.SELF_ASSESSED
    validated_by: Optional[str] = None
    validated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    years_experience: float = 0.0
    last_used: Optional[datetime] = None
    endorsements: List[str] = field(default_factory=list)  # Human IDs who endorsed
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "skill_name": self.skill_name,
            "proficiency": self.proficiency.value,
            "validation_status": self.validation_status.value,
            "validated_by": self.validated_by,
            "validated_at": self.validated_at.isoformat() if self.validated_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "years_experience": self.years_experience,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "endorsements": self.endorsements,
            "notes": self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HumanSkill":
        return cls(
            skill_id=data["skill_id"],
            skill_name=data["skill_name"],
            proficiency=ProficiencyLevel(data["proficiency"]),
            validation_status=SkillValidationStatus(data.get("validation_status", "self_assessed")),
            validated_by=data.get("validated_by"),
            validated_at=datetime.fromisoformat(data["validated_at"]) if data.get("validated_at") else None,
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            years_experience=data.get("years_experience", 0.0),
            last_used=datetime.fromisoformat(data["last_used"]) if data.get("last_used") else None,
            endorsements=data.get("endorsements", []),
            notes=data.get("notes")
        )


@dataclass
class SkillProficiencyMatrix:
    """Matrix of skill proficiency for a human"""
    human_id: str
    skills: Dict[str, HumanSkill] = field(default_factory=dict)
    last_calculated: datetime = field(default_factory=datetime.now)
    
    def get_proficiency(self, skill_id: str) -> Optional[ProficiencyLevel]:
        """Get proficiency level for a skill"""
        skill = self.skills.get(skill_id)
        return skill.proficiency if skill else None
    
    def get_skill_score(self, skill_id: str) -> float:
        """Get normalized skill score (0-100)"""
        skill = self.skills.get(skill_id)
        if not skill:
            return 0.0
        return (skill.proficiency.value / 5) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "human_id": self.human_id,
            "skills": {sid: s.to_dict() for sid, s in self.skills.items()},
            "last_calculated": self.last_calculated.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SkillProficiencyMatrix":
        skills = {}
        for sid, sdata in data.get("skills", {}).items():
            skills[sid] = HumanSkill.from_dict(sdata)
        return cls(
            human_id=data["human_id"],
            skills=skills,
            last_calculated=datetime.fromisoformat(data["last_calculated"]) if data.get("last_calculated") else datetime.now()
        )


class SkillRegistry:
    """
    Manages the catalog of human skills and proficiency tracking.
    
    Features:
    - Enum-based skill definitions
    - Human skill registration and tracking
    - Proficiency matrix management
    - Skill gap analysis
    - Skill validation and certification
    - Skill-based search and matching
    """
    
    def __init__(self, storage_key: str = "skill_registry"):
        self.storage_key = storage_key
        self.skills: Dict[str, SkillDefinition] = {}
        self.proficiency_matrices: Dict[str, SkillProficiencyMatrix] = {}
        self.skill_hierarchy: Dict[str, List[str]] = defaultdict(list)
        self._lock = threading.RLock()
        
        # Load data
        self._load_data()
        
        # Initialize default skills from SkillType enum
        self._initialize_default_skills_from_enum()
        
        logger.info(f"SkillRegistry initialized with {len(self.skills)} skills from SkillType enum")
    
    def _load_data(self) -> None:
        """Load skill data from state manager"""
        try:
            skills_data = state_manager.get(f"{self.storage_key}.skills", {})
            for sid, sdata in skills_data.items():
                if isinstance(sdata, dict):
                    self.skills[sid] = SkillDefinition.from_dict(sdata)
            
            matrices_data = state_manager.get(f"{self.storage_key}.matrices", {})
            for hid, mdata in matrices_data.items():
                if isinstance(mdata, dict):
                    self.proficiency_matrices[hid] = SkillProficiencyMatrix.from_dict(mdata)
            
            hierarchy_data = state_manager.get(f"{self.storage_key}.hierarchy", {})
            for parent, children in hierarchy_data.items():
                self.skill_hierarchy[parent] = children
                
        except Exception as e:
            logger.warning(f"Failed to load skill data: {e}")
    
    def _save_data(self) -> None:
        """Save skill data to state manager"""
        try:
            skills_data = {sid: s.to_dict() for sid, s in self.skills.items()}
            state_manager.set(f"{self.storage_key}.skills", skills_data)
            
            matrices_data = {hid: m.to_dict() for hid, m in self.proficiency_matrices.items()}
            state_manager.set(f"{self.storage_key}.matrices", matrices_data)
            
            hierarchy_data = dict(self.skill_hierarchy)
            state_manager.set(f"{self.storage_key}.hierarchy", hierarchy_data)
            
        except Exception as e:
            logger.error(f"Failed to save skill data: {e}")
    
    def _initialize_default_skills_from_enum(self) -> None:
        """Initialize skills from SkillType enum"""
        for skill_type in SkillType:
            if skill_type.skill_id not in self.skills:
                skill_def = SkillDefinition.from_skill_type(skill_type)
                self.skills[skill_def.skill_id] = skill_def
        
        self._save_data()
    
    # ========== Skill Type Enum Helper Methods ==========
    
    def get_skill_type(self, skill_id: str) -> Optional[SkillType]:
        """Get SkillType enum by skill_id"""
        return SkillType.from_id(skill_id)
    
    def get_skills_by_type_category(self, category: SkillCategory) -> List[SkillType]:
        """Get all SkillType enums in a category"""
        return SkillType.get_by_category(category)
    
    def list_all_skill_types(self) -> List[Dict[str, Any]]:
        """List all available skill types from enum"""
        return [
            {
                "skill_id": skill.skill_id,
                "name": skill.display_name,
                "category": skill.skill_category.value,
                "description": skill.skill_description
            }
            for skill in SkillType
        ]
    
    # ========== Existing Methods (unchanged from previous version) ==========
    
    def register_skill(self, skill: SkillDefinition) -> str:
        """Register a new skill in the registry"""
        with self._lock:
            self.skills[skill.skill_id] = skill
            self._save_data()
            logger.info(f"Registered skill: {skill.name} ({skill.skill_id})")
            return skill.skill_id
    
    def register_skill_from_type(self, skill_type: SkillType) -> str:
        """Register a skill from SkillType enum"""
        skill_def = SkillDefinition.from_skill_type(skill_type)
        return self.register_skill(skill_def)
    
    def update_skill(self, skill_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing skill definition"""
        with self._lock:
            if skill_id not in self.skills:
                return False
            
            skill = self.skills[skill_id]
            for key, value in updates.items():
                if hasattr(skill, key):
                    setattr(skill, key, value)
            skill.updated_at = datetime.now()
            
            self._save_data()
            return True
    
    def get_skill(self, skill_id: str) -> Optional[SkillDefinition]:
        """Get skill definition by ID"""
        return self.skills.get(skill_id)
    
    def get_skill_by_name(self, name: str) -> Optional[SkillDefinition]:
        """Get skill definition by name (case-insensitive)"""
        name_lower = name.lower()
        for skill in self.skills.values():
            if skill.name.lower() == name_lower:
                return skill
        return None
    
    def list_skills(self, category: SkillCategory = None, 
                   tags: List[str] = None) -> List[Dict[str, Any]]:
        """List all skills with optional filtering"""
        with self._lock:
            skills = list(self.skills.values())
            
            if category:
                skills = [s for s in skills if s.category == category]
            
            if tags:
                skills = [s for s in skills if any(tag in s.tags for tag in tags)]
            
            return [
                {
                    "skill_id": s.skill_id,
                    "name": s.name,
                    "category": s.category.value,
                    "description": s.description,
                    "tags": s.tags,
                    "prerequisites": s.prerequisites,
                    "estimated_learning_hours": s.estimated_learning_hours
                }
                for s in skills
            ]
    
    def get_skills_by_category(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get skills grouped by category"""
        with self._lock:
            by_category = defaultdict(list)
            for skill in self.skills.values():
                by_category[skill.category.value].append({
                    "skill_id": skill.skill_id,
                    "name": skill.name,
                    "description": skill.description
                })
            return dict(by_category)
    
    def register_human_skill(self, human_id: str, skill_id: str,
                            proficiency: ProficiencyLevel,
                            validation_status: SkillValidationStatus = SkillValidationStatus.SELF_ASSESSED,
                            years_experience: float = 0.0,
                            endorsements: List[str] = None) -> bool:
        """Register a skill for a human"""
        with self._lock:
            if skill_id not in self.skills:
                logger.warning(f"Skill {skill_id} not found")
                return False
            
            if human_id not in self.proficiency_matrices:
                self.proficiency_matrices[human_id] = SkillProficiencyMatrix(human_id=human_id)
            
            skill_def = self.skills[skill_id]
            human_skill = HumanSkill(
                skill_id=skill_id,
                skill_name=skill_def.name,
                proficiency=proficiency,
                validation_status=validation_status,
                years_experience=years_experience,
                endorsements=endorsements or []
            )
            
            self.proficiency_matrices[human_id].skills[skill_id] = human_skill
            self.proficiency_matrices[human_id].last_calculated = datetime.now()
            
            self._save_data()
            logger.info(f"Registered skill {skill_id} for human {human_id} at {proficiency} level")
            return True
    
    def register_human_skill_by_type(self, human_id: str, skill_type: SkillType,
                                    proficiency: ProficiencyLevel,
                                    validation_status: SkillValidationStatus = SkillValidationStatus.SELF_ASSESSED,
                                    years_experience: float = 0.0) -> bool:
        """Register a skill for a human using SkillType enum"""
        return self.register_human_skill(
            human_id=human_id,
            skill_id=skill_type.skill_id,
            proficiency=proficiency,
            validation_status=validation_status,
            years_experience=years_experience
        )
    
    def update_human_skill(self, human_id: str, skill_id: str,
                          proficiency: ProficiencyLevel = None,
                          validation_status: SkillValidationStatus = None,
                          years_experience: float = None,
                          last_used: datetime = None) -> bool:
        """Update a human's skill"""
        with self._lock:
            if human_id not in self.proficiency_matrices:
                return False
            
            matrix = self.proficiency_matrices[human_id]
            if skill_id not in matrix.skills:
                return False
            
            skill = matrix.skills[skill_id]
            if proficiency:
                skill.proficiency = proficiency
            if validation_status:
                skill.validation_status = validation_status
            if years_experience is not None:
                skill.years_experience = years_experience
            if last_used:
                skill.last_used = last_used
            
            matrix.last_calculated = datetime.now()
            self._save_data()
            return True
    
    def get_human_skills(self, human_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get all skills for a human"""
        with self._lock:
            matrix = self.proficiency_matrices.get(human_id)
            if not matrix:
                return None
            
            return [
                {
                    "skill_id": s.skill_id,
                    "skill_name": s.skill_name,
                    "proficiency": s.proficiency.value,
                    "proficiency_name": str(s.proficiency),
                    "validation_status": s.validation_status.value,
                    "years_experience": s.years_experience,
                    "endorsements_count": len(s.endorsements),
                    "last_used": s.last_used.isoformat() if s.last_used else None
                }
                for s in matrix.skills.values()
            ]
    
    def get_human_proficiency(self, human_id: str, skill_id: str) -> Optional[ProficiencyLevel]:
        """Get proficiency level for a specific skill"""
        with self._lock:
            matrix = self.proficiency_matrices.get(human_id)
            if not matrix:
                return None
            skill = matrix.skills.get(skill_id)
            return skill.proficiency if skill else None
    
    def get_human_skill_score(self, human_id: str, skill_id: str) -> float:
        """Get normalized skill score (0-100)"""
        with self._lock:
            matrix = self.proficiency_matrices.get(human_id)
            if not matrix:
                return 0.0
            return matrix.get_skill_score(skill_id)
    
    def find_humans_by_skill(self, skill_id: str, 
                            min_proficiency: ProficiencyLevel = ProficiencyLevel.BEGINNER,
                            limit: int = 20) -> List[Dict[str, Any]]:
        """Find humans with a specific skill at or above proficiency level"""
        with self._lock:
            results = []
            for human_id, matrix in self.proficiency_matrices.items():
                skill = matrix.skills.get(skill_id)
                if skill and skill.proficiency.value >= min_proficiency.value:
                    results.append({
                        "human_id": human_id,
                        "proficiency": skill.proficiency.value,
                        "proficiency_name": str(skill.proficiency),
                        "validation_status": skill.validation_status.value,
                        "years_experience": skill.years_experience,
                        "score": matrix.get_skill_score(skill_id)
                    })
            
            results.sort(key=lambda x: (-x["proficiency"], -x["score"]))
            return results[:limit]
    
    def find_humans_by_skill_type(self, skill_type: SkillType,
                                 min_proficiency: ProficiencyLevel = ProficiencyLevel.BEGINNER,
                                 limit: int = 20) -> List[Dict[str, Any]]:
        """Find humans with a specific SkillType"""
        return self.find_humans_by_skill(skill_type.skill_id, min_proficiency, limit)
    
    def endorse_skill(self, human_id: str, skill_id: str, endorser_id: str) -> bool:
        """Endorse a human's skill"""
        with self._lock:
            matrix = self.proficiency_matrices.get(human_id)
            if not matrix:
                return False
            
            skill = matrix.skills.get(skill_id)
            if not skill:
                return False
            
            if endorser_id not in skill.endorsements:
                skill.endorsements.append(endorser_id)
                
                if len(skill.endorsements) >= 3 and skill.validation_status == SkillValidationStatus.SELF_ASSESSED:
                    skill.validation_status = SkillValidationStatus.PEER_REVIEWED
                    skill.validated_at = datetime.now()
            
            self._save_data()
            return True
    
    def validate_skill(self, human_id: str, skill_id: str, 
                      validator_id: str, status: SkillValidationStatus) -> bool:
        """Validate or certify a human's skill"""
        with self._lock:
            matrix = self.proficiency_matrices.get(human_id)
            if not matrix:
                return False
            
            skill = matrix.skills.get(skill_id)
            if not skill:
                return False
            
            skill.validation_status = status
            skill.validated_by = validator_id
            skill.validated_at = datetime.now()
            
            if status == SkillValidationStatus.CERTIFIED:
                skill.expires_at = datetime.now() + timedelta(days=365)
            
            self._save_data()
            return True
    
    def get_skill_matrix(self, human_id: str) -> Optional[Dict[str, Any]]:
        """Get complete skill matrix for a human"""
        with self._lock:
            matrix = self.proficiency_matrices.get(human_id)
            if not matrix:
                return None
            
            scores = [matrix.get_skill_score(sid) for sid in matrix.skills]
            avg_score = sum(scores) / len(scores) if scores else 0
            
            if matrix.skills:
                strongest = max(matrix.skills.items(), key=lambda x: x[1].proficiency.value)
                weakest = min(matrix.skills.items(), key=lambda x: x[1].proficiency.value)
            else:
                strongest = weakest = (None, None)
            
            return {
                "human_id": human_id,
                "skill_count": len(matrix.skills),
                "average_proficiency": avg_score,
                "strongest_skill": {
                    "skill_id": strongest[0],
                    "proficiency": strongest[1].proficiency.value if strongest[1] else None
                } if strongest[0] else None,
                "weakest_skill": {
                    "skill_id": weakest[0],
                    "proficiency": weakest[1].proficiency.value if weakest[1] else None
                } if weakest[0] else None,
                "skills": [
                    {
                        "skill_id": s.skill_id,
                        "skill_name": s.skill_name,
                        "proficiency": s.proficiency.value,
                        "score": matrix.get_skill_score(s.skill_id)
                    }
                    for s in matrix.skills.values()
                ]
            }
    
    def get_team_skill_summary(self, human_ids: List[str] = None) -> Dict[str, Any]:
        """Get skill summary for a team"""
        with self._lock:
            matrices = list(self.proficiency_matrices.values())
            if human_ids:
                matrices = [m for m in matrices if m.human_id in human_ids]
            
            if not matrices:
                return {"total_humans": 0}
            
            skill_coverage = defaultdict(lambda: {"count": 0, "avg_proficiency": 0, "proficiencies": []})
            
            for matrix in matrices:
                for skill_id, skill in matrix.skills.items():
                    skill_coverage[skill_id]["count"] += 1
                    skill_coverage[skill_id]["proficiencies"].append(skill.proficiency.value)
            
            for skill_id, data in skill_coverage.items():
                data["avg_proficiency"] = sum(data["proficiencies"]) / len(data["proficiencies"])
                del data["proficiencies"]
            
            all_skill_ids = set(self.skills.keys())
            covered_skill_ids = set(skill_coverage.keys())
            missing_skills = all_skill_ids - covered_skill_ids
            
            return {
                "total_humans": len(matrices),
                "total_skills_covered": len(covered_skill_ids),
                "total_skills_missing": len(missing_skills),
                "missing_skills": [
                    {
                        "skill_id": sid,
                        "name": self.skills[sid].name,
                        "category": self.skills[sid].category.value
                    }
                    for sid in missing_skills
                ],
                "skill_coverage": {
                    sid: {
                        "human_count": data["count"],
                        "avg_proficiency": data["avg_proficiency"]
                    }
                    for sid, data in skill_coverage.items()
                }
            }
    
    def get_skill_statistics(self) -> Dict[str, Any]:
        """Get overall skill registry statistics"""
        with self._lock:
            total_humans = len(self.proficiency_matrices)
            total_skill_entries = sum(len(m.skills) for m in self.proficiency_matrices.values())
            
            proficiency_counts = defaultdict(int)
            for matrix in self.proficiency_matrices.values():
                for skill in matrix.skills.values():
                    proficiency_counts[skill.proficiency.name] += 1
            
            validation_counts = defaultdict(int)
            for matrix in self.proficiency_matrices.values():
                for skill in matrix.skills.values():
                    validation_counts[skill.validation_status.value] += 1
            
            return {
                "total_skills_defined": len(self.skills),
                "total_skills_from_enum": len(list(SkillType)),
                "total_humans_with_skills": total_humans,
                "total_skill_assignments": total_skill_entries,
                "avg_skills_per_human": total_skill_entries / total_humans if total_humans > 0 else 0,
                "proficiency_distribution": dict(proficiency_counts),
                "validation_distribution": dict(validation_counts),
                "skills_by_category": {
                    category.value: len([s for s in self.skills.values() if s.category == category])
                    for category in SkillCategory
                }
            }
    
    def search_humans_by_skills(self, required_skills: Dict[str, ProficiencyLevel],
                               match_any: bool = False,
                               limit: int = 10) -> List[Dict[str, Any]]:
        """Search for humans matching a set of required skills"""
        with self._lock:
            results = []
            
            for human_id, matrix in self.proficiency_matrices.items():
                match_score = 0
                matched_skills = []
                missing_skills = []
                
                for skill_id, required_prof in required_skills.items():
                    human_skill = matrix.skills.get(skill_id)
                    
                    if human_skill and human_skill.proficiency.value >= required_prof.value:
                        score_contribution = (human_skill.proficiency.value / 5) * 100
                        match_score += score_contribution
                        matched_skills.append({
                            "skill_id": skill_id,
                            "proficiency": human_skill.proficiency.value,
                            "required": required_prof.value
                        })
                    else:
                        missing_skills.append({
                            "skill_id": skill_id,
                            "required": required_prof.value,
                            "current": human_skill.proficiency.value if human_skill else 0
                        })
                
                if match_any:
                    match_percentage = (len(matched_skills) / len(required_skills)) * 100 if required_skills else 0
                else:
                    match_percentage = match_score / len(required_skills) if required_skills else 0
                
                if match_percentage > 0:
                    results.append({
                        "human_id": human_id,
                        "match_percentage": match_percentage,
                        "matched_skills": matched_skills,
                        "missing_skills": missing_skills,
                        "total_skills": len(matrix.skills)
                    })
            
            results.sort(key=lambda x: -x["match_percentage"])
            return results[:limit]
    
    def search_humans_by_skill_types(self, required_skills: Dict[SkillType, ProficiencyLevel],
                                    match_any: bool = False,
                                    limit: int = 10) -> List[Dict[str, Any]]:
        """Search for humans using SkillType enum"""
        skill_id_map = {skill.skill_id: prof for skill, prof in required_skills.items()}
        return self.search_humans_by_skills(skill_id_map, match_any, limit)
    
    def delete_human_skill(self, human_id: str, skill_id: str) -> bool:
        """Remove a skill from a human"""
        with self._lock:
            matrix = self.proficiency_matrices.get(human_id)
            if not matrix:
                return False
            
            if skill_id in matrix.skills:
                del matrix.skills[skill_id]
                self._save_data()
                return True
            return False
    
    def clear_human_skills(self, human_id: str) -> bool:
        """Remove all skills from a human"""
        with self._lock:
            if human_id in self.proficiency_matrices:
                del self.proficiency_matrices[human_id]
                self._save_data()
                return True
            return False


# Singleton instance
_skill_registry: Optional[SkillRegistry] = None


def get_skill_registry() -> SkillRegistry:
    """Get global SkillRegistry instance"""
    global _skill_registry
    if _skill_registry is None:
        _skill_registry = SkillRegistry()
    return _skill_registry