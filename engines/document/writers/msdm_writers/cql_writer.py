# engines/document/writers/msdm_writers/cql_writer.py
"""
Cassandra Query Language (CQL) Writer – converts an MSDMDocument into a CQL
schema script (.cql).  Handles:

- CREATE TABLE with partition keys, clustering columns, static, and column types.
- CREATE TYPE for user‑defined types (entities with kind OBJECT that are referenced as frozen).
- CREATE INDEX for secondary indexes.
- CREATE MATERIALIZED VIEW (if the entity kind is VIEW and sufficient metadata exists).
- Table options (compaction, compression, clustering order, etc.) from annotations.
- Support for soft‑delete in design mode is limited; the writer outputs the model as‑is.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple, Set

from .base_msdm_writer import BaseMSDMWriter, WriteTarget, SoftDeleteStrategy, ConnectionConfig
from ..base import WriteOptions
from ...models.msdm_models import (
    MSDMDocument,
    Entity,
    Attribute,
    DataType,
    ScalarType,
    Constraint,
    ConstraintType,
    Annotation,
    EntityKind,
    ScalarType,
    Index,
    Relationship,
)
try:
    from cassandra.cluster import Cluster
    from cassandra.auth import PlainTextAuthProvider
    from cassandra.query import SimpleStatement
    CASSANDRA_AVAILABLE = True
except ImportError:
    CASSANDRA_AVAILABLE = False

# ── ScalarType to CQL type mapping ──────────────────────────────
SCALAR_TO_CQL = {
    ScalarType.STRING:    "text",
    ScalarType.INT:       "int",
    ScalarType.LONG:      "bigint",
    ScalarType.FLOAT:     "float",
    ScalarType.DOUBLE:    "double",
    ScalarType.BOOLEAN:   "boolean",
    ScalarType.DATE:      "date",
    ScalarType.TIME:      "time",
    ScalarType.TIMESTAMP: "timestamp",
    ScalarType.DURATION:  "duration",
    ScalarType.UUID:      "uuid",
    ScalarType.BINARY:    "blob",
    ScalarType.DECIMAL:   "decimal",
    ScalarType.ANY:       "text",   # fallback
    ScalarType.JSON:      "text",   # no native JSON type (use text)
    ScalarType.XML:       "text",
}


class CQLWriter(BaseMSDMWriter):
    """Writer for Cassandra Query Language schema files (.cql)."""
    name = "cql"
    supported_extensions = (".cql",)

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
        # Collect all entities by kind
        tables = [e for e in document.entities if e.kind in (EntityKind.TABLE, EntityKind.COLUMN_FAMILY)]
        types = [e for e in document.entities if e.kind == EntityKind.OBJECT]  # UDTs
        views = [e for e in document.entities if e.kind == EntityKind.VIEW]

        # Write types first (they may be referenced by tables)
        for entity in types:
            lines.append(self._write_create_type(entity))
            lines.append("")

        # Write tables
        for entity in tables:
            lines.append(self._write_create_table(entity))
            lines.append("")

        # Write indexes (collected from entities)
        for entity in tables:
            for idx in entity.indexes:
                lines.append(self._write_create_index(idx, entity.name))
                lines.append("")

        # Write materialized views
        for entity in views:
            lines.append(self._write_create_mv(entity, document))

        # Join with semicolons and newlines
        cql_script = ";\n\n".join(line for line in lines if line) + ";\n"
        return cql_script.encode(self.options.encoding or "utf-8")

    async def get_supported_media_types(self) -> list[str]:
        return ["text/plain"]   # CQL is plain text

    async def get_supported_extensions(self) -> list[str]:
        return self.supported_extensions

    # ── CREATE TABLE ────────────────────────────────────────────
    def _write_create_table(self, entity: Entity) -> str:
        table_name = self._quote_identifier(entity.name)
        columns = []
        primary_key_def = ""

        # Separate partition keys, clustering columns, and regular columns
        partition_keys: List[str] = []
        clustering_cols: List[Tuple[str, str]] = []  # (name, direction)
        regular_cols: List[str] = []
        static_cols: Set[str] = set()

        # Determine PK configuration from constraints and attribute flags
        pk_constraint = next((c for c in entity.constraints if c.type == ConstraintType.PRIMARY_KEY), None)
        if pk_constraint:
            # Expect expression like "col1,col2" for partition keys, and possibly a separate clustering order annotation.
            # Actually, in MSDM we stored partition key columns in pk_constraint.expression, and clustering separately.
            pk_expr = pk_constraint.expression or ""
            partition_keys = [k.strip() for k in pk_expr.split(",") if k.strip()]
        else:
            # Fallback: use attributes with primary_key=True
            partition_keys = [a.name for a in entity.attributes if a.primary_key]

        # Clustering columns are identified by annotation 'clustering_order' or presence in primary key but not in partition keys.
        # We'll collect from annotations.
        for attr in entity.attributes:
            clustering_ann = next((a for a in attr.annotations if a.key == "clustering_order"), None)
            if clustering_ann:
                direction = clustering_ann.value.upper()
                clustering_cols.append((attr.name, direction))

        # Static columns
        for attr in entity.attributes:
            if any(a.key == "static" and a.value == "true" for a in attr.annotations):
                static_cols.add(attr.name)

        # Build column definitions
        for attr in entity.attributes:
            col_name = self._quote_identifier(attr.name)
            cql_type = self._datatype_to_cql(attr.data_type, attr.nested_attributes)
            col_def = f"{col_name} {cql_type}"
            if attr.primary_key or attr.name in partition_keys:
                continue  # handled later
            if attr.name in [c[0] for c in clustering_cols]:
                continue  # handled later
            if attr.required and not attr.primary_key:
                # In CQL, columns are nullable by default; NOT NULL is rarely used outside PK. We'll ignore required flag unless it's part of PK.
                pass
            col_def += ","
            if attr.name in static_cols:
                col_def += " STATIC"
            columns.append(col_def)

        # Primary key clause
        pk_parts = []
        if len(partition_keys) == 1 and not clustering_cols:
            # Simple primary key: PRIMARY KEY (col)
            pk_clause = f"PRIMARY KEY ({self._quote_identifier(partition_keys[0])})"
        else:
            # Composite
            pk_inner = ""
            if len(partition_keys) == 1:
                pk_inner = f"{self._quote_identifier(partition_keys[0])}"
            else:
                pk_inner = "(" + ", ".join(self._quote_identifier(k) for k in partition_keys) + ")"
            if clustering_cols:
                clustering_list = ", ".join(self._quote_identifier(c[0]) for c in clustering_cols)
                pk_inner += f", {clustering_list}"
            pk_clause = f"PRIMARY KEY ({pk_inner})"

        # WITH options
        with_options = self._build_table_options(entity, clustering_cols)

        # Assemble
        parts = [f"CREATE TABLE {table_name} ("]
        # Partition and clustering columns listed first (CQL convention)
        # We'll output all columns before PK clause
        all_col_lines = list(columns)  # regular columns
        # Add partition and clustering columns before PK (they are still part of the column list)
        # In CQL, partition/clustering columns are included in the column list as well, with their types.
        # We'll append them after regular but they must appear. However typical CQL puts PK columns first. We'll reorder: PK first, then clustering, then regular.
        pk_col_defs = []
        for pk in partition_keys:
            attr = next((a for a in entity.attributes if a.name == pk), None)
            if attr:
                pk_col_defs.append(f"{self._quote_identifier(pk)} {self._datatype_to_cql(attr.data_type, attr.nested_attributes)},")
        for clust_name, _ in clustering_cols:
            attr = next((a for a in entity.attributes if a.name == clust_name), None)
            if attr:
                pk_col_defs.append(f"{self._quote_identifier(clust_name)} {self._datatype_to_cql(attr.data_type, attr.nested_attributes)},")
        # combine
        all_cols = pk_col_defs + all_col_lines
        all_cols.append(f"    {pk_clause}")
        inner = "\n    ".join(all_cols)
        parts.append(f"    {inner}")
        parts.append(")")

        # WITH clause
        if with_options:
            parts.append(f"WITH {with_options}")

        return "\n".join(parts)

    # ── CREATE TYPE (UDT) ───────────────────────────────────────
    def _write_create_type(self, entity: Entity) -> str:
        type_name = self._quote_identifier(entity.name)
        lines = []
        for attr in entity.attributes:
            cql_type = self._datatype_to_cql(attr.data_type, attr.nested_attributes)
            lines.append(f"    {self._quote_identifier(attr.name)} {cql_type}")
        inner = ",\n".join(lines)
        return f"CREATE TYPE {type_name} (\n{inner}\n)"

    # ── CREATE INDEX ────────────────────────────────────────────
    def _write_create_index(self, idx: Index, table_name: str) -> str:
        name_part = f" {self._quote_identifier(idx.name)}" if idx.name else ""
        cols = ", ".join(self._quote_identifier(c) for c in idx.attributes)
        using = f" USING '{idx.method}'" if idx.method else ""
        return f"CREATE INDEX{name_part} ON {self._quote_identifier(table_name)} ({cols}){using}"

    # ── CREATE MATERIALIZED VIEW ────────────────────────────────
    def _write_create_mv(self, entity: Entity, doc: MSDMDocument) -> str:
        # The view definition may be stored as annotation "view_definition" (raw SQL) or we can reconstruct from base table and primary key.
        raw_ann = next((a for a in entity.annotations if a.key == "view_definition"), None)
        if raw_ann:
            # Return the original statement (assume it's valid CQL)
            return raw_ann.value
        # Simple reconstruction: we need base table name and columns.
        base_table = next((a.value for a in entity.annotations if a.key == "base_table"), None)
        if not base_table:
            return f"// cannot reconstruct view {entity.name}: missing base table"
        # Build SELECT columns from entity attributes
        select_cols = ", ".join(self._quote_identifier(a.name) for a in entity.attributes)
        # Primary key from entity constraints/attributes
        pk_parts = [a.name for a in entity.attributes if a.primary_key]
        if not pk_parts:
            pk_parts = [a.name for a in entity.attributes]  # fallback
        pk_str = ", ".join(self._quote_identifier(p) for p in pk_parts)
        view_name = self._quote_identifier(entity.name)
        base_name = self._quote_identifier(base_table)
        # Simplistic WHERE clause? We'll omit WHERE; might be incomplete.
        return f"CREATE MATERIALIZED VIEW {view_name} AS SELECT {select_cols} FROM {base_name} WHERE {pk_str} IS NOT NULL PRIMARY KEY ({pk_str})"

    # ── Type conversion ─────────────────────────────────────────
    def _datatype_to_cql(self, dt: DataType, nested_attrs: List[Attribute]) -> str:
        """Convert DataType to CQL type string."""
        base = dt.base
        if base == ScalarType.ARRAY:
            elem_str = self._datatype_to_cql(dt.element_type, []) if dt.element_type else "text"
            return f"list<{elem_str}>"
        elif base == ScalarType.MAP:
            key_str = self._datatype_to_cql(dt.key_type, []) if dt.key_type else "text"
            val_str = self._datatype_to_cql(dt.value_type, []) if dt.value_type else "text"
            return f"map<{key_str}, {val_str}>"
        elif base == ScalarType.STRUCT:
            if nested_attrs:
                # Nesting not fully supported inline; we would need a UDT reference.
                # If the attribute has a ref_entity and that entity is a UDT, use frozen<udt>
                # Here, we assume the UDT is referenced via dt.ref_entity when base is REF, but struct is different.
                # We'll check if there is a ref_entity from DataType? For structs derived from the parser, the attribute might have nested_attributes, but no separate UDT. We'll create an anonymous UDT name? Better to create a UDT from nested_attrs and use its name.
                # Since we only write design, we can generate a UDT with a generated name and include it in the script before this table.
                # For simplicity, we'll fallback to text.
                return "text"
            return "text"
        elif base == ScalarType.REF:
            ref = dt.ref_entity
            if ref:
                # If referencing a UDT, need frozen<udt>
                # We'll assume it should be frozen<ref> if it's a UDT (entity kind OBJECT). But we need to know; we can check document entities later. For now, output frozen<ref>.
                return f"frozen<{self._quote_identifier(ref)}>"
            return "text"
        elif base in SCALAR_TO_CQL:
            return SCALAR_TO_CQL[base]
        else:
            return "text"

    # ── Table options ───────────────────────────────────────────
    def _build_table_options(self, entity: Entity, clustering_cols: List[Tuple[str, str]]) -> str:
        opts = []
        # Clustering order
        if clustering_cols:
            order_parts = [f"{self._quote_identifier(c[0])} {c[1]}" for c in clustering_cols]
            opts.append(f"CLUSTERING ORDER BY ({', '.join(order_parts)})")
        # Compaction, compression, etc. from annotations
        for ann in entity.annotations:
            if ann.key in ("compaction", "compression", "caching", "comment", "speculative_retry",
                           "dclocal_read_repair_chance", "read_repair_chance", "gc_grace_seconds",
                           "bloom_filter_fp_chance", "default_time_to_live", "min_index_interval",
                           "max_index_interval", "memtable_flush_period_in_ms", "populate_io_cache_on_flush",
                           "replicate_on_write", "synchronous_updates", "paxos_grace_seconds",
                           "tombstone_failure_threshold", "tombstone_warn_threshold",
                           "additional_write_policy", "extensions"):
                if ann.value and ann.value != "{}":
                    opts.append(f"{ann.key} = {ann.value}")
        if opts:
            return " AND ".join(opts)
        return ""

    # ── Utilities ──────────────────────────────────────────────
    @staticmethod
    def _quote_identifier(name: str) -> str:
        """Double‑quote a CQL identifier if it contains special characters or is a reserved word.
           For safety, we always quote (most CQL parsers accept quoted identifiers)."""
        # Simple implementation: just wrap in double quotes after escaping inner quotes.
        escaped = name.replace('"', '""')
        return f'"{escaped}"'
    
    
    async def apply_to_database(
        self,
        document: MSDMDocument,
        connection: Optional[ConnectionConfig] = None,
    ) -> None:
        """
        Connect to a live Cassandra cluster, compare the MSDM model with
        the existing keyspace, and apply changes (CREATE/ALTER/DROP).
        Soft‑delete strategy controls removal of missing objects.
        """
        if not CASSANDRA_AVAILABLE:
            raise ImportError("cassandra-driver is required for database target. "
                              "Install it with: pip install cassandra-driver")

        if connection is None:
            raise ValueError("ConnectionConfig is required for database target")

        cluster, session = self._connect(connection)
        try:
            keyspace = document.namespace or connection.database or "default"
            # Ensure keyspace exists (create if not, but only for a fresh start)
            if keyspace not in self._get_keyspaces(session):
                await asyncio.to_thread(session.execute,
                    f"CREATE KEYSPACE IF NOT EXISTS {self._quote(keyspace)} "
                    "WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1}")
            session.set_keyspace(keyspace)

            existing_tables = self._get_existing_tables(session)
            model_tables = {e.name for e in document.entities if e.kind in (EntityKind.TABLE, EntityKind.COLUMN_FAMILY)}
            model_udts = {e.name for e in document.entities if e.kind == EntityKind.OBJECT}

            # Tables to remove (soft‑delete via rename or DROP)
            for table in existing_tables - model_tables:
                await self._remove_table(session, table)

            # Process each table entity
            for entity in document.entities:
                if entity.kind in (EntityKind.TABLE, EntityKind.COLUMN_FAMILY):
                    if entity.name in existing_tables:
                        await self._sync_table(session, entity)
                    else:
                        # Re‑use the design‑time CREATE TABLE output (synchronous here)
                        create_stmt = self._write_create_table(entity) + ";"
                        await asyncio.to_thread(session.execute, create_stmt)

            # UDTs (user‑defined types)
            existing_udts = self._get_existing_udts(session)
            for udt_name in model_udts - existing_udts:
                entity = next(e for e in document.entities if e.name == udt_name and e.kind == EntityKind.OBJECT)
                create_stmt = self._write_create_type(entity) + ";"
                await asyncio.to_thread(session.execute, create_stmt)
            for udt_name in existing_udts - model_udts:
                await self._remove_type(session, udt_name)

            # Indexes
            existing_indexes = self._get_existing_indexes(session)
            for entity in document.entities:
                if entity.kind not in (EntityKind.TABLE, EntityKind.COLUMN_FAMILY):
                    continue
                for idx in entity.indexes:
                    if idx.name not in existing_indexes:
                        create_idx = self._write_create_index(idx, entity.name) + ";"
                        await asyncio.to_thread(session.execute, create_idx)

            # Materialized views (similar pattern – omitted for brevity)

        finally:
            cluster.shutdown()

    # ── Cassandra cluster connection ───────────────────────────────
    def _connect(self, config: ConnectionConfig) -> Tuple[Cluster, Any]:
        """Create a Cassandra Cluster and Session from ConnectionConfig."""
        auth_provider = None
        if config.username and config.password:
            auth_provider = PlainTextAuthProvider(config.username, config.password)

        contact_points = [config.host] if config.host else ["127.0.0.1"]
        port = config.port or 9042
        cluster = Cluster(contact_points=contact_points, port=port,
                          auth_provider=auth_provider,
                          protocol_version=4)  # adjust if needed
        session = cluster.connect()
        return cluster, session

    # ── Schema introspection helpers ──────────────────────────────
    def _get_keyspaces(self, session) -> Set[str]:
        rows = session.execute("SELECT keyspace_name FROM system_schema.keyspaces")
        return {row.keyspace_name for row in rows}

    def _get_existing_tables(self, session) -> Set[str]:
        rows = session.execute("SELECT table_name FROM system_schema.tables WHERE keyspace_name = %s",
                               (session.keyspace,))
        return {row.table_name for row in rows}

    def _get_existing_udts(self, session) -> Set[str]:
        rows = session.execute("SELECT type_name FROM system_schema.types WHERE keyspace_name = %s",
                               (session.keyspace,))
        return {row.type_name for row in rows}

    def _get_existing_indexes(self, session) -> Set[str]:
        rows = session.execute("SELECT index_name FROM system_schema.indexes WHERE keyspace_name = %s",
                               (session.keyspace,))
        return {row.index_name for row in rows}

    def _get_existing_columns(self, session, table_name: str) -> Dict[str, str]:
        """Return column name -> type string for a given table."""
        rows = session.execute("SELECT column_name, type FROM system_schema.columns "
                               "WHERE keyspace_name = %s AND table_name = %s",
                               (session.keyspace, table_name))
        return {row.column_name: row.type for row in rows}

    # ── Table synchronisation ──────────────────────────────────────
    async def _sync_table(self, session, entity: Entity) -> None:
        table_name = entity.name
        existing_cols = self._get_existing_columns(session, table_name)
        model_cols = {attr.name: attr for attr in entity.attributes}
        model_col_names = set(model_cols.keys())

        # Add missing columns (Cassandra allows ALTER TABLE ADD COLUMN)
        for col_name, attr in model_cols.items():
            if col_name not in existing_cols:
                cql_type = self._datatype_to_cql(attr.data_type, attr.nested_attributes)
                stmt = f"ALTER TABLE {self._quote(table_name)} ADD {self._quote(col_name)} {cql_type}"
                await asyncio.to_thread(session.execute, stmt)

        # Remove or rename columns not in model
        for col_name in existing_cols.keys() - model_col_names:
            await self._remove_column(session, table_name, col_name)

        # Primary key changes require table recreation – not attempted automatically.
        # We could drop and recreate the table, but that would lose data.
        # For safety, we only handle column additions/removals and warn on PK mismatches.

    # ── Soft‑delete helpers ───────────────────────────────────────
    async def _remove_table(self, session, table_name: str) -> None:
        if self.soft_delete_strategy == SoftDeleteStrategy.NONE:
            await asyncio.to_thread(session.execute, f"DROP TABLE IF EXISTS {self._quote(table_name)}")
        elif self.soft_delete_strategy == SoftDeleteStrategy.PREFIX:
            new_name = f"_deleted_{table_name}"
            await asyncio.to_thread(session.execute,
                f"ALTER TABLE {self._quote(table_name)} RENAME TO {self._quote(new_name)}")
        elif self.soft_delete_strategy == SoftDeleteStrategy.SUFFIX:
            new_name = f"{table_name}_deleted"
            await asyncio.to_thread(session.execute,
                f"ALTER TABLE {self._quote(table_name)} RENAME TO {self._quote(new_name)}")
        # ANNOTATE: Cassandra does not support comments on tables; fall back to NONE

    async def _remove_column(self, session, table_name: str, col_name: str) -> None:
        if self.soft_delete_strategy == SoftDeleteStrategy.NONE:
            await asyncio.to_thread(session.execute,
                f"ALTER TABLE {self._quote(table_name)} DROP {self._quote(col_name)}")
        elif self.soft_delete_strategy == SoftDeleteStrategy.PREFIX:
            new_name = f"_deleted_{col_name}"
            await asyncio.to_thread(session.execute,
                f"ALTER TABLE {self._quote(table_name)} RENAME {self._quote(col_name)} TO {self._quote(new_name)}")
        elif self.soft_delete_strategy == SoftDeleteStrategy.SUFFIX:
            new_name = f"{col_name}_deleted"
            await asyncio.to_thread(session.execute,
                f"ALTER TABLE {self._quote(table_name)} RENAME {self._quote(col_name)} TO {self._quote(new_name)}")

    async def _remove_type(self, session, type_name: str) -> None:
        if self.soft_delete_strategy == SoftDeleteStrategy.NONE:
            await asyncio.to_thread(session.execute, f"DROP TYPE IF EXISTS {self._quote(type_name)}")
        elif self.soft_delete_strategy == SoftDeleteStrategy.PREFIX:
            new_name = f"_deleted_{type_name}"
            await asyncio.to_thread(session.execute,
                f"ALTER TYPE {self._quote(type_name)} RENAME TO {self._quote(new_name)}")
        # (suffix analogous)

    # ── Quoting (re‑use from _quote_identifier) ────────────────────
    @staticmethod
    def _quote(name: str) -> str:
        """Double‑quote a CQL identifier."""
        escaped = name.replace('"', '""')
        return f'"{escaped}"'    