# engines/document/writers/msdm_writers/neo4j_schema_writer.py
"""
Neo4j Schema Writer – converts an MSDMDocument into Cypher DDL statements (.cypher).
Handles:
- CREATE CONSTRAINT FOR node keys, uniqueness, and existence (node & relationship).
- CREATE INDEX for each label and property index.
- Raw statements preserved from the parser are written verbatim for round‑trip.
Soft‑delete is not applicable; the writer produces a clean schema snapshot.
"""
from __future__ import annotations

from typing import Optional

from ...models.msdm_models import ConstraintType
from ...models.msdm_models import Entity
from ...models.msdm_models import EntityKind
from ...models.msdm_models import MSDMDocument
from ..base import WriteOptions
from .base_msdm_writer import BaseMSDMWriter, ConnectionConfig
from .base_msdm_writer import SoftDeleteStrategy
from .base_msdm_writer import WriteTarget

try:
    from neo4j import AsyncGraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False


class Neo4jSchemaWriter(BaseMSDMWriter):
    name = "neo4j_schema"
    supported_extensions = (".cypher", ".cql")

    def __init__(
        self,
        options: WriteOptions | None = None,
        target_mode: WriteTarget = WriteTarget.DESIGN_FILE,
        soft_delete_strategy: SoftDeleteStrategy = SoftDeleteStrategy.NONE,
    ):
        super().__init__(options, target_mode, soft_delete_strategy)

    async def _write_design(self, document: MSDMDocument) -> bytes:
        lines = []
        for entity in document.entities:
            if entity.kind == EntityKind.GRAPH_NODE:
                lines.extend(self._write_node_constraints(entity))
            elif entity.kind == EntityKind.GRAPH_EDGE:
                lines.extend(self._write_edge_constraints(entity))
            if entity.kind in (EntityKind.GRAPH_NODE, EntityKind.GRAPH_EDGE):
                lines.extend(self._write_indexes(entity))

        for ann in document.annotations:
            if ann.key == "raw_statement":
                lines.append(ann.value)

        cypher = ";\n".join(lines) + ";\n" if lines else ""
        return cypher.encode(getattr(self.options, "encoding", "utf-8") or "utf-8")

    def get_supported_media_types(self) -> list[str]:
        return ["text/plain"]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    def _write_node_constraints(self, entity: Entity) -> list[str]:
        statements: list[str] = []
        label = self._quote_label(entity.name)
        pk_attrs = [
            a.name for a in entity.attributes
            if any(c.type == ConstraintType.PRIMARY_KEY for c in a.constraints)
        ]
        if pk_attrs and len(pk_attrs)>0:
            props = ", ".join(f"n.{self._quote_prop(p)}" for p in pk_attrs)
            statements.append(
                f"CREATE CONSTRAINT {self._constraint_name(entity.name, 'node_key')} "
                f"FOR (n:{label}) REQUIRE ({props}) IS NODE KEY"
            )
            return statements

        unique_attrs: set[str] = set()
        exist_attrs: set[str] = set()
        for attr in entity.attributes:
            for c in attr.constraints:
                if c.type == ConstraintType.UNIQUE:
                    unique_attrs.add(attr.name)
                elif c.type == ConstraintType.NOT_NULL:
                    exist_attrs.add(attr.name)
            if attr.required and not any(c.type == ConstraintType.PRIMARY_KEY for c in attr.constraints):
                exist_attrs.add(attr.name)

        for prop in unique_attrs:
            statements.append(
                f"CREATE CONSTRAINT {self._constraint_name(entity.name, f'unique_{prop}')} "
                f"FOR (n:{label}) REQUIRE n.{self._quote_prop(prop)} IS UNIQUE"
            )
        for prop in exist_attrs:
            statements.append(
                f"CREATE CONSTRAINT {self._constraint_name(entity.name, f'exists_{prop}')} "
                f"FOR (n:{label}) REQUIRE n.{self._quote_prop(prop)} IS NOT NULL"
            )
        return statements

    def _write_edge_constraints(self, entity: Entity) -> list[str]:
        statements: list[str] = []
        rel_type = self._quote_label(entity.name)
        for attr in entity.attributes:
            if attr.required or any(c.type == ConstraintType.NOT_NULL for c in attr.constraints):
                statements.append(
                    f"CREATE CONSTRAINT {self._constraint_name(entity.name, f'exists_{attr.name}')} "
                    f"FOR ()-[r:{rel_type}]-() REQUIRE r.{self._quote_prop(attr.name)} IS NOT NULL"
                )
        return statements

    def _write_indexes(self, entity: Entity) -> list[str]:
        statements: list[str] = []
        label = self._quote_label(entity.name)
        for idx in entity.indexes:
            if not idx.attributes:
                continue
            props = ", ".join(f"n.{self._quote_prop(p.name)}" for p in idx.attributes)
            index_name = idx.name or f"idx_{entity.name}_{'_'.join([a.name for a in idx.attributes])}"
            statements.append(
                f"CREATE INDEX {self._quote_identifier(index_name)} FOR (n:{label}) ON ({props})"
            )
        return statements

    @staticmethod
    def _quote_identifier(name: str) -> str:
        return f"`{name}`" if not name.isidentifier() or any(ch in name for ch in " -") else name

    @staticmethod
    def _quote_label(name: str) -> str:
        return Neo4jSchemaWriter._quote_identifier(name)

    @staticmethod
    def _quote_prop(name: str) -> str:
        return Neo4jSchemaWriter._quote_identifier(name)

    @staticmethod
    def _constraint_name(entity_name: str, suffix: str) -> str:
        return Neo4jSchemaWriter._quote_identifier(f"constraint_{entity_name}_{suffix}")

    async def apply_to_database(
        self,
        document: MSDMDocument,
        connection: ConnectionConfig | None = None,
    ) -> None:
        if not NEO4J_AVAILABLE:
            raise ImportError("neo4j is required. pip install neo4j")
        if connection is None:
            raise ValueError("ConnectionConfig required")

        uri = connection.url or f"bolt://{connection.host or 'localhost'}:{connection.port or 7687}"
        auth: tuple[str, str] | None = None
        if connection.username and connection.password:
            auth = (connection.username, connection.password)
        driver = AsyncGraphDatabase.driver(uri, auth=auth)
        try:
            async with driver.session() as session:
                for entity in document.entities:
                    if entity.kind == EntityKind.GRAPH_NODE:
                        for stmt in self._write_node_constraints(entity):
                            await session.run(stmt)
                        for stmt in self._write_indexes(entity):
                            await session.run(stmt)
                    elif entity.kind == EntityKind.GRAPH_EDGE:
                        for stmt in self._write_edge_constraints(entity):
                            await session.run(stmt)
        finally:
            await driver.close()