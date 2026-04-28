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
from typing import Optional, Dict, Any, List, Set, Tuple

from .base_msdm_writer import BaseMSDMWriter, WriteTarget, SoftDeleteStrategy
from engines.document.writers.base import WriteOptions
from engines.document.models.msdm_models import (
    MSDMDocument,
    Entity,
    Attribute,
    Constraint,
    ConstraintType,
    Index,
    Annotation,
    EntityKind,
)


class Neo4jSchemaWriter(BaseMSDMWriter):
    """Writer for Neo4j Cypher schema files (.cypher, .cql)."""
    name = "neo4j_schema"
    supported_extensions = (".cypher", ".cql")

    def __init__(
        self,
        options: Optional[WriteOptions] = None,
        target_mode: WriteTarget = WriteTarget.DESIGN_FILE,
        soft_delete_strategy: SoftDeleteStrategy = SoftDeleteStrategy.NONE,
    ):
        super().__init__(options, target_mode, soft_delete_strategy)

    # ── Public API ─────────────────────────────────────────────────
    async def _write_design(self, document: MSDMDocument) -> bytes:
        lines = []

        # Process graph nodes and edges
        for entity in document.entities:
            if entity.kind == EntityKind.GRAPH_NODE:
                lines.extend(self._write_node_constraints(entity))
            elif entity.kind == EntityKind.GRAPH_EDGE:
                lines.extend(self._write_edge_constraints(entity))

            # Indexes for any entity with kind relevant
            if entity.kind in (EntityKind.GRAPH_NODE, EntityKind.GRAPH_EDGE):
                lines.extend(self._write_indexes(entity))

        # Append raw statements preserved from parser (round‑trip)
        for ann in document.annotations:
            if ann.key == "raw_statement":
                lines.append(ann.value)

        cypher = ";\n".join(lines) + ";\n" if lines else ""
        return cypher.encode(self.options.encoding or "utf-8")

    async def get_supported_media_types(self) -> list[str]:
        return ["text/plain"]

    async def get_supported_extensions(self) -> list[str]:
        return self.supported_extensions

    # ── Node constraints ──────────────────────────────────────────
    def _write_node_constraints(self, entity: Entity) -> List[str]:
        statements: List[str] = []
        label = self._quote_label(entity.name)

        # Collect primary key attributes (node key)
        pk_attrs = [a.name for a in entity.attributes if a.primary_key]
        if pk_attrs:
            # If a composite node key already exists via constraint, use it; otherwise create
            # We'll generate a NODE KEY constraint for all primary keys.
            props = ", ".join(f"n.{self._quote_prop(p)}" for p in pk_attrs)
            statements.append(
                f"CREATE CONSTRAINT {self._constraint_name(entity.name, 'node_key')} "
                f"FOR (n:{label}) REQUIRE ({props}) IS NODE KEY"
            )
            return statements

        # Otherwise, process uniqueness and existence individually
        unique_attrs: Set[str] = set()
        exist_attrs: Set[str] = set()

        for attr in entity.attributes:
            for c in attr.constraints:
                if c.type == ConstraintType.UNIQUE:
                    unique_attrs.add(attr.name)
                elif c.type == ConstraintType.NOT_NULL:
                    exist_attrs.add(attr.name)
            # Also treat required without primary key as existence
            if attr.required and not attr.primary_key:
                exist_attrs.add(attr.name)

        # UNIQUE constraints
        for prop in unique_attrs:
            statements.append(
                f"CREATE CONSTRAINT {self._constraint_name(entity.name, f'unique_{prop}')} "
                f"FOR (n:{label}) REQUIRE n.{self._quote_prop(prop)} IS UNIQUE"
            )

        # Existence constraints
        for prop in exist_attrs:
            statements.append(
                f"CREATE CONSTRAINT {self._constraint_name(entity.name, f'exists_{prop}')} "
                f"FOR (n:{label}) REQUIRE n.{self._quote_prop(prop)} IS NOT NULL"
            )

        return statements

    # ── Edge constraints ──────────────────────────────────────────
    def _write_edge_constraints(self, entity: Entity) -> List[str]:
        statements: List[str] = []
        rel_type = self._quote_label(entity.name)

        # Existence on relationship properties only
        for attr in entity.attributes:
            if attr.required or any(c.type == ConstraintType.NOT_NULL for c in attr.constraints):
                statements.append(
                    f"CREATE CONSTRAINT {self._constraint_name(entity.name, f'exists_{attr.name}')} "
                    f"FOR ()-[r:{rel_type}]-() REQUIRE r.{self._quote_prop(attr.name)} IS NOT NULL"
                )
        return statements

    # ── Indexes ───────────────────────────────────────────────────
    def _write_indexes(self, entity: Entity) -> List[str]:
        statements: List[str] = []
        label = self._quote_label(entity.name)
        for idx in entity.indexes:
            if not idx.attributes:
                continue
            props = ", ".join(f"n.{self._quote_prop(p)}" for p in idx.attributes)
            index_name = idx.name or f"idx_{entity.name}_{'_'.join(idx.attributes)}"
            statements.append(
                f"CREATE INDEX {self._quote_identifier(index_name)} FOR (n:{label}) ON ({props})"
            )
        return statements

    # ── Helpers ────────────────────────────────────────────────────
    @staticmethod
    def _quote_identifier(name: str) -> str:
        """Backtick‑quote an identifier if needed."""
        if not name.isidentifier() or any(ch in name for ch in " -"):
            return f"`{name}`"
        return name

    @staticmethod
    def _quote_label(name: str) -> str:
        """Backtick‑quote a label."""
        return Neo4jSchemaWriter._quote_identifier(name)

    @staticmethod
    def _quote_prop(name: str) -> str:
        """Backtick‑quote a property name."""
        return Neo4jSchemaWriter._quote_identifier(name)

    @staticmethod
    def _constraint_name(entity_name: str, suffix: str) -> str:
        """Generate a constraint name."""
        return Neo4jSchemaWriter._quote_identifier(f"constraint_{entity_name}_{suffix}")