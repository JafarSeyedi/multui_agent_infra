#!/usr/bin/env python3
"""
Configuration Management - Unified configuration system for the AI development framework.

Part of the Shared module (shared/config.py)


This config.py provides:

Unified Configuration - Single source of truth for all framework settings
Multiple Formats - JSON, YAML, TOML, environment variables
Section-Based Organization - Logging, LLM, Ollama, Vector Store, State, Git, Analysis, Generation, Validation, Testing, Entry Points, Orchestration, Metrics, Security, Experimental
Environment Overrides - AI_DEV_* environment variables override config
Configuration Profiles - Development, testing, production, CI profiles
Dotted Key Access - config.get('llm.model') and config.set('llm.model', 'gpt-4')
Validation - Automatic validation of configuration values
Sensitive Data Redaction - Masks API keys and secrets in display
Default Locations - Auto-loads from .ai-dev-config.json, pyproject.toml, etc.
Global Singleton - get_config() for easy access throughout the framework
Import/Export - Save to file, export as environment variables
CLI Interface - Full CLI for configuration management

All other modules in the framework should use from ..shared.config import get_config to access configuration settings.
"""

import os
import json
import yaml
import tomllib
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from collections import defaultdict

from .logger import get_logger

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class ConfigFormat(str, Enum):
    """Configuration file format."""
    JSON = "json"
    YAML = "yaml"
    TOML = "toml"
    ENV = "env"
    INI = "ini"


class LogLevel(str, Enum):
    """Log level."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Environment(str, Enum):
    """Execution environment."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    CI = "ci"


class LLMProvider(str, Enum):
    """LLM provider."""
    DEEPSEEK = "deepseek"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    LOCAL = "local"
    CUSTOM = "custom"


# ============================================================
# CONFIGURATION SECTIONS
# ============================================================

@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: LogLevel = LogLevel.INFO
    file: Optional[Path] = None
    format: str = "console"  # console, json, detailed
    max_bytes: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    enable_console: bool = True
    enable_file: bool = False
    redact_sensitive: bool = True
    sensitive_patterns: List[str] = field(default_factory=lambda: [
        "password", "secret", "token", "key", "auth", "credential"
    ])


@dataclass
class LLMConfig:
    """LLM configuration."""
    provider: LLMProvider = LLMProvider.DEEPSEEK
    model: str = "deepseek-chat"
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    temperature: float = 0.1
    max_tokens: int = 4096
    timeout: int = 120
    max_retries: int = 3
    retry_delay: float = 1.0
    enable_cache: bool = True
    cache_ttl: int = 3600
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    cache_dir: Optional[Path] = None
    fallback_providers: List[LLMProvider] = field(default_factory=list)
    custom_headers: Dict[str, str] = field(default_factory=dict)
    # headers: Dict[str, str] = field(default_factory=dict)

@dataclass
class OllamaConfig:
    """Ollama configuration."""
    base_url: str = "http://localhost:11434"
    default_model: str = "mxbai-embed-large:latest"
    embedding_model: str = "mxbai-embed-large:latest"
    batch_size: int = 10
    max_retries: int = 3
    timeout: int = 60
    cache_enabled: bool = True
    cache_dir: Optional[Path] = None
    normalize_embeddings: bool = True


@dataclass
class VectorStoreConfig:
    """Vector store configuration."""
    persist_directory: Path = field(default_factory=lambda: Path(".ai_state/vector_store"))
    collection_prefix: str = "ai_dev"
    distance_metric: str = "cosine"  # cosine, euclidean, dot
    embedding_dimensions: int = 1024
    batch_size: int = 100
    cache_enabled: bool = True
    auto_create_collections: bool = True


@dataclass
class StateConfig:
    """State manager configuration."""
    directory: Path = field(default_factory=lambda: Path(".ai_state"))
    backend: StorageBackend = StorageBackend.JSON
    scope: StateScope = StateScope.PROJECT
    auto_save: bool = True
    save_interval: int = 60  # seconds
    max_history: int = 100
    compression: CompressionType = CompressionType.NONE
    encryption: EncryptionType = EncryptionType.NONE
    encryption_key: Optional[bytes] = None
    max_memory_entries: int = 10000
    default_ttl: Optional[int] = None
    lazy_load: bool = True
    backup_enabled: bool = True
    backup_interval: int = 3600  # seconds
    max_backups: int = 5


