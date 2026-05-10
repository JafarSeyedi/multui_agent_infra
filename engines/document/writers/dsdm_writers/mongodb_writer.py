# engines/document/writers/dsdm_writers/mongodb_writer.py
"""MongoDB writer (file output and live collection insertion)."""
from __future__ import annotations

from typing import Any
from motor.motor_asyncio import AsyncIOMotorCollection  # type: ignore[import-not-found]

from ...models.dsdm_models import DataDocument, DataNode, DataNodeKind, DataValue
from ...models.msdm_models import Entity, ScalarType
from .base_dsdm_writer import BaseDSDMWriter, DSDMWriteOptions
from .bson_writer import BSONWriter


class MongoDBWriter(BaseDSDMWriter):
    name = "mongodb"

    def get_supported_media_types(self) -> list[str]:
        return ["application/bson"]

    def get_supported_extensions(self) -> list[str]:
        return [".bson"]

    async def _serialise_root(self, root_node: DataNode, options: DSDMWriteOptions) -> bytes:
        writer = BSONWriter()
        return await writer._serialise_root(root_node, options)

    async def _serialise_node(self, node: DataNode, options: DSDMWriteOptions) -> bytes:
        return await self._serialise_root(node, options)

    async def write_to_collection(
        self,
        doc: DataDocument,
        collection: AsyncIOMotorCollection,
        options: DSDMWriteOptions,
        entity: Entity | None = None,
    ) -> None:
        entity = entity or (options.msdm_schema.entities[0] if options.msdm_schema and options.msdm_schema.entities else None)
        documents = self._convert_to_mongo_documents(doc.root, entity)
        if documents:
            await collection.insert_many(documents)

    def _convert_to_mongo_documents(self, root: DataNode, entity: Entity | None) -> list[dict[str, Any]]:
        if root.kind != DataNodeKind.ARRAY:
            raise ValueError("Root must be an ARRAY of documents")
        docs = []
        for obj_node in root.children:
            doc: dict[str, Any] = {}
            for child in obj_node.children:
                if child.name is None:
                    continue
                if child.value:
                    val = self._dsdm_to_mongo_value(child.value)
                else:
                    val = None
                doc[child.name] = val
            docs.append(doc)
        return docs

    def _dsdm_to_mongo_value(self, dv: DataValue) -> Any:
        if dv is None:
            return None
        st = dv.scalar_type
        val = dv.value
        # We rely on the driver to serialize Python types correctly; no bson specific conversions needed
        return val