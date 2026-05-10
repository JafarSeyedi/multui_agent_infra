# engines/document/writers/dsdm_writers/sql_writer.py
"""SQL writer with connection management and UPSERT generation."""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable, Optional, Sequence, cast

from ...models.dsdm_models import DataDocument, DataNode, DataNodeKind, DataValue
from ...models.msdm_models import Entity, Attribute, ScalarType
from .base_dsdm_writer import BaseDSDMWriter, DSDMWriteOptions


@runtime_checkable
class AsyncSQLConnection(Protocol):
    async def execute(self, query: str, params: tuple | None = None) -> None:
        ...
    async def executemany(self, query: str, params_list: Sequence[Sequence[Any]]) -> None:
        ...


class SQLDataWriter(BaseDSDMWriter):
    name = "sql"
    supported_extensions = (".sql",)
    media_type_str = "application/sql"

    def get_supported_media_types(self) -> list[str]:
        return [self.media_type_str]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    async def _serialise_root(self, root_node: DataNode, options: DSDMWriteOptions) -> bytes:
        entity = options.msdm_schema.entities[0] if options.msdm_schema and options.msdm_schema.entities else None
        statements = self._generate_upsert_sql(root_node, entity, options)
        return "\n".join(statements).encode(options.encoding)

    async def _serialise_node(self, node: DataNode, options: DSDMWriteOptions) -> bytes:
        return await self._serialise_root(node, options)

    async def write_to_database(
        self,
        doc: DataDocument,
        connection: AsyncSQLConnection,
        options: DSDMWriteOptions,
        table_name: str | None = None,
        entity: Entity | None = None,
    ) -> None:
        entity = entity or (options.msdm_schema.entities[0] if options.msdm_schema and options.msdm_schema.entities else None)
        if not entity:
            raise ValueError("An MSDM entity is required to build SQL statements")
        table = table_name or entity.name
        rows = self._extract_rows(doc.root, entity)
        if not rows:
            return
        sql = self._build_upsert_sql(table, entity, options)
        col_names = [attr.name for attr in entity.attributes]
        params = [tuple(row.get(col) for col in col_names) for row in rows]
        await connection.executemany(sql, params)

    def _generate_upsert_sql(self, root_node: DataNode, entity: Entity | None, options: DSDMWriteOptions) -> list[str]:
        if not entity:
            raise ValueError("An MSDM entity is required")
        rows = self._extract_rows(root_node, entity)
        if not rows:
            return []
        table = entity.name
        return self._generate_literal_inserts(table, entity, rows)

    def _extract_rows(self, root: DataNode, entity: Entity) -> list[dict]:
        if root.kind != DataNodeKind.ARRAY:
            raise ValueError("Root must be an ARRAY of objects")
        rows = []
        for obj_node in root.children:
            if obj_node.kind != DataNodeKind.OBJECT:
                continue
            row = {}
            for attr in entity.attributes:
                child = next((c for c in obj_node.children if c.name == attr.name), None)
                if child and child.value:
                    row[attr.name] = child.value.value
                else:
                    row[attr.name] = None
            rows.append(row)
        return rows

    def _build_upsert_sql(self, table: str, entity: Entity, options: DSDMWriteOptions) -> str:
        columns = [attr.name for attr in entity.attributes]
        cols_joined = ", ".join(columns)
        placeholders = ", ".join(["%s"] * len(columns))
        conflict_target = options.custom.get("upsert_key", "id") if options.custom else "id"
        updates = ", ".join([f"{col} = EXCLUDED.{col}" for col in columns])
        return f"INSERT INTO {table} ({cols_joined}) VALUES ({placeholders}) ON CONFLICT ({conflict_target}) DO UPDATE SET {updates};"

    def _generate_literal_inserts(self, table: str, entity: Entity, rows: list[dict]) -> list[str]:
        statements = []
        for row in rows:
            values = []
            for attr in entity.attributes:
                val = row.get(attr.name)
                values.append(self._format_sql_value(val, attr))
            stmt = f"INSERT INTO {table} ({', '.join(attr.name for attr in entity.attributes)}) VALUES ({', '.join(values)});"
            statements.append(stmt)
        return statements

    def _format_sql_value(self, val: Any, attr: Attribute) -> str:
        if val is None:
            return "NULL"
        dt = attr.data_type.base
        if dt in (ScalarType.INT, ScalarType.LONG, ScalarType.FLOAT, ScalarType.DOUBLE, ScalarType.DECIMAL):
            return str(val)
        elif dt == ScalarType.BOOLEAN:
            return "TRUE" if val else "FALSE"
        elif dt == ScalarType.BINARY:
            import base64
            if isinstance(val, bytes):
                return f"E'\\\\x{base64.b16encode(val).decode()}'"
            return f"'{val}'"
        else:
            escaped = str(val).replace("'", "''")
            return f"'{escaped}'"