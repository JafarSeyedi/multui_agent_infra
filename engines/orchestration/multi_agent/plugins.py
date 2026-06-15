from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BasePlugin(ABC):
    @abstractmethod
    async def on_session_start(
        self, app_name: str, user_id: str, session_id: str,
    ) -> None:
        ...

    @abstractmethod
    async def on_session_end(
        self, app_name: str, user_id: str, session_id: str,
    ) -> None:
        ...

    @abstractmethod
    async def before_agent_execution(
        self, agent_name: str, input_data: Any,
    ) -> Any | None:
        ...

    @abstractmethod
    async def after_agent_execution(
        self, agent_name: str, input_data: Any, output_data: Any,
    ) -> None:
        ...


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: list[BasePlugin] = []

    def register(self, plugin: BasePlugin) -> None:
        self._plugins.append(plugin)

    def unregister(self, plugin: BasePlugin) -> None:
        self._plugins.remove(plugin)

    @property
    def plugins(self) -> list[BasePlugin]:
        return list(self._plugins)

    async def fire_session_start(
        self, app_name: str, user_id: str, session_id: str,
    ) -> None:
        for plugin in self._plugins:
            await plugin.on_session_start(app_name, user_id, session_id)

    async def fire_session_end(
        self, app_name: str, user_id: str, session_id: str,
    ) -> None:
        for plugin in self._plugins:
            await plugin.on_session_end(app_name, user_id, session_id)

    async def fire_before_agent(
        self, agent_name: str, input_data: Any,
    ) -> Any | None:
        for plugin in self._plugins:
            result = await plugin.before_agent_execution(agent_name, input_data)
            if result is not None:
                return result
        return None

    async def fire_after_agent(
        self, agent_name: str, input_data: Any, output_data: Any,
    ) -> None:
        for plugin in self._plugins:
            await plugin.after_agent_execution(agent_name, input_data, output_data)
