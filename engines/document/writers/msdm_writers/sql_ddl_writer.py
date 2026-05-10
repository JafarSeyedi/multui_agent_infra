"""
SQL DDL Writer – converts an MSDMDocument into a SQL DDL script (.sql).
Supports CREATE TABLE with all columns, constraints (PRIMARY KEY, UNIQUE,
CHECK, FOREIGN KEY), indexes, and CREATE VIEW statements.
"""
from __future__ import annotations

import warnings
from typing import Optional, List

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncConnection, AsyncEngine

from ...models.msdm_models import Attribute, Constraint, ConstraintType, DataType, Entity
from ...models.msdm_models import EntityKind, Index, MSDMDocument, ScalarType
from ..base import WriteOptions
from .base_msdm_writer import BaseMSDMWriter, ConnectionConfig, SoftDeleteStrategy, WriteTarget


_SCALAR_TO_SQL: dict[ScalarType, str] = {
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
    name = "sql_ddl"
    supported_extensions = (".sql", ".ddl")

    def __init__(
        self,
        options: WriteOptions | None = None,
        target_mode: WriteTarget = WriteTarget.DESIGN_FILE,
        soft_delete_strategy: SoftDeleteStrategy = SoftDeleteStrategy.NONE,
    ):
        super().__init__(options, target_mode, soft_delete_strategy)

    async def _write_design(self, document: MSDMDocument) -> bytes:
        lines: list[str] = []

        tables = [e for e in document.entities if e.kind == EntityKind.TABLE]
        views = [e for e in document.entities if e.kind == EntityKind.VIEW]

        for entity in tables:
            lines.append(self._build_create_table(entity))
            lines.append("")

        for entity in tables:
            for idx in entity.indexes:
                lines.append(self._build_create_index(idx, entity.name))

        for entity in views:
            # Retrieve view definition from annotations if available
            if hasattr(entity, "annotations"):
                ddl = next((a.value for a in entity.annotations if a.key == "view_definition"), None)
                if ddl:
                    lines.append(ddl)
                else:
                    lines.append(f"CREATE VIEW {self._quote(entity.name)} AS SELECT * FROM ...")
            else:
                lines.append(f"CREATE VIEW {self._quote(entity.name)} AS SELECT * FROM ...")
            lines.append("")

        # Raw DDL stored in document annotations
        if hasattr(document, "annotations"):
            for ann in document.annotations:
                if ann.key == "raw_ddl":
                    lines.append(ann.value)

        script = ";\n\n".join(line for line in lines if line) + ";\n"
        encoding = self.options.encoding if self.options else "utf-8"
        return script.encode(encoding or "utf-8")

    def get_supported_media_types(self) -> list[str]:
        return ["text/plain"]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)
    
    # ------------------------------------------------------------------
    # DDL generation
    # ------------------------------------------------------------------
    def _build_create_table(self, entity: Entity) -> str:
        table_name = self._quote(entity.name)
        columns = [self._column_definition(attr) for attr in entity.attributes]
        constraints = [self._constraint_to_sql(c, table_name) for c in entity.constraints if self._constraint_to_sql(c, table_name)]
        all_parts = [p for p in columns + constraints if p is not None]
        body = ",\n  ".join(all_parts)
        return f"CREATE TABLE {table_name} (\n  {body}\n)"

    def _column_definition(self, attr: Attribute) -> str:
        name = self._quote(attr.name)
        type_str = self._datatype_to_sql(attr.data_type)
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
        if hasattr(attr, "annotations") and any(a.key == "auto_increment" for a in attr.annotations):
            parts.append("AUTO_INCREMENT")
        return " ".join(parts)

    def _constraint_to_sql(self, c: Constraint, table_name: str) -> str | None:
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
            if c.ref_entity and c.ref_attr_ids:
                ref_cols = [self._quote(col) for col in c.ref_attr_ids]
                ref_table = self._quote(c.ref_entity.name)
                return f"{name_part}FOREIGN KEY ({', '.join(local_cols)}) REFERENCES {ref_table} ({', '.join(ref_cols)})"
        return None

    def _build_create_index(self, idx: Index, table_name: str) -> str:
        unique = "UNIQUE " if idx.unique else ""
        name = self._quote(idx.name or f"idx_{table_name}_{'_'.join([attr.name for attr in idx.attributes])}")
        cols = ", ".join(self._quote(c.name) for c in idx.attributes)
        return f"CREATE {unique}INDEX {name} ON {self._quote(table_name)} ({cols})"

    @staticmethod
    def _datatype_to_sql(dt: DataType) -> str:
        base = dt.base
        if base in _SCALAR_TO_SQL:
            sql = _SCALAR_TO_SQL[base]
        else:
            sql = "TEXT"
        if base == ScalarType.DECIMAL:
            p = dt.precision or 10
            s = dt.scale or 0
            sql = f"DECIMAL({p},{s})"
        elif base in (ScalarType.ARRAY, ScalarType.MAP, ScalarType.STRUCT):
            sql = "TEXT"
        return sql

    def _normalize_columns(self, expr: str | None) -> list[str]:
        if not expr:
            return []
        return [self._quote(c.strip()) for c in expr.split(",") if c.strip()]

    @staticmethod
    def _quote(name: str | None) -> str:
        if name is None:
            return '""'
        escaped = name.replace('"', '""')
        return f'"{escaped}"'    

    # ------------------------------------------------------------------
    # Database application (async)
    # ------------------------------------------------------------------
    async def apply_to_database(
        self, document: MSDMDocument, connection: Optional[ConnectionConfig] = None
    ) -> None:
        if connection is None:
            raise ValueError("ConnectionConfig required for database target")
        engine = await self._build_sqlalchemy_engine(connection)
        try:
            async with engine.begin() as conn:
                await self._execute_migration(conn, document)
        finally:
            await engine.dispose()

    @staticmethod
    async def _build_sqlalchemy_engine(config: ConnectionConfig) -> AsyncEngine:
        dialect = getattr(config, "dialect", None)
        if dialect == "postgresql":
            url = f"postgresql+asyncpg://{config.username}:{config.password}@{config.host}:{config.port}/{config.database}"
        elif dialect == "mysql":
            url = f"mysql+aiomysql://{config.username}:{config.password}@{config.host}:{config.port}/{config.database}"
        else:
            # Default to SQLite async
            url = "sqlite+aiosqlite:///./temp.db"
        return create_async_engine(url, echo=False)

    async def _execute_migration(self, conn: AsyncConnection, document: MSDMDocument):
        def _sync_inspect(sync_conn):
            return inspect(sync_conn)

        inspector = await conn.run_sync(_sync_inspect)
        existing_tables = set(inspector.get_table_names())
        model_tables = {e.name for e in document.entities if e.kind == EntityKind.TABLE}

        for table in existing_tables - model_tables:
            await self._remove_table(conn, table)

        for entity in document.entities:
            if entity.kind == EntityKind.TABLE:
                if entity.name in existing_tables:
                    await self._sync_table(conn, inspector, entity)
                else:
                    await conn.execute(text(self._build_create_table(entity)))
            elif entity.kind == EntityKind.VIEW:
                ddl = None
                if hasattr(entity, "annotations"):
                    ddl = next((a.value for a in entity.annotations if a.key == "view_definition"), None)
                if ddl:
                    await conn.execute(text(ddl))
                else:
                    await conn.execute(text(f"CREATE OR REPLACE VIEW {self._quote(entity.name)} AS SELECT * FROM ..."))

        await self._sync_indexes(conn, inspector, document)

    async def _sync_table(self, conn: AsyncConnection, inspector, entity: Entity):
        table_name = entity.name
        existing_cols = {col["name"]: col for col in inspector.get_columns(table_name)}
        model_cols = {attr.name: attr for attr in entity.attributes}

        for name, attr in model_cols.items():
            if name not in existing_cols:
                col_def = self._column_definition_sql(attr)
                await conn.execute(text(f"ALTER TABLE {self._quote(table_name)} ADD COLUMN {col_def}"))

        for name in existing_cols.keys() - model_cols.keys():
            await self._remove_column(conn, table_name, name)

        await self._recreate_constraints(conn, table_name, entity)

    async def _remove_table(self, conn: AsyncConnection, table_name: str):
        if self.soft_delete_strategy == SoftDeleteStrategy.NONE:
            await conn.execute(text(f"DROP TABLE IF EXISTS {self._quote(table_name)}"))
        elif self.soft_delete_strategy == SoftDeleteStrategy.PREFIX:
            new_name = f"_deleted_{table_name}"
            await conn.execute(text(f"ALTER TABLE {self._quote(table_name)} RENAME TO {self._quote(new_name)}"))
        elif self.soft_delete_strategy == SoftDeleteStrategy.SUFFIX:
            new_name = f"{table_name}_deleted"
            await conn.execute(text(f"ALTER TABLE {self._quote(table_name)} RENAME TO {self._quote(new_name)}"))
        elif self.soft_delete_strategy == SoftDeleteStrategy.ANNOTATE:
            # PostgreSQL specific
            try:
                await conn.execute(text(f"COMMENT ON TABLE {self._quote(table_name)} IS 'deprecated'"))
            except Exception:
                warnings.warn(f"ANNOTATE soft-delete not supported on this database; table {table_name} was not removed")

    async def _remove_column(self, conn: AsyncConnection, table_name: str, col_name: str):
        if self.soft_delete_strategy == SoftDeleteStrategy.NONE:
            await conn.execute(text(f"ALTER TABLE {self._quote(table_name)} DROP COLUMN IF EXISTS {self._quote(col_name)}"))
        elif self.soft_delete_strategy == SoftDeleteStrategy.PREFIX:
            new_name = f"_deleted_{col_name}"
            await conn.execute(text(f"ALTER TABLE {self._quote(table_name)} RENAME COLUMN {self._quote(col_name)} TO {self._quote(new_name)}"))
        elif self.soft_delete_strategy == SoftDeleteStrategy.SUFFIX:
            new_name = f"{col_name}_deleted"
            await conn.execute(text(f"ALTER TABLE {self._quote(table_name)} RENAME COLUMN {self._quote(col_name)} TO {self._quote(new_name)}"))

    async def _recreate_constraints(self, conn: AsyncConnection, table_name: str, entity: Entity):
        def _get_fks(sync_conn):
            return inspect(sync_conn).get_foreign_keys(table_name)

        fks = await conn.run_sync(_get_fks)
        for fk in fks:
            await conn.execute(text(f"ALTER TABLE {self._quote(table_name)} DROP CONSTRAINT {self._quote(fk['name'])}"))
        for c in entity.constraints:
            sql = self._constraint_to_sql(c, table_name)
            if sql:
                await conn.execute(text(f"ALTER TABLE {self._quote(table_name)} ADD {sql}"))

    async def _sync_indexes(self, conn: AsyncConnection, inspector, document: MSDMDocument):
        for entity in document.entities:
            if entity.kind != EntityKind.TABLE:
                continue
            table_name = entity.name
            existing_idx = inspector.get_indexes(table_name)
            existing_idx_names = {idx["name"] for idx in existing_idx if idx.get("name")}
            for idx_def in entity.indexes:
                if idx_def.name not in existing_idx_names:
                    unique = "UNIQUE " if idx_def.unique else ""
                    cols = ", ".join(self._quote(c.name) for c in idx_def.attributes)
                    sql = f"CREATE {unique}INDEX {self._quote(idx_def.name)} ON {self._quote(table_name)} ({cols})"
                    await conn.execute(text(sql))

    @staticmethod
    def _column_definition_sql(attr: Attribute) -> str:
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