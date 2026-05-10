#engines/storage/graph/base.py
# knowledge graph
# entity relationships
# engines/storage/graph/base.py
from abc import ABC
from abc import abstractmethod
from typing import Any

from engines.storage.base_storage import BaseStorage


class GraphStorage(BaseStorage, ABC):
    """
    Graph database abstraction.
    """

    @abstractmethod
    async def add_node(self, node_id: str, properties: dict[str, Any]) -> None:
        pass

    @abstractmethod
    async def add_edge(
        self,
        source: str,
        target: str,
        relation: str,
        properties: dict[str, Any] | None = None,
    ) -> None:
        pass

    @abstractmethod
    async def query(self, cypher: str) -> list[dict[str, Any]]:
        pass
