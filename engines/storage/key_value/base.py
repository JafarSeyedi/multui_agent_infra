# data types:
# state
# session
# feature flags
# config
# short memory
# engines/storage/key_value/base.py
from abc import ABC
from abc import abstractmethod
from typing import Any

from engines.storage.base_storage import BaseStorage


class KeyValueStorage(BaseStorage, ABC):
    """
    Key-value storage abstraction.
    """

    @abstractmethod
    async def set(self, key: str, value: Any) -> None:
        pass

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        pass

    @abstractmethod
    async def list_keys(self, prefix: str | None = None) -> list[str]:
        pass
