# engines/document/writers/dsdm_writers/cassandra_writer.py
"""Cassandra writer."""
from ...models.dsdm_models import DataDocument, DataNode, DataNodeKind
from ...models.msdm_models import Entity
from .base_dsdm_writer import BaseDSDMWriter, DSDMWriteOptions


class CassandraWriter(BaseDSDMWriter):
    name = "cassandra"

    def get_supported_media_types(self) -> list[str]:
        return []

    def get_supported_extensions(self) -> list[str]:
        return []

    async def _serialise_root(self, root_node: DataNode, options: DSDMWriteOptions) -> bytes:
        raise RuntimeError("Cassandra writer does not support file output. Use write_to_cassandra.")

    async def _serialise_node(self, node: DataNode, options: DSDMWriteOptions) -> bytes:
        raise RuntimeError("Cassandra writer does not support node output.")

    async def write_to_cassandra(
        self,
        doc: DataDocument,
        session,
        keyspace: str,
        entity: Entity | None = None,
        options: DSDMWriteOptions | None = None,
    ) -> None:
        entity = entity or (options.msdm_schema.entities[0] if options and options.msdm_schema and options.msdm_schema.entities else None)
        if not entity:
            raise ValueError("Entity is required for Cassandra write")
        table = entity.name
        columns = [attr.name for attr in entity.attributes]
        col_spec = ", ".join(columns)
        placeholders = ", ".join(["%s"] * len(columns))
        query = f"INSERT INTO {keyspace}.{table} ({col_spec}) VALUES ({placeholders})"

        prepared = await session.prepare(query)

        if doc.root.kind != DataNodeKind.ARRAY:
            raise ValueError("Cassandra writer expects root ARRAY of rows")
        for obj_node in doc.root.children:
            row = []
            for attr in entity.attributes:
                child = next((c for c in obj_node.children if c.name == attr.name), None)
                val = child.value.value if child and child.value else None
                row.append(val)
            await session.execute(prepared, row)