from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List


class StorageAdapter(ABC):
    """Abstract base adapter for key-value storage systems."""

    @abstractmethod
    async def save(self, key: str, data: Dict[str, Any]) -> None:
        """Persist a record."""
        pass

    @abstractmethod
    async def load(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve a record by key."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete a record."""
        pass

    @abstractmethod
    async def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """List keys optionally filtered by prefix."""
        pass
