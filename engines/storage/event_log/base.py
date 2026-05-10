from abc import ABC
from abc import abstractmethod

from engines.storage.base_storage import BaseStorage


class LogStorage(BaseStorage, ABC):
    """
    Async log persistence layer.
    Used for agent execution logs and system events.
    """

    @abstractmethod
    async def log_agent_execution(self, agent_name: str, record: dict) -> None:
        ...

    @abstractmethod
    async def list_agent_logs(self, agent_name: str) -> list[str]:
        ...

    @abstractmethod
    async def get_agent_log(self, key: str) -> dict | None:
        ...

    @abstractmethod
    async def log_event(self, event_type: str, payload: dict) -> None:
        ...

    @abstractmethod
    async def list_events(self, event_type: str | None = None) -> list[str]:
        ...

    @abstractmethod
    async def get_event(self, key: str) -> dict | None:
        ...
