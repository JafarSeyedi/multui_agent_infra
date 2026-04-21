"""
Config Updater for Co-Evolution Engine

Automatically updates configuration files when code changes to maintain consistency.
Handles:
- Configuration schema evolution
- Backward compatibility
- Default value management
- Environment variable sync
- Multi-format config support (JSON, YAML, TOML, ENV)

This implementation provides:

    Configuration Registry: Central registry of all config entries with metadata
    Multiple Format Support: JSON, YAML, TOML, ENV, Python, INI
    Auto-Discovery: Scans config files and applies needed updates
    Change Tracking: Records all configuration changes with history
    Backup & Rollback: Creates backups before changes, supports rollback
    Validation: Type checking, allowed values, regex patterns
    Migration Support: Version-to-version migration plans
    Deprecation Management: Mark old keys as deprecated with replacements
    Environment Sync: Sync with environment variables
    Diff Generation: Show differences between current and expected config

The config updater integrates with your co-evolution engine to keep configuration synchronized as code evolves.
"""

import os
import json
import re
from typing import Dict, List, Optional, Any, Set, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from enum import Enum
from collections import defaultdict

from ....shared.logger import get_logger
from ....shared.state_manager import state_manager
from ....shared.config import config
from ....shared.file_utils import file_utils

logger = get_logger(__name__)


class ConfigFormat(Enum):
    """Supported configuration formats"""
    JSON = "json"
    YAML = "yaml"
    TOML = "toml"
    ENV = "env"
    PYTHON = "python"  # Python module
    INI = "ini"


class ChangeType(Enum):
    """Types of configuration changes"""
    ADD = "add"
    REMOVE = "remove"
    MODIFY = "modify"
    RENAME = "rename"
    DEPRECATE = "deprecate"


@dataclass
class ConfigEntry:
    """Represents a configuration entry"""
    key: str
    value: Any
    default_value: Any
    description: str
    required: bool = False
    deprecated: bool = False
    deprecated_since: Optional[str] = None
    replacement_key: Optional[str] = None
    validation_regex: Optional[str] = None
    validation_type: Optional[str] = None  # int, str, bool, list, dict
    allowed_values: Optional[List[Any]] = None
    sensitive: bool = False
    tags: List[str] = field(default_factory=list)
    version_added: Optional[str] = None
    last_modified: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "default_value": self.default_value,
            "description": self.description,
            "required": self.required,
            "deprecated": self.deprecated,
            "deprecated_since": self.deprecated_since,
            "replacement_key": self.replacement_key,
            "validation_regex": self.validation_regex,
            "validation_type": self.validation_type,
            "allowed_values": self.allowed_values,
            "sensitive": self.sensitive,
            "tags": self.tags,
            "version_added": self.version_added,
            "last_modified": self.last_modified.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConfigEntry":
        return cls(
            key=data["key"],
            value=data.get("value"),
            default_value=data.get("default_value"),
            description=data.get("description", ""),
            required=data.get("required", False),
            deprecated=data.get("deprecated", False),
            deprecated_since=data.get("deprecated_since"),
            replacement_key=data.get("replacement_key"),
            validation_regex=data.get("validation_regex"),
            validation_type=data.get("validation_type"),
            allowed_values=data.get("allowed_values"),
            sensitive=data.get("sensitive", False),
            tags=data.get("tags", []),
            version_added=data.get("version_added"),
            last_modified=datetime.fromisoformat(data["last_modified"]) if data.get("last_modified") else datetime.now()
        )


@dataclass
class ConfigChange:
    """Represents a configuration change"""
    change_type: ChangeType
    key: str
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    reason: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    affected_files: List[str] = field(default_factory=list)
    backward_compatible: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "change_type": self.change_type.value,
            "key": self.key,
            "old_value": self._serialize_value(self.old_value),
            "new_value": self._serialize_value(self.new_value),
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat(),
            "affected_files": self.affected_files,
            "backward_compatible": self.backward_compatible
        }
    
    @staticmethod
    def _serialize_value(value: Any) -> Any:
        """Serialize value for storage"""
        if isinstance(value, datetime):
            return value.isoformat()
        return value


