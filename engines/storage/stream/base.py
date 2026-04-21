# engines/storage/stream/base.py

# Event Stream

# event sourcing
# message replay
# pipelines

# engines/storage/stream/base.py

from abc import ABC, abstractmethod
from typing import Any, Dict, List
from engines.storage.base_storage import BaseStorage


class StreamStorage(BaseStorage, ABC):
    """
    Event stream storage abstraction.
    """

    @abstractmethod
    async def publish(
        self,
        topic: str,
        message: Dict[str, Any],
    ) -> None:
        pass

    @abstractmethod
    async def consume(
        self,
        topic: str,
        group: str,
    ) -> List[Dict[str, Any]]:
        pass
