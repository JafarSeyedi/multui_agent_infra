# engines/document/writers/msdm_writers/sql_ddl_writer.py
"""
SQL DDL Writer – converts an MSDMDocument into a SQL DDL script (.sql).
Supports CREATE TABLE with all columns, constraints (PRIMARY KEY, UNIQUE,
CHECK, FOREIGN KEY), indexes, and CREATE VIEW statements.  Soft‑delete
is not applied to DDL; the script always reflects the current model.
"""

from __future__ import annotations
from typing import Optional, Dict, Any, List, Tuple, Set

from .base_msdm_writer import BaseMSDMWriter, WriteTarget, SoftDeleteStrategy, ConnectionConfig
import asyncio
from sqlalchemy import create_engine, inspect, MetaData, Table, Column, text, DDL
from sqlalchemy.engine import Engine, Connection
from sqlalchemy.types import TypeEngine, String as SAString, Integer, BigInteger, Float, Date, DateTime, Boolean, LargeBinary
from engines.document.writers.base import WriteOptions
from engines.document.models.msdm_models import (
    MSDMDocument,
    Entity,
    Attribute,
    DataType,
    Constraint,
    ConstraintType,
    Index,
    Annotation,
    EntityKind,
    ScalarType,
)



# ── ScalarType to SQL type string (generic ANSI SQL) ──────────────
_SCALAR_TO_SQL: Dict[ScalarType, str] = {
    ScalarType.STRING:    "VARCHAR",
    ScalarType.INT:       "INTEGER",
    ScalarType.LONG:      "BIGINT",
    ScalarType.FLOAT:     "REAL",
    ScalarType.DOUBLE:    "DOUBLE PRECISION",
    ScalarType.BOOLEAN:   "BOOLEAN",
    ScalarType.DATE:      "DATE",
    ScalarType.TIME:      "TIME",
    ScalarType.TIMESTAMP: "TIMESTAMP",
    ScalarType.BINARY:    "BLOB",
    ScalarType.DECIMAL:   "DECIMAL",
    ScalarType.DURATION:  "INTERVAL",
    ScalarType.UUID:      "CHAR(36)",
    ScalarType.ANY:       "TEXT",
    ScalarType.JSON:      "JSON",
    ScalarType.XML:       "XML",
}