@dataclass
class GitConfig:
    """Git integration configuration."""
    enabled: bool = True
    auto_commit: bool = False
    commit_message_template: str = "🤖 AI: {description}"
    branch_prefix: str = "ai-dev/"
    create_pr: bool = False
    pr_labels: List[str] = field(default_factory=lambda: ["ai-generated"])
    watch_branches: List[str] = field(default_factory=lambda: ["main", "master", "develop"])


@dataclass
class AnalysisConfig:
    """Code analysis configuration."""
    scan_on_start: bool = False
    scan_on_change: bool = True
    debounce_ms: int = 500
    max_file_size_mb: int = 10
    include_patterns: List[str] = field(default_factory=lambda: ["*.py", "*.md", "*.json", "*.yaml"])
    exclude_patterns: List[str] = field(default_factory=lambda: [
        "__pycache__", "*.pyc", ".git", ".venv", "venv", "dist", "build",
        ".pytest_cache", ".mypy_cache", ".ruff_cache", ".ai_state",
        "node_modules", "migrations", "alembic"
    ])
    analyze_complexity: bool = True
    analyze_dependencies: bool = True
    analyze_security: bool = True
    max_complexity: int = 10


@dataclass
class GenerationConfig:
    """Code generation configuration."""
    output_dir: Path = field(default_factory=lambda: Path("generated"))
    backup_original: bool = True
    use_llm: bool = True
    max_iterations: int = 5
    quality_threshold: float = 0.9
    docstring_style: str = "google"  # google, numpy, sphinx
    include_tests: bool = True
    include_type_hints: bool = True
    line_length: int = 88
    indent_size: int = 4


@dataclass
class ValidationConfig:
    """Validation configuration."""
    enabled: bool = True
    validators: List[str] = field(default_factory=lambda: [
        "mypy", "ruff", "imports", "docstring", "complexity"
    ])
    fail_on_error: bool = True
    fail_on_warning: bool = False
    auto_fix: bool = False
    max_errors: int = 100
    thresholds: Dict[str, float] = field(default_factory=lambda: {
        "complexity": 10.0,
        "coverage": 80.0,
        "docstring_coverage": 90.0
    })


@dataclass
class TestingConfig:
    """Testing configuration."""
    framework: str = "pytest"
    test_paths: List[str] = field(default_factory=lambda: ["tests", "test"])
    parallel: bool = True
    workers: int = 4
    timeout: int = 300
    test_timeout: int = 30
    retry_failed: bool = True
    max_retries: int = 2
    coverage_enabled: bool = True
    coverage_threshold: float = 80.0
    detect_flaky: bool = True
    slow_threshold: float = 1.0


@dataclass
class EntryPointConfig:
    """Entry point configuration."""
    cli_enabled: bool = True
    api_enabled: bool = False
    web_enabled: bool = False
    bot_enabled: bool = False
    ide_plugin_enabled: bool = False
    
    # API settings
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    api_reload: bool = False
    
    # Web settings
    web_host: str = "127.0.0.1"
    web_port: int = 8080
    web_static_dir: str = "static"
    
    # Bot settings
    bot_token: Optional[str] = None
    bot_provider: str = "slack"  # slack, discord, telegram


@dataclass
class OrchestrationConfig:
    """Orchestration configuration."""
    workflow_engine: str = "default"
    max_concurrent_workflows: int = 3
    workflow_timeout: int = 600
    enable_scheduling: bool = False
    checkpoint_enabled: bool = True
    checkpoint_dir: Path = field(default_factory=lambda: Path(".ai_state/checkpoints"))
    human_in_the_loop: bool = True
    approval_required: bool = False
    notification_channels: List[str] = field(default_factory=lambda: ["cli"])


@dataclass
class MetricsConfig:
    """Metrics and telemetry configuration."""
    enabled: bool = True
    collect_performance: bool = True
    collect_usage: bool = True
    collect_errors: bool = True
    anonymize: bool = True
    export_format: str = "json"  # json, prometheus, datadog
    export_interval: int = 60
    retention_days: int = 30


