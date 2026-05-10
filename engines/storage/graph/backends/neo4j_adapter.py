from __future__ import annotations

from typing import Any
from typing import TYPE_CHECKING

from ..base import GraphStorage

if TYPE_CHECKING:
    from neo4j import AsyncDriver


class Neo4jAdapter(GraphStorage):
    """Neo4j graph backend using the official async driver when available."""

    def __init__(self, uri: str, username: str, password: str, database: str | None = None) -> None:
        super().__init__()
        self.uri = uri
        self.username = username
        self.password = password
        self.database = database

        self._driver: AsyncDriver | None = None

    async def connect(self) -> None:
        try:
            from neo4j import AsyncGraphDatabase
        except ImportError as exc:
            raise RuntimeError("neo4j package is required for Neo4jAdapter.") from exc

        self._driver = AsyncGraphDatabase.driver(
            self.uri,
            auth=(self.username, self.password),
        )

        self._connected = True

    async def disconnect(self) -> None:
        if self._driver is not None:
            await self._driver.close()

        self._driver = None
        self._connected = False

    async def health(self) -> bool:
        if self._driver is None:
            return False

        try:
            await self._driver.verify_connectivity()
            return True
        except Exception:
            return False

    async def _run(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        await self.ensure_connected()

        assert self._driver is not None

        async with self._driver.session(database=self.database) as session:
            result = await session.run(query, parameters or {})

            return [record.data() async for record in result]

    async def add_node(self, node_id: str, properties: dict[str, Any]) -> None:
        params = {"node_id": node_id, "properties": properties}

        await self._run(
            "MERGE (n {id: $node_id}) SET n += $properties RETURN n",
            params,
        )

    async def add_edge(
        self,
        source: str,
        target: str,
        relation: str,
        properties: dict[str, Any] | None = None,
    ) -> None:
        params = {
            "source": source,
            "target": target,
            "relation": relation,
            "properties": properties or {},
        }

        query = (
            "MERGE (s {id: $source}) "
            "MERGE (t {id: $target}) "
            "MERGE (s)-[r:RELATED {type: $relation}]->(t) "
            "SET r += $properties "
            "RETURN r"
        )

        await self._run(query, params)

    async def query(self, cypher: str) -> list[dict[str, Any]]:
        return await self._run(cypher)
