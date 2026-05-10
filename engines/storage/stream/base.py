# engines/storage/stream/base.py
# Event Stream
# event sourcing
# message replay
# pipelines
# engines/storage/stream/base.py
from abc import ABC
from abc import abstractmethod
from typing import Any

from engines.storage.base_storage import BaseStorage


class StreamStorage(BaseStorage, ABC):
    """
    Event stream storage abstraction.
    """

    @abstractmethod
    async def publish(
        self,
        topic: str,
        message: dict[str, Any],
    ) -> None:
        pass

    @abstractmethod
    async def consume(
        self,
        topic: str,
        group: str,
    ) -> list[dict[str, Any]]:
        pass
