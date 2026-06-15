"""Plugin system for the agent engine.

Supports AGENT, STRATEGY, TOOL, SKILL, and PROTOCOL plugin types.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class AgentPlugin(ABC):
    """Base interface for all plugin types."""

    @abstractmethod
    def plugin_id(self) -> str:
        """Unique identifier for this plugin."""

    @abstractmethod
    def plugin_type(self) -> str:
        """One of: AGENT, STRATEGY, TOOL, SKILL, PROTOCOL"""

    def activate(self, registry: PluginRegistry) -> None:
        """Called when the plugin is loaded and activated."""

    def deactivate(self) -> None:
        """Called when the plugin is unloaded."""


class StrategyPlugin(AgentPlugin):
    """Base for strategy plugins."""

    def plugin_type(self) -> str:
        return "STRATEGY"

    @abstractmethod
    def scenario_name(self) -> str: ...


class ProtocolPlugin(AgentPlugin):
    """Base for protocol plugins."""

    def plugin_type(self) -> str:
        return "PROTOCOL"

    @abstractmethod
    def protocol_name(self) -> str: ...


class PluginRegistry:
    """Central registry for discovering, loading, and managing plugins."""

    def __init__(self) -> None:
        self._plugins: dict[str, AgentPlugin] = {}

    def register(self, plugin: AgentPlugin) -> None:
        pid = plugin.plugin_id()
        if pid in self._plugins:
            raise ValueError(f"Plugin '{pid}' is already registered")
        self._plugins[pid] = plugin
        plugin.activate(self)

    def unregister(self, plugin_id: str) -> None:
        plugin = self._plugins.pop(plugin_id, None)
        if plugin:
            plugin.deactivate()

    def get(self, plugin_id: str) -> AgentPlugin | None:
        return self._plugins.get(plugin_id)

    def get_by_type(self, plugin_type: str) -> list[AgentPlugin]:
        return [p for p in self._plugins.values() if p.plugin_type() == plugin_type]

    def list_plugins(self) -> list[str]:
        return list(self._plugins.keys())

    def load_from_manifest(self, manifest_path: str) -> None:
        """Load a plugin from a YAML manifest file."""
        import importlib.util
        import yaml

        with open(manifest_path) as f:
            manifest = yaml.safe_load(f)

        plugin_id = manifest.get("id")
        entry = manifest.get("entry", "")
        if not entry or ":" not in entry:
            raise ValueError(f"Invalid entry spec in {manifest_path}: '{entry}' (expected 'module:ClassName')")

        module_path, class_name = entry.split(":", 1)
        spec = importlib.util.spec_from_file_location(module_path, module_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load module from {module_path}")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        plugin_cls = getattr(mod, class_name)
        plugin = plugin_cls()
        self.register(plugin)

    def activate_all(self) -> None:
        for plugin in self._plugins.values():
            plugin.activate(self)
