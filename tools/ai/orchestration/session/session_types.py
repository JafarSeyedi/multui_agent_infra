"""
Session Types for Session Manager

Defines the type hierarchy and specialized session classes for different
interaction modalities in the system. Provides:
- Base session class with common functionality
- Specialized session types for CLI, API, IDE, Bot, Human Task, Workflow
- Type-specific validation and behavior
- Session conversion and upgrade paths

# Call this when module is loaded
_initialize_session_type_enum()
This session_types.py provides:

    SessionCapability Enum: Defines capabilities (READ, WRITE, EXECUTE, INTERACTIVE, HUMAN_TASK, FEEDBACK, etc.)
    SessionIntegration Enum: Integration types (REST_API, GRAPHQL, WEBSOCKET, CLI, IDE_PLUGIN, DISCORD_BOT, etc.)
    SessionTypeConfig: Configuration per session type (timeout, concurrency, rate limits, capabilities)
    SessionTypeRegistry: Registry for session type configurations with upgrade paths
    SessionTypeMetadata: Descriptions, icons, colors, priorities for UI display
    SessionTypeConverter: Utilities for converting between session types
    SessionTypeValidator: Validation rules for different session types (required/optional fields)
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from ...shared.logger import get_logger

logger = get_logger(__name__)


class SessionCapability(Enum):
    """Capabilities that different session types can have"""
    # Core capabilities
    READ = "read"                           # Can read data
    WRITE = "write"                         # Can write/modify data
    EXECUTE = "execute"                     # Can execute workflows/tasks
    DELETE = "delete"                       # Can delete resources
    
    # Interaction capabilities
    INTERACTIVE = "interactive"             # Supports interactive input
    BATCH = "batch"                         # Supports batch operations
    STREAMING = "streaming"                 # Supports streaming responses
    WEBHOOK = "webhook"                     # Supports webhook callbacks
    
    # Human-specific capabilities
    HUMAN_TASK = "human_task"               # Can handle human tasks
    FEEDBACK = "feedback"                   # Can provide feedback
    APPROVAL = "approval"                   # Can approve/reject
    
    # Automation capabilities
    SCHEDULING = "scheduling"               # Can schedule workflows
    TRIGGERING = "triggering"               # Can trigger events
    MONITORING = "monitoring"               # Can monitor system state
    
    # Admin capabilities
    ADMIN = "admin"                         # Administrative operations
    CONFIG = "config"                       # Can modify configuration
    AUDIT = "audit"                         # Can access audit logs


class SessionIntegration(Enum):
    """Integration types for sessions"""
    NATIVE = "native"                       # Native system session
    REST_API = "rest_api"                   # REST API session
    GRAPHQL = "graphql"                     # GraphQL API session
    WEBSOCKET = "websocket"                 # WebSocket session
    CLI = "cli"                             # Command-line interface
    IDE_PLUGIN = "ide_plugin"               # IDE plugin
    DISCORD_BOT = "discord_bot"             # Discord bot
    SLACK_BOT = "slack_bot"                 # Slack bot
    WEBHOOK = "webhook"                     # Webhook integration


@dataclass
class SessionTypeConfig:
    """Configuration for a session type"""
    session_type: 'SessionType'
    capabilities: List[SessionCapability]
    default_timeout_minutes: int
    max_concurrent_sessions: int
    requires_auth: bool
    supports_persistence: bool
    supports_streaming: bool
    rate_limit_per_minute: int
    allowed_origins: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_type": self.session_type.value,
            "capabilities": [c.value for c in self.capabilities],
            "default_timeout_minutes": self.default_timeout_minutes,
            "max_concurrent_sessions": self.max_concurrent_sessions,
            "requires_auth": self.requires_auth,
            "supports_persistence": self.supports_persistence,
            "supports_streaming": self.supports_streaming,
            "rate_limit_per_minute": self.rate_limit_per_minute,
            "allowed_origins": self.allowed_origins
        }


# Import SessionType from session_manager to avoid circular import
# Using string reference for type hints
SessionType = None  # Will be set at runtime


class SessionTypeRegistry:
    """
    Registry for session type configurations and behaviors.
    
    Provides:
    - Session type registration and lookup
    - Capability-based filtering
    - Type-specific configuration
    - Upgrade paths between session types
    """
    
    _instance = None
    _configs: Dict[str, SessionTypeConfig] = {}
    _upgrade_paths: Dict[str, Dict[str, List[str]]] = {}  # from_type -> {to_type: [steps]}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self) -> None:
        """Initialize registry with default session types"""
        self._register_default_configs()
        self._register_upgrade_paths()
    
    def _register_default_configs(self) -> None:
        """Register default session type configurations"""
        # CLI Session
        self.register_config(SessionTypeConfig(
            session_type=SessionType.CLI,
            capabilities=[
                SessionCapability.READ,
                SessionCapability.WRITE,
                SessionCapability.EXECUTE,
                SessionCapability.INTERACTIVE,
                SessionCapability.HUMAN_TASK,
                SessionCapability.FEEDBACK
            ],
            default_timeout_minutes=60,
            max_concurrent_sessions=5,
            requires_auth=False,
            supports_persistence=True,
            supports_streaming=False,
            rate_limit_per_minute=60
        ))
        
        # API Session
        self.register_config(SessionTypeConfig(
            session_type=SessionType.API,
            capabilities=[
                SessionCapability.READ,
                SessionCapability.WRITE,
                SessionCapability.EXECUTE,
                SessionCapability.BATCH,
                SessionCapability.WEBHOOK,
                SessionCapability.TRIGGERING
            ],
            default_timeout_minutes=30,
            max_concurrent_sessions=100,
            requires_auth=True,
            supports_persistence=False,
            supports_streaming=False,
            rate_limit_per_minute=300,
            allowed_origins=["*"]
        ))
        
        # IDE Plugin Session
        self.register_config(SessionTypeConfig(
            session_type=SessionType.IDE,
            capabilities=[
                SessionCapability.READ,
                SessionCapability.WRITE,
                SessionCapability.EXECUTE,
                SessionCapability.INTERACTIVE,
                SessionCapability.HUMAN_TASK,
                SessionCapability.FEEDBACK,
                SessionCapability.MONITORING
            ],
            default_timeout_minutes=120,
            max_concurrent_sessions=3,
            requires_auth=True,
            supports_persistence=True,
            supports_streaming=True,
            rate_limit_per_minute=120
        ))
        
        # Bot Session (Discord/Slack)
        self.register_config(SessionTypeConfig(
            session_type=SessionType.BOT,
            capabilities=[
                SessionCapability.READ,
                SessionCapability.EXECUTE,
                SessionCapability.HUMAN_TASK,
                SessionCapability.FEEDBACK,
                SessionCapability.TRIGGERING
            ],
            default_timeout_minutes=1440,  # 24 hours
            max_concurrent_sessions=50,
            requires_auth=False,
            supports_persistence=True,
            supports_streaming=True,
            rate_limit_per_minute=30
        ))
        
        # Human Task Session
        self.register_config(SessionTypeConfig(
            session_type=SessionType.HUMAN_TASK,
            capabilities=[
                SessionCapability.READ,
                SessionCapability.WRITE,
                SessionCapability.HUMAN_TASK,
                SessionCapability.FEEDBACK,
                SessionCapability.APPROVAL,
                SessionCapability.INTERACTIVE
            ],
            default_timeout_minutes=30,
            max_concurrent_sessions=10,
            requires_auth=True,
            supports_persistence=True,
            supports_streaming=False,
            rate_limit_per_minute=20
        ))
        
        # Workflow Session
        self.register_config(SessionTypeConfig(
            session_type=SessionType.WORKFLOW,
            capabilities=[
                SessionCapability.READ,
                SessionCapability.WRITE,
                SessionCapability.EXECUTE,
                SessionCapability.SCHEDULING,
                SessionCapability.MONITORING
            ],
            default_timeout_minutes=720,  # 12 hours
            max_concurrent_sessions=200,
            requires_auth=True,
            supports_persistence=True,
            supports_streaming=False,
            rate_limit_per_minute=1000
        ))
        
        # Service Session
        self.register_config(SessionTypeConfig(
            session_type=SessionType.SERVICE,
            capabilities=[
                SessionCapability.READ,
                SessionCapability.WRITE,
                SessionCapability.EXECUTE,
                SessionCapability.DELETE,
                SessionCapability.BATCH,
                SessionCapability.SCHEDULING,
                SessionCapability.MONITORING,
                SessionCapability.ADMIN
            ],
            default_timeout_minutes=43200,  # 30 days
            max_concurrent_sessions=50,
            requires_auth=True,
            supports_persistence=True,
            supports_streaming=False,
            rate_limit_per_minute=5000
        ))
        
        # Web Session
        self.register_config(SessionTypeConfig(
            session_type=SessionType.WEB,
            capabilities=[
                SessionCapability.READ,
                SessionCapability.WRITE,
                SessionCapability.EXECUTE,
                SessionCapability.INTERACTIVE,
                SessionCapability.HUMAN_TASK,
                SessionCapability.FEEDBACK
            ],
            default_timeout_minutes=60,
            max_concurrent_sessions=10,
            requires_auth=True,
            supports_persistence=True,
            supports_streaming=True,
            rate_limit_per_minute=100,
            allowed_origins=["http://localhost:3000", "https://app.example.com"]
        ))
        
        # System Session
        self.register_config(SessionTypeConfig(
            session_type=SessionType.SYSTEM,
            capabilities=[
                SessionCapability.READ,
                SessionCapability.WRITE,
                SessionCapability.EXECUTE,
                SessionCapability.DELETE,
                SessionCapability.ADMIN,
                SessionCapability.CONFIG,
                SessionCapability.AUDIT,
                SessionCapability.MONITORING
            ],
            default_timeout_minutes=1440,
            max_concurrent_sessions=10,
            requires_auth=True,
            supports_persistence=True,
            supports_streaming=False,
            rate_limit_per_minute=10000
        ))
    
    def _register_upgrade_paths(self) -> None:
        """Register session upgrade paths"""
        self._upgrade_paths = {
            SessionType.CLI.value: {
                SessionType.API.value: ["authenticate", "generate_api_key"],
                SessionType.WEB.value: ["authenticate", "create_web_session"]
            },
            SessionType.API.value: {
                SessionType.SERVICE.value: ["verify_credentials", "elevate_permissions"]
            },
            SessionType.HUMAN_TASK.value: {
                SessionType.WORKFLOW.value: ["complete_current_task", "create_workflow_session"]
            },
            SessionType.BOT.value: {
                SessionType.API.value: ["authenticate_bot", "get_api_token"]
            }
        }
    
    def register_config(self, config: SessionTypeConfig) -> None:
        """Register a session type configuration"""
        self._configs[config.session_type.value] = config
        logger.debug(f"Registered session type config: {config.session_type.value}")
    
    def get_config(self, session_type) -> Optional[SessionTypeConfig]:
        """Get configuration for a session type"""
        if isinstance(session_type, Enum):
            session_type = session_type.value
        return self._configs.get(session_type)
    
    def get_capabilities(self, session_type) -> List[SessionCapability]:
        """Get capabilities for a session type"""
        config = self.get_config(session_type)
        return config.capabilities if config else []
    
    def has_capability(self, session_type, capability: SessionCapability) -> bool:
        """Check if session type has a specific capability"""
        capabilities = self.get_capabilities(session_type)
        return capability in capabilities
    
    def get_all_session_types(self) -> List[str]:
        """Get all registered session types"""
        return list(self._configs.keys())
    
    def get_session_types_by_capability(self, 
                                       capability: SessionCapability) -> List[str]:
        """Get session types that have a specific capability"""
        result = []
        for type_name, config in self._configs.items():
            if capability in config.capabilities:
                result.append(type_name)
        return result
    
    def get_upgrade_path(self, from_type, to_type) -> Optional[List[str]]:
        """Get upgrade steps from one session type to another"""
        if isinstance(from_type, Enum):
            from_type = from_type.value
        if isinstance(to_type, Enum):
            to_type = to_type.value
        
        return self._upgrade_paths.get(from_type, {}).get(to_type)
    
    def can_upgrade(self, from_type, to_type) -> bool:
        """Check if session can be upgraded from one type to another"""
        return self.get_upgrade_path(from_type, to_type) is not None


# Session type specific metadata and behaviors
class SessionTypeMetadata:
    """Metadata and behavior for specific session types"""
    
    @staticmethod
    def get_type_description(session_type) -> str:
        """Get description for a session type"""
        descriptions = {
            SessionType.CLI: "Command-line interface session for terminal users",
            SessionType.API: "REST/GraphQL API session for programmatic access",
            SessionType.IDE: "IDE plugin session for VS Code, PyCharm, etc.",
            SessionType.WEB: "Web interface session for browser users",
            SessionType.BOT: "Chat bot session for Discord, Slack, etc.",
            SessionType.HUMAN_TASK: "Human-in-the-loop task assignment session",
            SessionType.WORKFLOW: "Workflow execution session",
            SessionType.SERVICE: "Service-to-service integration session",
            SessionType.SYSTEM: "System internal session"
        }
        return descriptions.get(session_type, "Unknown session type")
    
    @staticmethod
    def get_icon(session_type) -> str:
        """Get icon representation for session type"""
        icons = {
            SessionType.CLI: "💻",
            SessionType.API: "🔌",
            SessionType.IDE: "📝",
            SessionType.WEB: "🌐",
            SessionType.BOT: "🤖",
            SessionType.HUMAN_TASK: "👤",
            SessionType.WORKFLOW: "⚙️",
            SessionType.SERVICE: "🔗",
            SessionType.SYSTEM: "🏢"
        }
        return icons.get(session_type, "❓")
    
    @staticmethod
    def get_color(session_type) -> str:
        """Get color for session type (for UI)"""
        colors = {
            SessionType.CLI: "#00FF00",      # Green
            SessionType.API: "#FF9900",      # Orange
            SessionType.IDE: "#007ACC",      # Blue
            SessionType.WEB: "#FF5733",      # Red-Orange
            SessionType.BOT: "#5865F2",      # Discord Blurple
            SessionType.HUMAN_TASK: "#9B59B6",  # Purple
            SessionType.WORKFLOW: "#3498DB", # Light Blue
            SessionType.SERVICE: "#E74C3C",  # Red
            SessionType.SYSTEM: "#2C3E50"    # Dark Blue
        }
        return colors.get(session_type, "#808080")  # Gray default
    
    @staticmethod
    def get_priority(session_type) -> int:
        """
        Get processing priority for session type.
        Higher number = higher priority.
        """
        priorities = {
            SessionType.SYSTEM: 100,
            SessionType.WORKFLOW: 80,
            SessionType.SERVICE: 70,
            SessionType.API: 60,
            SessionType.HUMAN_TASK: 50,
            SessionType.CLI: 40,
            SessionType.IDE: 40,
            SessionType.WEB: 35,
            SessionType.BOT: 30
        }
        return priorities.get(session_type, 10)
    
    @staticmethod
    def get_rate_limit_headers(session_type) -> Dict[str, str]:
        """Get recommended rate limit headers for session type"""
        headers = {
            SessionType.API: "X-RateLimit-Limit",
            SessionType.CLI: "X-Session-Limit",
            SessionType.BOT: "X-Bot-RateLimit"
        }
        return {headers.get(session_type, "X-RateLimit-Limit"): "60"}
    
    @staticmethod
    def is_interactive(session_type) -> bool:
        """Check if session type supports interactive mode"""
        interactive_types = [SessionType.CLI, SessionType.IDE, SessionType.WEB, SessionType.HUMAN_TASK]
        return session_type in interactive_types
    
    @staticmethod
    def supports_webhooks(session_type) -> bool:
        """Check if session type supports webhooks"""
        return session_type in [SessionType.API, SessionType.SERVICE]
    
    @staticmethod
    def requires_user_agent(session_type) -> bool:
        """Check if session type requires user agent header"""
        return session_type in [SessionType.API, SessionType.WEB, SessionType.BOT]


# Session type conversion utilities
class SessionTypeConverter:
    """Utilities for converting between session types"""
    
    @staticmethod
    def get_compatible_types(session_type) -> List[SessionType]:
        """Get session types compatible with the given type"""
        compatibility = {
            SessionType.CLI: [SessionType.API, SessionType.WEB],
            SessionType.API: [SessionType.SERVICE, SessionType.WORKFLOW],
            SessionType.BOT: [SessionType.API],
            SessionType.HUMAN_TASK: [SessionType.WORKFLOW],
            SessionType.IDE: [SessionType.API],
            SessionType.WEB: [SessionType.API]
        }
        return compatibility.get(session_type, [])
    
    @staticmethod
    def get_downgrade_path(session_type) -> List[SessionType]:
        """Get possible downgrade paths for a session type"""
        downgrades = {
            SessionType.SERVICE: [SessionType.API],
            SessionType.WORKFLOW: [SessionType.HUMAN_TASK, SessionType.API],
            SessionType.API: [SessionType.CLI, SessionType.WEB],
            SessionType.WEB: [SessionType.CLI]
        }
        return downgrades.get(session_type, [])
    
    @staticmethod
    def estimate_conversion_cost(from_type: SessionType, 
                                to_type: SessionType) -> Dict[str, Any]:
        """Estimate cost/complexity of converting between session types"""
        if from_type == to_type:
            return {"cost": 0, "complexity": "none", "steps": []}
        
        registry = SessionTypeRegistry()
        steps = registry.get_upgrade_path(from_type, to_type)
        
        if steps:
            return {
                "cost": len(steps) * 10,
                "complexity": "low" if len(steps) <= 2 else "medium",
                "steps": steps,
                "estimated_seconds": len(steps) * 5
            }
        
        return {
            "cost": 100,
            "complexity": "high",
            "steps": ["manual_review_required"],
            "estimated_seconds": 300
        }


# Session type validation rules
class SessionTypeValidator:
    """Validation rules for different session types"""
    
    @staticmethod
    def validate_session_data(session_type, data: Dict[str, Any]) -> List[str]:
        """Validate session data for specific session type"""
        errors = []
        
        if session_type == SessionType.API:
            if "api_key" not in data and "token" not in data:
                errors.append("API session requires api_key or token")
        
        elif session_type == SessionType.BOT:
            if "bot_id" not in data:
                errors.append("Bot session requires bot_id")
            if "platform" not in data:
                errors.append("Bot session requires platform (discord/slack)")
        
        elif session_type == SessionType.IDE:
            if "plugin_version" not in data:
                errors.append("IDE session requires plugin_version")
            if "editor" not in data:
                errors.append("IDE session requires editor type")
        
        elif session_type == SessionType.HUMAN_TASK:
            if "human_id" not in data:
                errors.append("Human task session requires human_id")
            if "assignment_id" not in data:
                errors.append("Human task session requires assignment_id")
        
        elif session_type == SessionType.WORKFLOW:
            if "workflow_id" not in data:
                errors.append("Workflow session requires workflow_id")
        
        return errors
    
    @staticmethod
    def get_required_fields(session_type) -> List[str]:
        """Get required fields for session type"""
        required = {
            SessionType.API: ["api_key"],
            SessionType.BOT: ["bot_id", "platform"],
            SessionType.IDE: ["plugin_version", "editor"],
            SessionType.HUMAN_TASK: ["human_id", "assignment_id"],
            SessionType.WORKFLOW: ["workflow_id"],
            SessionType.SERVICE: ["service_name", "service_version"],
            SessionType.SYSTEM: ["system_component"]
        }
        return required.get(session_type, [])
    
    @staticmethod
    def get_optional_fields(session_type) -> List[str]:
        """Get optional fields for session type"""
        optional = {
            SessionType.CLI: ["terminal_type", "shell", "columns", "rows"],
            SessionType.API: ["user_agent", "accept_header", "content_type"],
            SessionType.IDE: ["workspace_path", "project_name"],
            SessionType.WEB: ["referer", "screen_size", "language"],
            SessionType.BOT: ["guild_id", "channel_id", "user_mention"],
            SessionType.HUMAN_TASK: ["context", "deadline", "priority"],
            SessionType.WORKFLOW: ["parent_execution_id", "trigger"],
            SessionType.SERVICE: ["callback_url", "retry_config"],
            SessionType.SYSTEM: ["component_instance", "cluster_id"]
        }
        return optional.get(session_type, [])


# Export utilities for easy access
def get_session_type_config(session_type) -> Optional[SessionTypeConfig]:
    """Get configuration for a session type"""
    return SessionTypeRegistry().get_config(session_type)


def session_type_has_capability(session_type, capability: SessionCapability) -> bool:
    """Check if session type has capability"""
    return SessionTypeRegistry().has_capability(session_type, capability)


def get_session_types_with_capability(capability: SessionCapability) -> List[str]:
    """Get all session types with a capability"""
    return SessionTypeRegistry().get_session_types_by_capability(capability)


def validate_session_for_type(session_type, data: Dict[str, Any]) -> List[str]:
    """Validate session data for type"""
    return SessionTypeValidator.validate_session_data(session_type, data)


# Import SessionType from session_manager after definition to avoid circular import
def _initialize_session_type_enum():
    """Initialize SessionType reference (called after session_manager is imported)"""
    global SessionType
    if SessionType is None:
        from .session_manager import SessionType as ST
        SessionType = ST


# Call this when module is loaded
_initialize_session_type_enum()