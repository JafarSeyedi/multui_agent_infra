"""
Work Item Types for Human Task Management

Defines the types of human task work items using an enum-based approach.
This separates type definitions from queue management logic.

Each work item type has specific:
- Display name and description
- Required skills
- Default priority
- Approval requirements
- Timeout settings
- Template structure
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


class WorkItemType(Enum):
    """
    Enumeration of all human task work item types.
    This replaces separate files for each work item type.
    """
    
    APPROVAL = {
        "id": "approval",
        "display_name": "Approval Request",
        "description": "Request for approval on a change, PR, or decision",
        "required_skills": ["code_review", "decision_making"],
        "default_priority": 1,  # High priority (0=highest, 4=lowest)
        "requires_approval": True,
        "timeout_hours": 48,
        "icon": "✅",
        "color": "#4CAF50"
    }
    
    BUG_TRIAGE = {
        "id": "bug_triage",
        "display_name": "Bug Triage",
        "description": "Triage and prioritize reported bugs",
        "required_skills": ["debugging", "priority_assessment", "testing"],
        "default_priority": 0,  # Critical priority
        "requires_approval": False,
        "timeout_hours": 24,
        "icon": "🐛",
        "color": "#F44336"
    }
    
    CONFLICT = {
        "id": "conflict",
        "display_name": "Conflict Resolution",
        "description": "Resolve merge or design conflicts",
        "required_skills": ["conflict_resolution", "communication", "git"],
        "default_priority": 0,  # Critical priority
        "requires_approval": False,
        "timeout_hours": 24,
        "icon": "⚡",
        "color": "#FF9800"
    }
    
    DESIGN = {
        "id": "design",
        "display_name": "Design Review",
        "description": "Review architecture and design documents",
        "required_skills": ["architecture", "design_review", "documentation"],
        "default_priority": 2,  # Medium priority
        "requires_approval": True,
        "timeout_hours": 72,
        "icon": "📐",
        "color": "#2196F3"
    }
    
    FEATURE_SPEC = {
        "id": "feature_spec",
        "display_name": "Feature Specification",
        "description": "Review and approve feature specifications",
        "required_skills": ["requirements_analysis", "domain_knowledge", "technical_writing"],
        "default_priority": 2,  # Medium priority
        "requires_approval": True,
        "timeout_hours": 72,
        "icon": "📋",
        "color": "#9C27B0"
    }
    
    REVIEW = {
        "id": "review",
        "display_name": "Code Review",
        "description": "Review code changes for quality and standards",
        "required_skills": ["code_review", "programming", "testing"],
        "default_priority": 1,  # High priority
        "requires_approval": False,
        "timeout_hours": 48,
        "icon": "👁️",
        "color": "#00BCD4"
    }
    
    TEST_FAILURE = {
        "id": "test_failure",
        "display_name": "Test Failure Analysis",
        "description": "Analyze and resolve test failures",
        "required_skills": ["testing", "debugging", "programming"],
        "default_priority": 0,  # Critical priority
        "requires_approval": False,
        "timeout_hours": 24,
        "icon": "❌",
        "color": "#E91E63"
    }
    
    # Optional: Add more types as needed
    # SECURITY_REVIEW = { ... }
    # DOCUMENTATION = { ... }
    # DEPLOYMENT = { ... }
    
    @property
    def id(self) -> str:
        """Get work item type ID"""
        return self.value["id"]
    
    @property
    def display_name(self) -> str:
        """Get human-readable display name"""
        return self.value["display_name"]
    
    @property
    def description(self) -> str:
        """Get work item type description"""
        return self.value["description"]
    
    @property
    def required_skills(self) -> List[str]:
        """Get skills required for this work item type"""
        return self.value["required_skills"]
    
    @property
    def default_priority(self) -> int:
        """Get default priority (0=highest, 4=lowest)"""
        return self.value["default_priority"]
    
    @property
    def requires_approval(self) -> bool:
        """Check if this work item type requires approval"""
        return self.value["requires_approval"]
    
    @property
    def timeout_hours(self) -> int:
        """Get default timeout in hours"""
        return self.value["timeout_hours"]
    
    @property
    def icon(self) -> str:
        """Get icon for UI display"""
        return self.value["icon"]
    
    @property
    def color(self) -> str:
        """Get color for UI display"""
        return self.value["color"]
    
    @classmethod
    def from_id(cls, type_id: str) -> Optional["WorkItemType"]:
        """Get WorkItemType from ID string"""
        for item_type in cls:
            if item_type.id == type_id:
                return item_type
        return None
    
    @classmethod
    def get_by_skill(cls, skill: str) -> List["WorkItemType"]:
        """Get work item types that require a specific skill"""
        return [item_type for item_type in cls if skill in item_type.required_skills]
    
    @classmethod
    def get_by_priority(cls, priority_level: int) -> List["WorkItemType"]:
        """Get work item types with a specific default priority"""
        return [item_type for item_type in cls if item_type.default_priority == priority_level]
    
    @classmethod
    def get_priority_order(cls) -> List["WorkItemType"]:
        """Get work item types sorted by priority (highest first)"""
        return sorted(cls, key=lambda x: x.default_priority)
    
    @classmethod
    def get_requires_approval(cls) -> List["WorkItemType"]:
        """Get work item types that require approval"""
        return [item_type for item_type in cls if item_type.requires_approval]
    
    @classmethod
    def to_list(cls) -> List[Dict[str, Any]]:
        """Convert all work item types to a list of dictionaries"""
        return [
            {
                "id": wt.id,
                "display_name": wt.display_name,
                "description": wt.description,
                "required_skills": wt.required_skills,
                "default_priority": wt.default_priority,
                "requires_approval": wt.requires_approval,
                "timeout_hours": wt.timeout_hours,
                "icon": wt.icon,
                "color": wt.color
            }
            for wt in cls
        ]


# Helper function for quick lookup
def get_work_item_type(type_id: str) -> Optional[WorkItemType]:
    """Convenience function to get work item type by ID"""
    return WorkItemType.from_id(type_id)


def get_all_work_item_types() -> List[Dict[str, Any]]:
    """Get all work item types as a list of dictionaries"""
    return WorkItemType.to_list()


def get_work_item_types_by_skill(skill: str) -> List[Dict[str, Any]]:
    """Get work item types that require a specific skill"""
    return [
        {
            "id": wt.id,
            "display_name": wt.display_name,
            "description": wt.description,
            "default_priority": wt.default_priority,
            "timeout_hours": wt.timeout_hours
        }
        for wt in WorkItemType.get_by_skill(skill)
    ]