@dataclass
class SecurityConfig:
    """Security configuration."""
    scan_dependencies: bool = True
    scan_secrets: bool = True
    scan_vulnerabilities: bool = True
    fail_on_critical: bool = True
    fail_on_high: bool = False
    allowed_licenses: List[str] = field(default_factory=lambda: [
        "MIT", "Apache-2.0", "BSD-3-Clause", "BSD-2-Clause", "ISC", "Python-2.0"
    ])
    secret_patterns: List[str] = field(default_factory=lambda: [
        "password\\s*=\\s*['\"]\\S+['\"]",
        "api_key\\s*=\\s*['\"]\\S+['\"]",
        "token\\s*=\\s*['\"]\\S+['\"]",
    ])


@dataclass
class ExperimentalConfig:
    """Experimental features configuration."""
    enabled: bool = False
    features: List[str] = field(default_factory=list)
    llm_refinement: bool = False
    auto_refactor: bool = False
    predictive_analysis: bool = False


# ============================================================
# MAIN CONFIGURATION
# ============================================================

@dataclass
class Config:
    """
    Unified configuration for the AI development framework.
    
    Features:
    - Load from multiple formats (JSON, YAML, TOML)
    - Environment variable overrides
    - Nested configuration sections
    - Configuration validation
    - Default values
    - Configuration profiles
    - Secret management
    - Hot reload support
    """
    
    # Core
    project_root: Path = field(default_factory=Path.cwd)
    project_name: str = "ai-dev-project"
    environment: Environment = Environment.DEVELOPMENT
    version: str = "1.0.0"
    debug: bool = False
    
    # Configuration sections
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    vector_store: VectorStoreConfig = field(default_factory=VectorStoreConfig)
    state: StateConfig = field(default_factory=StateConfig)
    git: GitConfig = field(default_factory=GitConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    generation: GenerationConfig = field(default_factory=GenerationConfig)
    validation: ValidationConfig = field(default_factory=ValidationConfig)
    testing: TestingConfig = field(default_factory=TestingConfig)
    entry_points: EntryPointConfig = field(default_factory=EntryPointConfig)
    orchestration: OrchestrationConfig = field(default_factory=OrchestrationConfig)
    metrics: MetricsConfig = field(default_factory=MetricsConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    experimental: ExperimentalConfig = field(default_factory=ExperimentalConfig)
    
    # Custom settings
    custom: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    _loaded_from: Optional[Path] = None
    _loaded_at: Optional[datetime] = None
    _overrides: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization setup."""
        self._apply_environment_overrides()
    
    # ============================================================
    # LOADING METHODS
    # ============================================================
    
    @classmethod
    def load(cls, path: Optional[Path] = None) -> 'Config':
        """
        Load configuration from file.
        
        Args:
            path: Path to configuration file (auto-detects format)
            
        Returns:
            Config instance
        """
        config = cls()
        
        if path and path.exists():
            config._loaded_from = path
            config._loaded_at = datetime.now()
            
            format = cls._detect_format(path)
            
            if format == ConfigFormat.JSON:
                config._load_json(path)
            elif format == ConfigFormat.YAML:
                config._load_yaml(path)
            elif format == ConfigFormat.TOML:
                config._load_toml(path)
            else:
                logger.warning(f"Unknown config format: {path}")
        
        # Load from default locations if no path provided
        if not path:
            config._load_from_default_locations()
        
        config._apply_environment_overrides()
        
        return config
    
    @classmethod
    def load_from_dict(cls, data: Dict[str, Any]) -> 'Config':
        """Load configuration from dictionary."""
        config = cls()
        config._update_from_dict(data)
        config._apply_environment_overrides()
        return config
    
    @classmethod
    def _detect_format(cls, path: Path) -> ConfigFormat:
        """Detect configuration file format."""
        suffix = path.suffix.lower()
        
        if suffix == '.json':
            return ConfigFormat.JSON
        elif suffix in ('.yaml', '.yml'):
            return ConfigFormat.YAML
        elif suffix == '.toml':
            return ConfigFormat.TOML
        elif suffix == '.env':
            return ConfigFormat.ENV
        elif suffix in ('.ini', '.cfg', '.conf'):
            return ConfigFormat.INI
        else:
            return ConfigFormat.JSON
    
    def _load_from_default_locations(self):
        """Load from default configuration locations."""
        default_paths = [
            self.project_root / ".ai-dev-config.json",
            self.project_root / ".ai-dev-config.yaml",
            self.project_root / ".ai-dev-config.yml",
            self.project_root / ".ai-dev-config.toml",
            self.project_root / "pyproject.toml",
            self.project_root / ".ai-dev" / "config.json",
            Path.home() / ".ai-dev" / "config.json",
        ]
        
        for path in default_paths:
            if path.exists():
                self._loaded_from = path
                self._loaded_at = datetime.now()
                
                format = self._detect_format(path)
                
                if format == ConfigFormat.JSON:
                    self._load_json(path)
                elif format == ConfigFormat.YAML:
                    self._load_yaml(path)
                elif format == ConfigFormat.TOML:
                    self._load_toml(path)
                
                logger.debug(f"Loaded config from {path}")
                break
    
    def _load_json(self, path: Path):
        """Load JSON configuration."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self._update_from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load JSON config: {e}")
    
    def _load_yaml(self, path: Path):
        """Load YAML configuration."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            if data:
                self._update_from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load YAML config: {e}")
    
    def _load_toml(self, path: Path):
        """Load TOML configuration."""
        try:
            with open(path, 'rb') as f:
                data = tomllib.load(f)
            
            # Handle pyproject.toml format
            if 'tool' in data and 'ai-dev' in data['tool']:
                data = data['tool']['ai-dev']
            
            self._update_from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load TOML config: {e}")
    
    def _update_from_dict(self, data: Dict[str, Any]):
        """Update configuration from dictionary."""
        # Core settings
        if 'project_root' in data:
            self.project_root = Path(data['project_root'])
        if 'project_name' in data:
            self.project_name = data['project_name']
        if 'environment' in data:
            self.environment = Environment(data['environment'])
        if 'version' in data:
            self.version = data['version']
        if 'debug' in data:
            self.debug = data['debug']
        
        # Section configurations
        section_map = {
            'logging': self.logging,
            'llm': self.llm,
            'ollama': self.ollama,
            'vector_store': self.vector_store,
            'state': self.state,
            'git': self.git,
            'analysis': self.analysis,
            'generation': self.generation,
            'validation': self.validation,
            'testing': self.testing,
            'entry_points': self.entry_points,
            'orchestration': self.orchestration,
            'metrics': self.metrics,
            'security': self.security,
            'experimental': self.experimental,
        }
        
        for key, section in section_map.items():
            if key in data:
                self._update_section(section, data[key])
        
        # Custom settings
        if 'custom' in data:
            self.custom = data['custom']
    
    def _update_section(self, section: Any, data: Dict[str, Any]):
        """Update a configuration section."""
        for key, value in data.items():
            if hasattr(section, key):
                current_value = getattr(section, key)
                
                # Handle Path conversion
                if isinstance(current_value, Path) and value is not None:
                    setattr(section, key, Path(value))
                # Handle Enum conversion
                elif isinstance(current_value, Enum) and value is not None:
                    enum_class = type(current_value)
                    try:
                        setattr(section, key, enum_class(value))
                    except ValueError:
                        pass
                else:
                    setattr(section, key, value)
    
    def _apply_environment_overrides(self):
        """Apply environment variable overrides."""
        env_prefix = "AI_DEV_"
        
        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                config_key = key[len(env_prefix):].lower()
                self._overrides[config_key] = value
                self._apply_override(config_key, value)
    
    def _apply_override(self, key: str, value: str):
        """Apply a single environment override."""
        parts = key.split('__')
        
        if len(parts) == 1:
            # Top-level setting
            if hasattr(self, parts[0]):
                self._set_value(self, parts[0], value)
        elif len(parts) == 2:
            # Section setting
            section_name, attr_name = parts
            if hasattr(self, section_name):
                section = getattr(self, section_name)
                if hasattr(section, attr_name):
                    self._set_value(section, attr_name, value)
    
    def _set_value(self, obj: Any, attr: str, value: str):
        """Set a value with type conversion."""
        current = getattr(obj, attr)
        
        if isinstance(current, bool):
            setattr(obj, attr, value.lower() in ('true', '1', 'yes', 'on'))
        elif isinstance(current, int):
            setattr(obj, attr, int(value))
        elif isinstance(current, float):
            setattr(obj, attr, float(value))
        elif isinstance(current, Path):
            setattr(obj, attr, Path(value))
        elif isinstance(current, Enum):
            enum_class = type(current)
            try:
                setattr(obj, attr, enum_class(value))
            except ValueError:
                pass
        else:
            setattr(obj, attr, value)
    
    # ============================================================
    # SAVING METHODS
    # ============================================================
    
    def save(self, path: Optional[Path] = None, format: ConfigFormat = ConfigFormat.JSON):
        """
        Save configuration to file.
        
        Args:
            path: Output path (uses loaded path if None)
            format: Output format
        """
        output_path = path or self._loaded_from
        if not output_path:
            output_path = self.project_root / ".ai-dev-config.json"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == ConfigFormat.JSON:
            self._save_json(output_path)
        elif format == ConfigFormat.YAML:
            self._save_yaml(output_path)
        elif format == ConfigFormat.TOML:
            self._save_toml(output_path)
        else:
            self._save_json(output_path)
        
        logger.info(f"Saved config to {output_path}")
    
    def _save_json(self, path: Path):
        """Save as JSON."""
        data = self.to_dict()
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
    
    def _save_yaml(self, path: Path):
        """Save as YAML."""
        data = self.to_dict()
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, indent=2)
    
    def _save_toml(self, path: Path):
        """Save as TOML."""
        data = self.to_dict()
        with open(path, 'w', encoding='utf-8') as f:
            # Simple TOML serialization
            for key, value in data.items():
                if isinstance(value, dict):
                    f.write(f"[{key}]\n")
                    for k, v in value.items():
                        f.write(f"{k} = {self._toml_value(v)}\n")
                else:
                    f.write(f"{key} = {self._toml_value(value)}\n")
    
    def _toml_value(self, value: Any) -> str:
        """Convert value to TOML string."""
        if isinstance(value, bool):
            return str(value).lower()
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, str):
            return f'"{value}"'
        elif isinstance(value, list):
            return "[" + ", ".join(self._toml_value(v) for v in value) + "]"
        else:
            return f'"{value}"'
    
    # ============================================================
    # CONVERSION METHODS
    # ============================================================
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        result = {
            'project_root': str(self.project_root),
            'project_name': self.project_name,
            'environment': self.environment.value,
            'version': self.version,
            'debug': self.debug,
        }
        
        # Add sections
        sections = [
            'logging', 'llm', 'ollama', 'vector_store', 'state', 'git',
            'analysis', 'generation', 'validation', 'testing', 'entry_points',
            'orchestration', 'metrics', 'security', 'experimental'
        ]
        
        for section_name in sections:
            section = getattr(self, section_name)
            result[section_name] = self._section_to_dict(section)
        
        if self.custom:
            result['custom'] = self.custom
        
        return result
    
    def _section_to_dict(self, section: Any) -> Dict[str, Any]:
        """Convert section to dictionary."""
        result = {}
        for key, value in asdict(section).items():
            if isinstance(value, Path):
                result[key] = str(value)
            elif isinstance(value, Enum):
                result[key] = value.value
            elif isinstance(value, datetime):
                result[key] = value.isoformat()
            else:
                result[key] = value
        return result
    
    def to_env_vars(self) -> Dict[str, str]:
        """Convert configuration to environment variables."""
        env_vars = {}
        
        def flatten(obj: Any, prefix: str = "AI_DEV_"):
            if hasattr(obj, '__dataclass_fields__'):
                for key, value in asdict(obj).items():
                    if value is not None:
                        flatten(value, f"{prefix}{key.upper()}__")
            else:
                env_vars[prefix.rstrip('_')] = str(obj)
        
        flatten(self)
        return env_vars
    
    # ============================================================
    # VALIDATION METHODS
    # ============================================================
    
    def validate(self) -> List[str]:
        """Validate configuration."""
        errors = []
        
        if not self.project_root.exists():
            errors.append(f"Project root does not exist: {self.project_root}")
        
        if self.llm.provider == LLMProvider.DEEPSEEK and not self.llm.api_key:
            if not os.environ.get("DEEPSEEK_API_KEY"):
                errors.append("DeepSeek API key not configured")
        
        if self.llm.temperature < 0 or self.llm.temperature > 2:
            errors.append("LLM temperature must be between 0 and 2")
        
        if self.generation.max_iterations < 1:
            errors.append("Generation max_iterations must be at least 1")
        
        if self.testing.workers < 1:
            errors.append("Testing workers must be at least 1")
        
        return errors
    
    def is_valid(self) -> bool:
        """Check if configuration is valid."""
        return len(self.validate()) == 0
    
    # ============================================================
    # UTILITY METHODS
    # ============================================================
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dotted key.
        
        Args:
            key: Dotted key (e.g., 'llm.model', 'analysis.max_complexity')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        parts = key.split('.')
        current = self
        
        for part in parts:
            if hasattr(current, part):
                current = getattr(current, part)
            elif isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
        
        return current
    
    def set(self, key: str, value: Any):
        """
        Set configuration value by dotted key.
        
        Args:
            key: Dotted key (e.g., 'llm.model', 'analysis.max_complexity')
            value: Value to set
        """
        parts = key.split('.')
        current = self
        
        for part in parts[:-1]:
            if hasattr(current, part):
                current = getattr(current, part)
            else:
                raise KeyError(f"Invalid configuration key: {key}")
        
        last_part = parts[-1]
        if hasattr(current, last_part):
            setattr(current, last_part, value)
        else:
            raise KeyError(f"Invalid configuration key: {key}")
    
    def merge(self, other: 'Config') -> 'Config':
        """Merge another configuration into this one."""
        for key, value in asdict(other).items():
            if value is not None:
                if hasattr(self, key):
                    current = getattr(self, key)
                    if isinstance(current, (dict, list)):
                        setattr(self, key, value)
                    elif value != current:
                        setattr(self, key, value)
        return self
    
    def copy(self) -> 'Config':
        """Create a copy of the configuration."""
        return Config.load_from_dict(self.to_dict())
    
    def reset_section(self, section_name: str):
        """Reset a configuration section to defaults."""
        default_config = Config()
        if hasattr(self, section_name) and hasattr(default_config, section_name):
            setattr(self, section_name, getattr(default_config, section_name))
    
    def reset_all(self):
        """Reset all configuration to defaults."""
        default_config = Config()
        for key in asdict(self).keys():
            if hasattr(default_config, key):
                setattr(self, key, getattr(default_config, key))
    
    # ============================================================
    # PROFILES
    # ============================================================
    
    def apply_profile(self, profile: str):
        """Apply a configuration profile."""
        profiles = {
            'development': {
                'debug': True,
                'logging': {'level': 'DEBUG'},
                'llm': {'enable_cache': True},
                'generation': {'max_iterations': 3},
            },
            'testing': {
                'debug': True,
                'logging': {'level': 'DEBUG'},
                'testing': {'coverage_enabled': True, 'detect_flaky': True},
                'validation': {'fail_on_warning': True},
            },
            'production': {
                'debug': False,
                'logging': {'level': 'WARNING'},
                'llm': {'enable_cache': True, 'temperature': 0.0},
                'generation': {'max_iterations': 10, 'backup_original': True},
                'validation': {'fail_on_error': True, 'fail_on_warning': False},
                'security': {'fail_on_critical': True, 'fail_on_high': True},
            },
            'ci': {
                'debug': False,
                'logging': {'level': 'INFO', 'format': 'json'},
                'testing': {'parallel': True, 'workers': 4},
                'validation': {'fail_on_error': True},
                'metrics': {'enabled': True},
            },
        }
        
        if profile in profiles:
            self._update_from_dict(profiles[profile])
            logger.info(f"Applied '{profile}' profile")
        else:
            logger.warning(f"Unknown profile: {profile}")
    
    # ============================================================
    # DISPLAY
    # ============================================================
    
    def display(self, show_sensitive: bool = False) -> str:
        """Get human-readable configuration display."""
        data = self.to_dict()
        
        if not show_sensitive:
            self._redact_sensitive(data)
        
        return json.dumps(data, indent=2, default=str)
    
    def _redact_sensitive(self, data: Dict[str, Any]):
        """Redact sensitive information."""
        sensitive_keys = {'api_key', 'password', 'secret', 'token', 'key', 'auth'}
        
        for key, value in list(data.items()):
            if any(s in key.lower() for s in sensitive_keys):
                data[key] = "***REDACTED***"
            elif isinstance(value, dict):
                self._redact_sensitive(value)
    
    def __repr__(self) -> str:
        return f"Config(project='{self.project_name}', env='{self.environment.value}')"


# ============================================================
# GLOBAL CONFIGURATION SINGLETON
# ============================================================

_config_instance: Optional[Config] = None


def get_config(reload: bool = False) -> Config:
    """
    Get the global configuration instance.
    
    Args:
        reload: Force reload from disk
        
    Returns:
        Config instance
    """
    global _config_instance
    
    if _config_instance is None or reload:
        _config_instance = Config.load()
    
    return _config_instance


def set_config(config: Config):
    """Set the global configuration instance."""
    global _config_instance
    _config_instance = config


def reset_config():
    """Reset the global configuration instance."""
    global _config_instance
    _config_instance = None


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for configuration management."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage AI Development Framework configuration")
    parser.add_argument("--init", action="store_true", help="Initialize configuration file")
    parser.add_argument("--show", action="store_true", help="Show current configuration")
    parser.add_argument("--show-sensitive", action="store_true", help="Show including sensitive values")
    parser.add_argument("--validate", action="store_true", help="Validate configuration")
    parser.add_argument("--get", type=str, help="Get configuration value (dotted key)")
    parser.add_argument("--set", nargs=2, metavar=('KEY', 'VALUE'), help="Set configuration value")
    parser.add_argument("--profile", type=str, help="Apply configuration profile")
    parser.add_argument("--export", action="store_true", help="Export as environment variables")
    parser.add_argument("--output", "-o", type=Path, help="Output file for export")
    parser.add_argument("--format", choices=["json", "yaml", "toml"], default="json", help="Output format")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(), help="Project root directory")
    
    args = parser.parse_args()
    
    if args.init:
        config = Config(project_root=args.project_root)
        config.save(args.project_root / ".ai-dev-config.json")
        print(f"Configuration initialized at {args.project_root / '.ai-dev-config.json'}")
        return
    
    config = Config.load()
    
    if args.validate:
        errors = config.validate()
        if errors:
            print("Configuration errors:")
            for error in errors:
                print(f"  - {error}")
        else:
            print("✅ Configuration is valid")
        return
    
    if args.show:
        print(config.display(show_sensitive=args.show_sensitive))
        return
    
    if args.get:
        value = config.get(args.get)
        if value is not None:
            print(json.dumps(value, default=str, indent=2))
        else:
            print(f"Key not found: {args.get}")
        return
    
    if args.set:
        key, value = args.set
        try:
            # Try to parse as JSON
            parsed_value = json.loads(value)
        except json.JSONDecodeError:
            parsed_value = value
        config.set(key, parsed_value)
        config.save()
        print(f"Set {key} = {parsed_value}")
        return
    
    if args.profile:
        config.apply_profile(args.profile)
        config.save()
        print(f"Applied profile: {args.profile}")
        return
    
    if args.export:
        env_vars = config.to_env_vars()
        output_lines = [f"{k}={v}" for k, v in env_vars.items()]
        output = "\n".join(output_lines)
        
        if args.output:
            args.output.write_text(output)
            print(f"Exported to {args.output}")
        else:
            print(output)
        return
    
    # Default: show help
    parser.print_help()


if __name__ == "__main__":
    main()