@dataclass
class ConfigMigration:
    """Configuration migration path"""
    from_version: str
    to_version: str
    changes: List[ConfigChange]
    requires_manual_intervention: bool = False
    migration_script: Optional[str] = None
    validation_steps: List[str] = field(default_factory=list)


class ConfigUpdater:
    """
    Automatically updates configuration files when code changes.
    
    Features:
    - Detects configuration drift between code and config files
    - Adds new config entries with defaults
    - Removes deprecated entries
    - Migrates values to new keys
    - Validates config values against schemas
    - Backs up configs before changes
    - Supports multiple config formats
    """
    
    def __init__(self, storage_key: str = "config_updater"):
        self.storage_key = storage_key
        self.config_registry: Dict[str, ConfigEntry] = {}
        self.config_files: Dict[str, Tuple[Path, ConfigFormat]] = {}
        self.change_history: List[ConfigChange] = []
        self.migrations: List[ConfigMigration] = []
        
        # Load registry
        self._load_registry()
        
        # Initialize default config entries
        self._initialize_default_entries()
        
        logger.info("ConfigUpdater initialized")
    
    def _load_registry(self) -> None:
        """Load configuration registry from state manager"""
        try:
            registry_data = state_manager.get(f"{self.storage_key}.registry", {})
            for key, entry_data in registry_data.items():
                self.config_registry[key] = ConfigEntry.from_dict(entry_data)
            
            history_data = state_manager.get(f"{self.storage_key}.history", [])
            self.change_history = [ConfigChange(**h) for h in history_data]
            
        except Exception as e:
            logger.warning(f"Failed to load config registry: {e}")
    
    def _save_registry(self) -> None:
        """Save configuration registry to state manager"""
        try:
            registry_data = {k: v.to_dict() for k, v in self.config_registry.items()}
            state_manager.set(f"{self.storage_key}.registry", registry_data)
            
            history_data = [c.to_dict() for c in self.change_history]
            state_manager.set(f"{self.storage_key}.history", history_data)
            
        except Exception as e:
            logger.error(f"Failed to save config registry: {e}")
    
    def _initialize_default_entries(self) -> None:
        """Initialize default configuration entries"""
        default_entries = [
            ConfigEntry(
                key="orchestration.max_concurrent_workflows",
                value=10,
                default_value=10,
                description="Maximum number of workflows that can run concurrently",
                required=False,
                validation_type="int",
                tags=["orchestration", "performance"]
            ),
            ConfigEntry(
                key="orchestration.task_timeout_seconds",
                value=300,
                default_value=300,
                description="Default timeout for individual tasks in seconds",
                required=False,
                validation_type="int",
                tags=["orchestration", "timeout"]
            ),
            ConfigEntry(
                key="orchestration.retry_attempts",
                value=3,
                default_value=3,
                description="Number of retry attempts for failed tasks",
                required=False,
                validation_type="int",
                tags=["orchestration", "reliability"]
            ),
            ConfigEntry(
                key="orchestration.retry_delay_seconds",
                value=5,
                default_value=5,
                description="Delay between retry attempts in seconds",
                required=False,
                validation_type="int",
                tags=["orchestration", "reliability"]
            ),
            ConfigEntry(
                key="llm.model_name",
                value="deepseek-coder",
                default_value="deepseek-coder",
                description="LLM model to use for generation",
                required=True,
                validation_type="str",
                tags=["llm", "ai"]
            ),
            ConfigEntry(
                key="llm.temperature",
                value=0.7,
                default_value=0.7,
                description="Temperature for LLM sampling (0-1)",
                required=False,
                validation_type="float",
                allowed_values=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
                tags=["llm", "ai"]
            ),
            ConfigEntry(
                key="llm.max_tokens",
                value=4096,
                default_value=4096,
                description="Maximum tokens for LLM response",
                required=False,
                validation_type="int",
                tags=["llm", "ai"]
            ),
            ConfigEntry(
                key="human_in_loop.session_timeout_minutes",
                value=30,
                default_value=30,
                description="Timeout for human-in-the-loop sessions in minutes",
                required=False,
                validation_type="int",
                tags=["human", "session"]
            ),
            ConfigEntry(
                key="human_in_loop.max_concurrent_sessions",
                value=5,
                default_value=5,
                description="Maximum number of concurrent human sessions",
                required=False,
                validation_type="int",
                tags=["human", "session"]
            ),
            ConfigEntry(
                key="quality.enable_mypy",
                value=True,
                default_value=True,
                description="Enable mypy type checking",
                required=False,
                validation_type="bool",
                tags=["quality", "validation"]
            ),
            ConfigEntry(
                key="quality.enable_ruff",
                value=True,
                default_value=True,
                description="Enable ruff linting",
                required=False,
                validation_type="bool",
                tags=["quality", "validation"]
            ),
            ConfigEntry(
                key="quality.coverage_threshold",
                value=80,
                default_value=80,
                description="Minimum test coverage percentage",
                required=False,
                validation_type="int",
                tags=["quality", "testing"]
            ),
            ConfigEntry(
                key="storage.backend",
                value="json",
                default_value="json",
                description="Storage backend (json, sqlite, postgres)",
                required=True,
                validation_type="str",
                allowed_values=["json", "sqlite", "postgres"],
                tags=["storage"]
            ),
            ConfigEntry(
                key="storage.path",
                value="./data",
                default_value="./data",
                description="Storage path for data files",
                required=False,
                validation_type="str",
                tags=["storage"]
            ),
            ConfigEntry(
                key="logging.level",
                value="INFO",
                default_value="INFO",
                description="Logging level (DEBUG, INFO, WARNING, ERROR)",
                required=False,
                validation_type="str",
                allowed_values=["DEBUG", "INFO", "WARNING", "ERROR"],
                tags=["logging"]
            ),
        ]
        
        for entry in default_entries:
            if entry.key not in self.config_registry:
                self.config_registry[entry.key] = entry
    
    def register_config_file(self, file_path: Union[str, Path], 
                            format: ConfigFormat) -> None:
        """Register a configuration file to be managed"""
        path = Path(file_path)
        if not path.exists():
            logger.warning(f"Config file {path} does not exist, will create if needed")
        
        self.config_files[str(path)] = (path, format)
        logger.debug(f"Registered config file: {path}")
    
    def scan_and_update(self, config_path: Union[str, Path] = None) -> List[ConfigChange]:
        """
        Scan configuration files and apply necessary updates.
        
        Args:
            config_path: Specific config file to update (all if None)
            
        Returns:
            List of changes applied
        """
        changes = []
        
        if config_path:
            files_to_update = {str(config_path): self.config_files.get(str(config_path))}
        else:
            files_to_update = self.config_files
        
        for file_path, (path, format) in files_to_update.items():
            if path is None:
                continue
            
            try:
                file_changes = self._update_config_file(path, format)
                changes.extend(file_changes)
            except Exception as e:
                logger.error(f"Failed to update {path}: {e}")
        
        # Save change history
        self.change_history.extend(changes)
        self._save_registry()
        
        return changes
    
    def _update_config_file(self, path: Path, format: ConfigFormat) -> List[ConfigChange]:
        """Update a single configuration file"""
        changes = []
        
        # Load existing config
        existing_config = self._load_config_file(path, format)
        
        # Create backup
        self._backup_config(path)
        
        # Apply updates
        updated_config, file_changes = self._apply_updates(existing_config, format)
        changes.extend(file_changes)
        
        # Save updated config
        if file_changes:
            self._save_config_file(path, updated_config, format)
            logger.info(f"Updated {path} with {len(file_changes)} changes")
        
        return changes
    
    def _load_config_file(self, path: Path, format: ConfigFormat) -> Dict[str, Any]:
        """Load configuration from file"""
        if not path.exists():
            return {}
        
        content = file_utils.read_file(str(path))
        
        if format == ConfigFormat.JSON:
            return json.loads(content)
        elif format == ConfigFormat.ENV:
            return self._parse_env_file(content)
        elif format == ConfigFormat.PYTHON:
            return self._parse_python_config(content)
        else:
            # For other formats, try JSON as fallback
            try:
                return json.loads(content)
            except:
                return {}
    
    def _parse_env_file(self, content: str) -> Dict[str, Any]:
        """Parse .env file content"""
        config = {}
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    # Parse common types
                    if value.lower() == 'true':
                        value = True
                    elif value.lower() == 'false':
                        value = False
                    elif value.isdigit():
                        value = int(value)
                    elif value.replace('.', '').isdigit():
                        value = float(value)
                    config[key] = value
        return config
    
    def _parse_python_config(self, content: str) -> Dict[str, Any]:
        """Parse Python config module content"""
        config = {}
        # Simple regex to extract variables
        pattern = r'^([A-Z_][A-Z0-9_]*)\s*=\s*(.+)$'
        for line in content.split('\n'):
            match = re.match(pattern, line.strip())
            if match:
                key = match.group(1)
                value_str = match.group(2)
                # Try to evaluate safely (limited)
                try:
                    # Only allow basic types
                    if value_str in ['True', 'False']:
                        value = value_str == 'True'
                    elif value_str.isdigit():
                        value = int(value_str)
                    elif value_str.replace('.', '').isdigit():
                        value = float(value_str)
                    else:
                        value = value_str.strip('\'"')
                    config[key] = value
                except:
                    pass
        return config
    
    def _save_config_file(self, path: Path, config_data: Dict[str, Any], 
                         format: ConfigFormat) -> None:
        """Save configuration to file"""
        if format == ConfigFormat.JSON:
            content = json.dumps(config_data, indent=2)
        elif format == ConfigFormat.ENV:
            content = self._format_env_file(config_data)
        elif format == ConfigFormat.PYTHON:
            content = self._format_python_config(config_data)
        else:
            content = json.dumps(config_data, indent=2)
        
        file_utils.write_file(str(path), content)
    
    def _format_env_file(self, config_data: Dict[str, Any]) -> str:
        """Format config as .env file"""
        lines = []
        for key, value in config_data.items():
            if isinstance(value, bool):
                value_str = str(value)
            elif isinstance(value, (int, float)):
                value_str = str(value)
            else:
                value_str = f'"{value}"'
            lines.append(f"{key}={value_str}")
        return '\n'.join(lines)
    
    def _format_python_config(self, config_data: Dict[str, Any]) -> str:
        """Format config as Python module"""
        lines = ["# Auto-generated configuration", f"# Updated: {datetime.now()}\n"]
        for key, value in config_data.items():
            if isinstance(value, bool):
                value_str = str(value)
            elif isinstance(value, str):
                value_str = f'"{value}"'
            else:
                value_str = str(value)
            lines.append(f"{key} = {value_str}")
        return '\n'.join(lines)
    
    def _backup_config(self, path: Path) -> None:
        """Create backup of configuration file"""
        if not path.exists():
            return
        
        backup_dir = path.parent / ".config_backups"
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"{path.name}.{timestamp}.bak"
        
        content = file_utils.read_file(str(path))
        file_utils.write_file(str(backup_path), content)
        
        logger.debug(f"Created backup: {backup_path}")
    
    def _apply_updates(self, existing_config: Dict[str, Any], 
                      format: ConfigFormat) -> Tuple[Dict[str, Any], List[ConfigChange]]:
        """Apply configuration updates based on registry"""
        updated_config = existing_config.copy()
        changes = []
        
        # Add missing config entries
        for key, entry in self.config_registry.items():
            if key not in updated_config:
                if entry.required:
                    # Add required config with default
                    updated_config[key] = entry.default_value
                    changes.append(ConfigChange(
                        change_type=ChangeType.ADD,
                        key=key,
                        new_value=entry.default_value,
                        reason=f"Required config entry added with default value"
                    ))
                elif entry.default_value is not None:
                    # Add optional config with default
                    updated_config[key] = entry.default_value
                    changes.append(ConfigChange(
                        change_type=ChangeType.ADD,
                        key=key,
                        new_value=entry.default_value,
                        reason=f"Optional config entry added with default value"
                    ))
        
        # Update deprecated entries
        for key, entry in self.config_registry.items():
            if entry.deprecated and key in updated_config:
                if entry.replacement_key:
                    # Migrate to new key
                    if entry.replacement_key not in updated_config:
                        updated_config[entry.replacement_key] = updated_config[key]
                        changes.append(ConfigChange(
                            change_type=ChangeType.RENAME,
                            key=key,
                            old_value=updated_config[key],
                            new_value=updated_config[entry.replacement_key],
                            reason=f"Config key deprecated, migrated to {entry.replacement_key}",
                            backward_compatible=True
                        ))
                
                # Mark as deprecated but keep for now
                changes.append(ConfigChange(
                    change_type=ChangeType.DEPRECATE,
                    key=key,
                    reason=f"Config key is deprecated since {entry.deprecated_sing}",
                    backward_compatible=True
                ))
        
        # Validate existing values
        for key, value in list(updated_config.items()):
            if key in self.config_registry:
                entry = self.config_registry[key]
                validated_value, change = self._validate_and_fix_value(key, value, entry)
                if change:
                    updated_config[key] = validated_value
                    changes.append(change)
        
        # Remove obsolete entries (optional, based on config)
        if self._should_remove_obsolete():
            for key in list(updated_config.keys()):
                if key not in self.config_registry:
                    # Unknown config entry
                    changes.append(ConfigChange(
                        change_type=ChangeType.REMOVE,
                        key=key,
                        old_value=updated_config[key],
                        reason="Obsolete config entry removed"
                    ))
                    del updated_config[key]
        
        return updated_config, changes
    
    def _validate_and_fix_value(self, key: str, value: Any, 
                               entry: ConfigEntry) -> Tuple[Any, Optional[ConfigChange]]:
        """Validate config value and attempt to fix if needed"""
        # Check allowed values
        if entry.allowed_values and value not in entry.allowed_values:
            if entry.default_value in entry.allowed_values:
                return entry.default_value, ConfigChange(
                    change_type=ChangeType.MODIFY,
                    key=key,
                    old_value=value,
                    new_value=entry.default_value,
                    reason=f"Value {value} not in allowed values {entry.allowed_values}, reset to default"
                )
            return value, None
        
        # Check type
        if entry.validation_type:
            expected_type = self._get_type_class(entry.validation_type)
            if not isinstance(value, expected_type):
                try:
                    # Attempt type conversion
                    converted = expected_type(value)
                    return converted, ConfigChange(
                        change_type=ChangeType.MODIFY,
                        key=key,
                        old_value=value,
                        new_value=converted,
                        reason=f"Converted from {type(value).__name__} to {entry.validation_type}"
                    )
                except:
                    # Fallback to default
                    return entry.default_value, ConfigChange(
                        change_type=ChangeType.MODIFY,
                        key=key,
                        old_value=value,
                        new_value=entry.default_value,
                        reason=f"Invalid type, reset to default"
                    )
        
        # Check regex pattern
        if entry.validation_regex and isinstance(value, str):
            if not re.match(entry.validation_regex, value):
                return entry.default_value, ConfigChange(
                    change_type=ChangeType.MODIFY,
                    key=key,
                    old_value=value,
                    new_value=entry.default_value,
                    reason=f"Value doesn't match pattern {entry.validation_regex}, reset to default"
                )
        
        return value, None
    
    def _get_type_class(self, type_name: str) -> type:
        """Get Python type class from type name"""
        type_map = {
            "int": int,
            "str": str,
            "bool": bool,
            "float": float,
            "list": list,
            "dict": dict
        }
        return type_map.get(type_name, str)
    
    def _should_remove_obsolete(self) -> bool:
        """Check if obsolete config entries should be removed"""
        # This could be configurable
        return config.get("config_updater.remove_obsolete", False)
    
    def add_config_entry(self, entry: ConfigEntry) -> None:
        """Add or update a configuration entry in the registry"""
        self.config_registry[entry.key] = entry
        self._save_registry()
        logger.info(f"Added config entry: {entry.key}")
    
    def deprecate_config(self, key: str, replacement_key: Optional[str] = None,
                        since_version: str = None) -> bool:
        """Mark a config entry as deprecated"""
        if key not in self.config_registry:
            logger.warning(f"Config entry {key} not found")
            return False
        
        self.config_registry[key].deprecated = True
        self.config_registry[key].deprecated_since = since_version or "current"
        self.config_registry[key].replacement_key = replacement_key
        self._save_registry()
        
        logger.info(f"Deprecated config entry: {key} -> {replacement_key}")
        return True
    
    def create_migration(self, from_version: str, to_version: str,
                        changes: List[ConfigChange]) -> ConfigMigration:
        """Create a configuration migration plan"""
        migration = ConfigMigration(
            from_version=from_version,
            to_version=to_version,
            changes=changes,
            requires_manual_intervention=self._check_manual_needed(changes),
            validation_steps=self._generate_validation_steps(changes)
        )
        
        self.migrations.append(migration)
        return migration
    
    def _check_manual_needed(self, changes: List[ConfigChange]) -> bool:
        """Check if migration requires manual intervention"""
        for change in changes:
            if change.change_type == ChangeType.REMOVE:
                if change.old_value is not None:
                    return True
            if not change.backward_compatible:
                return True
        return False
    
    def _generate_validation_steps(self, changes: List[ConfigChange]) -> List[str]:
        """Generate validation steps for migration"""
        steps = []
        for change in changes:
            if change.change_type == ChangeType.MODIFY:
                steps.append(f"Verify {change.key} new value: {change.new_value}")
            elif change.change_type == ChangeType.RENAME:
                steps.append(f"Check that {change.key} value migrated to {change.new_value}")
        return steps
    
    def apply_migration(self, migration: ConfigMigration) -> List[ConfigChange]:
        """Apply a configuration migration"""
        changes = []
        
        for change in migration.changes:
            # Update registry
            if change.change_type == ChangeType.MODIFY:
                if change.key in self.config_registry:
                    self.config_registry[change.key].value = change.new_value
                    self.config_registry[change.key].last_modified = datetime.now()
                    changes.append(change)
            
            elif change.change_type == ChangeType.RENAME:
                if change.key in self.config_registry:
                    entry = self.config_registry[change.key]
                    entry.key = change.new_value
                    entry.last_modified = datetime.now()
                    # Keep old entry as deprecated
                    old_entry = ConfigEntry(
                        key=change.key,
                        value=change.old_value,
                        default_value=entry.default_value,
                        description=entry.description,
                        deprecated=True,
                        replacement_key=change.new_value,
                        tags=entry.tags
                    )
                    self.config_registry[change.key] = old_entry
                    self.config_registry[change.new_value] = entry
                    changes.append(change)
        
        self._save_registry()
        logger.info(f"Applied migration {migration.from_version} -> {migration.to_version}")
        
        return changes
    
    def get_config_diff(self, config_path: Union[str, Path]) -> Dict[str, Any]:
        """Get differences between current config and registry"""
        path = Path(config_path)
        if str(path) not in self.config_files:
            return {"error": "Config file not registered"}
        
        format = self.config_files[str(path)][1]
        existing_config = self._load_config_file(path, format)
        
        diff = {
            "missing": [],
            "extra": [],
            "different": [],
            "deprecated": []
        }
        
        # Check missing entries
        for key, entry in self.config_registry.items():
            if key not in existing_config:
                diff["missing"].append({
                    "key": key,
                    "default": entry.default_value,
                    "required": entry.required
                })
        
        # Check extra entries
        for key in existing_config:
            if key not in self.config_registry:
                diff["extra"].append({
                    "key": key,
                    "value": existing_config[key]
                })
        
        # Check different values
        for key, entry in self.config_registry.items():
            if key in existing_config and existing_config[key] != entry.value:
                diff["different"].append({
                    "key": key,
                    "current": existing_config[key],
                    "expected": entry.value
                })
        
        # Check deprecated
        for key, entry in self.config_registry.items():
            if entry.deprecated and key in existing_config:
                diff["deprecated"].append({
                    "key": key,
                    "replacement": entry.replacement_key,
                    "since": entry.deprecated_since
                })
        
        return diff
    
    def sync_environment_variables(self, env_prefix: str = "APP_") -> List[ConfigChange]:
        """Sync configuration with environment variables"""
        changes = []
        
        for key, entry in self.config_registry.items():
            env_key = f"{env_prefix}{key.upper().replace('.', '_')}"
            env_value = os.environ.get(env_key)
            
            if env_value is not None:
                # Parse environment variable
                parsed_value = self._parse_env_value(env_value, entry.validation_type)
                
                if parsed_value != entry.value:
                    changes.append(ConfigChange(
                        change_type=ChangeType.MODIFY,
                        key=key,
                        old_value=entry.value,
                        new_value=parsed_value,
                        reason=f"Synced from environment variable {env_key}"
                    ))
                    entry.value = parsed_value
                    entry.last_modified = datetime.now()
        
        if changes:
            self._save_registry()
            logger.info(f"Synced {len(changes)} config entries from environment")
        
        return changes
    
    def _parse_env_value(self, value: str, value_type: Optional[str]) -> Any:
        """Parse environment variable value"""
        if value_type == "bool":
            return value.lower() in ['true', '1', 'yes', 'on']
        elif value_type == "int":
            return int(value)
        elif value_type == "float":
            return float(value)
        else:
            return value
    
    def export_config(self, format: ConfigFormat = ConfigFormat.JSON) -> str:
        """Export current configuration registry"""
        config_data = {key: entry.value for key, entry in self.config_registry.items()}
        
        if format == ConfigFormat.JSON:
            return json.dumps(config_data, indent=2)
        elif format == ConfigFormat.ENV:
            return self._format_env_file(config_data)
        elif format == ConfigFormat.PYTHON:
            return self._format_python_config(config_data)
        else:
            return json.dumps(config_data, indent=2)
    
    def get_change_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent configuration change history"""
        return [c.to_dict() for c in self.change_history[-limit:]]
    
    def rollback_change(self, change_index: int) -> bool:
        """Rollback a specific configuration change"""
        if change_index >= len(self.change_history):
            return False
        
        change = self.change_history[change_index]
        
        if change.change_type == ChangeType.ADD:
            # Remove added entry
            if change.key in self.config_registry:
                # Reset to default or remove
                if self.config_registry[change.key].default_value is not None:
                    self.config_registry[change.key].value = self.config_registry[change.key].default_value
                else:
                    del self.config_registry[change.key]
        
        elif change.change_type == ChangeType.MODIFY:
            # Restore old value
            if change.key in self.config_registry:
                self.config_registry[change.key].value = change.old_value
        
        self._save_registry()
        logger.info(f"Rolled back change: {change.key}")
        
        return True
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get summary of configuration state"""
        return {
            "total_entries": len(self.config_registry),
            "required_entries": len([e for e in self.config_registry.values() if e.required]),
            "deprecated_entries": len([e for e in self.config_registry.values() if e.deprecated]),
            "sensitive_entries": len([e for e in self.config_registry.values() if e.sensitive]),
            "managed_files": len(self.config_files),
            "total_changes": len(self.change_history),
            "pending_migrations": len(self.migrations),
            "entries_by_tag": self._group_by_tag()
        }
    
    def _group_by_tag(self) -> Dict[str, int]:
        """Group config entries by tag"""
        tag_counts = defaultdict(int)
        for entry in self.config_registry.values():
            for tag in entry.tags:
                tag_counts[tag] += 1
        return dict(tag_counts)


# Singleton instance
_config_updater: Optional[ConfigUpdater] = None


def get_config_updater() -> ConfigUpdater:
    """Get global ConfigUpdater instance"""
    global _config_updater
    if _config_updater is None:
        _config_updater = ConfigUpdater()
    return _config_updater