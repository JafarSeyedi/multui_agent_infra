# engines/document/writers/dsdm_writers/base_dsdm_writer.py
"""
Base writer for DSDM formats. Accepts BaseDocument, casts to DataDocument internally.
Schema‑driven field ordering and validation are shared.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, Optional, cast

from ...models.base import BaseDocument
from ...models.dsdm_models import DataDocument, DataNode
from ...models.msdm_models import MSDMDocument
from ..base import BaseDocumentWriter, WriteOptions


class DSDMWriteOptions(WriteOptions):
    """Extended write options for DSDM writers."""
    msdm_schema: MSDMDocument | None = None   # renamed
    strip_extra_fields: bool = False
    require_all_required: bool = True
    unsafe_operations_allowed: bool = False      # added


class BaseDSDMWriter(BaseDocumentWriter):
    def __init__(self, options: DSDMWriteOptions | None = None):
        super().__init__(options=options or DSDMWriteOptions())

    # Override write methods to accept BaseDocument, then cast/assert DataDocument
    async def write(self, document: BaseDocument) -> bytes:
        if not isinstance(document, DataDocument):
            raise TypeError(f"Expected DataDocument, got {type(document)}")
        doc = cast(DataDocument, document)
        opts = self._writer_options(doc)
        return await self._serialise_root(doc.root, opts)

    async def write_stream(self, document: BaseDocument) -> AsyncIterator[bytes]:
        if not isinstance(document, DataDocument):
            raise TypeError(f"Expected DataDocument, got {type(document)}")
        doc = cast(DataDocument, document)
        data = await self.write(doc)
        yield data

    async def write_to_file(
        self,
        document: BaseDocument,
        target: Path,
        options: dict[str, Any] | None = None,
    ) -> None:
        if not isinstance(document, DataDocument):
            raise TypeError(f"Expected DataDocument, got {type(document)}")
        doc = cast(DataDocument, document)
        opts = self._writer_options(doc)
        if options:
            opts = opts.copy(update=options)
        raw = await self._serialise_root(doc.root, opts)
        target.write_bytes(raw)

    @abstractmethod
    async def _serialise_root(self, root_node: DataNode, options: DSDMWriteOptions) -> bytes:
        ...

    @abstractmethod
    async def _serialise_node(self, node: DataNode, options: DSDMWriteOptions) -> bytes:
        ...

    def _writer_options(self, document: DataDocument) -> DSDMWriteOptions:
        opts = DSDMWriteOptions(**(self.options.model_dump() if self.options else {}))
        if opts.msdm_schema is None and document.schema_ref and document.schema_ref.data_struct:
            opts.msdm_schema = document.schema_ref.data_struct
        return opts

    # Schema helpers unchanged but now use msdm_schema
    def _get_attribute_order(self, node: DataNode, options: DSDMWriteOptions) -> list[str] | None:
        if options.msdm_schema is None:
            return None
        binding = node.schema_binding
        if binding and binding.entity:
            return [attr.name for attr in binding.entity.attributes]
        return None

    def _should_include_field(self, field_name: str, node: DataNode, options: DSDMWriteOptions) -> bool:
        if not options.strip_extra_fields or options.msdm_schema is None:
            return True
        binding = node.schema_binding
        if binding and binding.entity:
            return field_name in {attr.name for attr in binding.entity.attributes}
        return True

    def _check_required_fields(self, node: DataNode, options: DSDMWriteOptions) -> None:
        if not options.require_all_required or options.msdm_schema is None:
            return
        binding = node.schema_binding
        if binding and binding.entity:
            required_names = {attr.name for attr in binding.entity.attributes if attr.required}
            present_names = {child.name for child in node.children}
            missing = required_names - present_names
            if missing:
                raise ValueError(f"Required fields missing in '{node.name}': {', '.join(missing)}")