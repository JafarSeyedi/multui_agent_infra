from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class StorageAdapter(ABC):
    """Abstract base adapter for all storage types."""

    @abstractmethod
    def save(self, key: str, data: Dict[str, Any]) -> None:
        """Persist a record."""
        pass

    @abstractmethod
    def load(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve a record by key."""
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete a record."""
        pass

    @abstractmethod
    def list_keys(self, prefix: Optional[str] = None) -> list[str]:
        """List keys optionally filtered by prefix."""
        pass