class SqlDDLWriter(BaseMSDMWriter):
    """Writer for SQL DDL script (.sql, .ddl)."""
    name = "sql_ddl"
    supported_extensions = (".sql", ".ddl")

    def __init__(
        self,
        options: Optional[WriteOptions] = None,
        target_mode: WriteTarget = WriteTarget.DESIGN_FILE,
        soft_delete_strategy: SoftDeleteStrategy = SoftDeleteStrategy.NONE,
    ):
        super().__init__(options, target_mode, soft_delete_strategy)

    async def _write_design(self, document: MSDMDocument) -> bytes:
        lines: List[str] = []

        # Separate view entities from table entities
        tables: List[Entity] = [e for e in document.entities
                                if e.kind in (EntityKind.TABLE,)]
        views: List[Entity] = [e for e in document.entities
                               if e.kind == EntityKind.VIEW]

        # Write CREATE TABLE statements
        for entity in tables:
            lines.append(self._build_create_table(entity))
            lines.append("")

        # Write indexes (standalone CREATE INDEX)
        for entity in tables:
            for idx in entity.indexes:
                lines.append(self._build_create_index(idx, entity.name))

        # Write CREATE VIEW statements
        for entity in views:
            # Views store the original DDL in an annotation
            ddl = self._get_annotation(entity, "view_definition")
            if ddl:
                lines.append(ddl)
            else:
                lines.append(f"CREATE VIEW {self._quote(entity.name)} AS SELECT * FROM ...")
            lines.append("")

        # Append raw DDL statements that were preserved from parser
        for ann in document.annotations:
            if ann.key == "raw_ddl":
                lines.append(ann.value)

        script = ";\n\n".join(line for line in lines if line) + ";\n"
        return script.encode(self.options.encoding or "utf-8")

    async def get_supported_media_types(self) -> list[str]:
        return ["text/plain"]

    async def get_supported_extensions(self) -> list[str]:
        return self.supported_extensions


    # ── CREATE TABLE ─────────────────────────────────────────────
    def _build_create_table(self, entity: Entity) -> str:
        table_name = self._quote(entity.name)
        # Columns
        columns: List[str] = []
        constraints: List[str] = []

        for attr in entity.attributes:
            col_def = self._column_definition(attr)
            columns.append(col_def)
            # Inline constraints from attribute are included in _column_definition

        # Table‑level constraints
        for c in entity.constraints:
            constr_sql = self._constraint_to_sql(c, table_name)
            if constr_sql:
                constraints.append(constr_sql)

        all_parts = columns + constraints
        body = ",\n  ".join(all_parts)
        return f"CREATE TABLE {table_name} (\n  {body}\n)"

    def _column_definition(self, attr: Attribute) -> str:
        name = self._quote(attr.name)
        type_str = self._datatype_to_sql(attr.data_type)
        parts = [f"{name} {type_str}"]

        # Inline constraints
        for c in attr.constraints:
            if c.type == ConstraintType.NOT_NULL:
                parts.append("NOT NULL")
            elif c.type == ConstraintType.PRIMARY_KEY:
                # Inline PK (single column)
                parts.append("PRIMARY KEY")
            elif c.type == ConstraintType.UNIQUE:
                parts.append("UNIQUE")
            elif c.type == ConstraintType.CHECK:
                if c.expression:
                    parts.append(f"CHECK ({c.expression})")
            elif c.type == ConstraintType.DEFAULT:
                if c.expression:
                    parts.append(f"DEFAULT {c.expression}")
            elif c.type == ConstraintType.FOREIGN_KEY:
                # Inline FK cannot be fully expressed here; will be table-level
                pass

        # Additional modifiers from annotations (e.g., AUTO_INCREMENT)
        if any(a.key == "auto_increment" for a in attr.annotations):
            parts.append("AUTO_INCREMENT")

        return " ".join(parts)

    def _constraint_to_sql(self, c: Constraint, table_name: str) -> Optional[str]:
        """Convert a table‑level constraint to SQL fragment."""
        name_part = f"CONSTRAINT {self._quote(c.name)} " if c.name else ""
        if c.type == ConstraintType.PRIMARY_KEY:
            cols = self._normalize_columns(c.expression)
            return f"{name_part}PRIMARY KEY ({', '.join(cols)})"
        if c.type == ConstraintType.UNIQUE:
            cols = self._normalize_columns(c.expression)
            return f"{name_part}UNIQUE ({', '.join(cols)})"
        if c.type == ConstraintType.CHECK:
            return f"{name_part}CHECK ({c.expression})" if c.expression else None
        if c.type == ConstraintType.FOREIGN_KEY:
            local_cols = self._normalize_columns(c.expression)
            if c.referenced_entity and c.referenced_attributes:
                ref_cols = [self._quote(col) for col in c.referenced_attributes]
                ref_table = self._quote(c.referenced_entity)
                return f"{name_part}FOREIGN KEY ({', '.join(local_cols)}) REFERENCES {ref_table} ({', '.join(ref_cols)})"
        return None

    # ── CREATE INDEX ────────────────────────────────────────────
    def _build_create_index(self, idx: Index, table_name: str) -> str:
        unique = "UNIQUE " if idx.unique else ""
        name = self._quote(idx.name or f"idx_{table_name}_{'_'.join(idx.attributes)}")
        cols = ", ".join(self._quote(c) for c in idx.attributes)
        return f"CREATE {unique}INDEX {name} ON {self._quote(table_name)} ({cols})"

    # ── DataType conversion ─────────────────────────────────────
    def _datatype_to_sql(self, dt: DataType) -> str:
        base = dt.base
        if base in _SCALAR_TO_SQL:
            sql = _SCALAR_TO_SQL[base]
        else:
            sql = "TEXT"

        # Add precision/scale for DECIMAL
        if base == ScalarType.DECIMAL:
            p = dt.precision or 10
            s = dt.scale or 0
            sql = f"DECIMAL({p},{s})"
        # For ARRAY, MAP, STRUCT we can't map directly; fallback to TEXT
        if base == ScalarType.ARRAY:
            sql = "TEXT"
        elif base == ScalarType.MAP:
            sql = "TEXT"
        elif base == ScalarType.STRUCT:
            sql = "TEXT"
        return sql

    # ── Helpers ──────────────────────────────────────────────────
    def _normalize_columns(self, expr: Optional[str]) -> List[str]:
        """Normalize a comma‑separated list of column names."""
        if not expr:
            return []
        return [self._quote(c.strip()) for c in expr.split(",") if c.strip()]

    def _get_annotation(self, obj, key: str) -> Optional[str]:
        if isinstance(obj, Entity):
            return next((a.value for a in obj.annotations if a.key == key), None)
        if isinstance(obj, Attribute):
            return next((a.value for a in obj.annotations if a.key == key), None)
        return None

    @staticmethod
    def _quote(name: str) -> str:
        """Double‑quote an SQL identifier."""
        escaped = name.replace('"', '""')
        return f'"{escaped}"'
    


    async def apply_to_database(self, document: MSDMDocument, connection: ConnectionConfig = None):
        if connection is None:
            raise ValueError("ConnectionConfig required for database target")

        engine = _build_sqlalchemy_engine(connection)
        try:
            with engine.begin() as conn:
                await self._execute_migration(conn, document)
        finally:
            engine.dispose()

    async def _execute_migration(self, conn: Connection, document: MSDMDocument):
        inspector = inspect(conn.engine)
        existing_tables = set(inspector.get_table_names())
        model_tables = {e.name for e in document.entities if e.kind == EntityKind.TABLE}

        # Tables to drop (soft delete via rename or actual DROP)
        to_drop = existing_tables - model_tables
        for table in to_drop:
            await self._remove_table(conn, table)

        # Process each model entity
        for entity in document.entities:
            if entity.kind == EntityKind.TABLE:
                if entity.name in existing_tables:
                    await self._sync_table(conn, inspector, entity)
                else:
                    await conn.execute(text(self._build_create_table(entity)))
            elif entity.kind == EntityKind.VIEW:
                # Views are handled as raw DDL; either recreate or skip
                ddl = next((a.value for a in entity.annotations if a.key == "view_definition"), None)
                if ddl:
                    await conn.execute(text(ddl))

        # Indexes (create if not exist, drop if removed? We'll just create missing ones)
        await self._sync_indexes(conn, inspector, document)

        # Raw DDL annotations (kept for round‑trip)
        for ann in document.annotations:
            if ann.key == "raw_ddl":
                await conn.execute(text(ann.value))

    async def _sync_table(self, conn: Connection, inspector, entity: Entity):
        """Alter an existing table to match the model."""
        table_name = entity.name
        existing_cols = {col["name"]: col for col in inspector.get_columns(table_name)}
        model_cols = {attr.name: attr for attr in entity.attributes}

        # Add missing columns
        for name, attr in model_cols.items():
            if name not in existing_cols:
                col_def = self._column_definition_sql(attr)
                await conn.execute(text(f"ALTER TABLE {self._quote(table_name)} ADD COLUMN {col_def}"))

        # Drop/rename columns present in DB but not in model
        for name in existing_cols.keys() - model_cols.keys():
            await self._remove_column(conn, table_name, name)

        # Modify column types? Not safe; we skip.
        # Constraints: we can't easily diff inline constraints; we'll rely on table‑level constraint recreation.
        # Drop all existing FK / unique / check constraints and recreate from model.
        await self._recreate_constraints(conn, table_name, entity)

    async def _remove_table(self, conn: Connection, table_name: str):
        """Apply soft‑delete strategy to a table."""
        if self.soft_delete_strategy == SoftDeleteStrategy.NONE:
            await conn.execute(text(f"DROP TABLE IF EXISTS {self._quote(table_name)}"))
        elif self.soft_delete_strategy == SoftDeleteStrategy.PREFIX:
            new_name = f"_deleted_{table_name}"
            await conn.execute(text(f"ALTER TABLE {self._quote(table_name)} RENAME TO {self._quote(new_name)}"))
        elif self.soft_delete_strategy == SoftDeleteStrategy.SUFFIX:
            new_name = f"{table_name}_deleted"
            await conn.execute(text(f"ALTER TABLE {self._quote(table_name)} RENAME TO {self._quote(new_name)}"))
        # ANNOTATE: cannot represent in DB; leave as is (but we might add a comment)
        # We'll store a comment annotation if possible.
        if self.soft_delete_strategy == SoftDeleteStrategy.ANNOTATE:
            await conn.execute(text(f"COMMENT ON TABLE {self._quote(table_name)} IS 'deprecated'"))

    async def _remove_column(self, conn: Connection, table_name: str, col_name: str):
        """Soft‑delete a column."""
        if self.soft_delete_strategy == SoftDeleteStrategy.NONE:
            await conn.execute(text(f"ALTER TABLE {self._quote(table_name)} DROP COLUMN IF EXISTS {self._quote(col_name)}"))
        elif self.soft_delete_strategy == SoftDeleteStrategy.PREFIX:
            new_name = f"_deleted_{col_name}"
            await conn.execute(text(f"ALTER TABLE {self._quote(table_name)} RENAME COLUMN {self._quote(col_name)} TO {self._quote(new_name)}"))
        elif self.soft_delete_strategy == SoftDeleteStrategy.SUFFIX:
            new_name = f"{col_name}_deleted"
            await conn.execute(text(f"ALTER TABLE {self._quote(table_name)} RENAME COLUMN {self._quote(col_name)} TO {self._quote(new_name)}"))
        # ANNOTATE: we'd need to store a comment; not standard.

    async def _recreate_constraints(self, conn: Connection, table_name: str, entity: Entity):
        """Drop and recreate all table‑level constraints."""
        # Drop existing FK constraints on this table
        inspector = inspect(conn.engine)
        for fk in inspector.get_foreign_keys(table_name):
            await conn.execute(text(f"ALTER TABLE {self._quote(table_name)} DROP CONSTRAINT {self._quote(fk['name'])}"))
        # Unique and check constraints – we drop by name if we can retrieve them; not always portable.
        # We'll recreate from model.
        for c in entity.constraints:
            sql = self._constraint_to_sql(c, table_name)
            if sql:
                await conn.execute(text(f"ALTER TABLE {self._quote(table_name)} ADD {sql}"))

    async def _sync_indexes(self, conn: Connection, inspector, document: MSDMDocument):
        """Create missing indexes; drop those not in model."""
        # We'll only create missing; dropping could be destructive, but we honor soft‑delete?
        for entity in document.entities:
            if entity.kind != EntityKind.TABLE:
                continue
            table_name = entity.name
            existing_idx = inspector.get_indexes(table_name)
            existing_idx_names = {idx["name"] for idx in existing_idx if idx.get("name")}
            for idx_def in entity.indexes:
                if idx_def.name not in existing_idx_names:
                    unique = "UNIQUE " if idx_def.unique else ""
                    cols = ", ".join(self._quote(c) for c in idx_def.attributes)
                    sql = f"CREATE {unique}INDEX {self._quote(idx_def.name)} ON {self._quote(table_name)} ({cols})"
                    await conn.execute(text(sql))

    @staticmethod
    def _column_definition_sql(attr: Attribute) -> str:
        """Return column definition SQL fragment (name type constraints)."""
        name = SqlDDLWriter._quote(attr.name)
        type_str = SqlDDLWriter._datatype_to_sql(attr.data_type)
        parts = [f"{name} {type_str}"]
        for c in attr.constraints:
            if c.type == ConstraintType.NOT_NULL:
                parts.append("NOT NULL")
            elif c.type == ConstraintType.PRIMARY_KEY:
                parts.append("PRIMARY KEY")
            elif c.type == ConstraintType.UNIQUE:
                parts.append("UNIQUE")
            elif c.type == ConstraintType.CHECK and c.expression:
                parts.append(f"CHECK ({c.expression})")
            elif c.type == ConstraintType.DEFAULT and c.expression:
                parts.append(f"DEFAULT {c.expression}")
        return " ".join(parts)
    