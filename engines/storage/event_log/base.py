from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from engines.storage.base_storage import BaseStorage


class LogStorage(BaseStorage, ABC):
    """
    Async log persistence layer.
    Used for agent execution logs and system events.
    """

    @abstractmethod
    async def log_agent_execution(self, agent_name: str, record: Dict) -> None:
        ...

    @abstractmethod
    async def list_agent_logs(self, agent_name: str) -> List[str]:
        ...

    @abstractmethod
    async def get_agent_log(self, key: str) -> Optional[Dict]:
        ...

    @abstractmethod
    async def log_event(self, event_type: str, payload: Dict) -> None:
        ...

    @abstractmethod
    async def list_events(self, event_type: Optional[str] = None) -> List[str]:
        ...

    @abstractmethod
    async def get_event(self, key: str) -> Optional[Dict]:
        ...
