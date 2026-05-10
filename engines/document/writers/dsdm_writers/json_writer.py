# engines/document/writers/dsdm_writers/json_writer.py
"""JSON writer."""
from ...parsers.dsdm_parsers.dsdm_utils import node_to_python
from ...models.dsdm_models import DataNode
from .base_dsdm_writer import BaseDSDMWriter, DSDMWriteOptions
import json

class JSONWriter(BaseDSDMWriter):
    name = "json"
    supported_extensions = (".json",)
    media_type_str = "application/json"

    def get_supported_media_types(self) -> list[str]:
        return [self.media_type_str]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    async def _serialise_root(self, root_node: DataNode, options: DSDMWriteOptions) -> bytes:
        py_obj = node_to_python(root_node)
        indent = 2 if options.pretty_print else None
        return json.dumps(py_obj, indent=indent, ensure_ascii=False).encode(options.encoding)

    async def _serialise_node(self, node: DataNode, options: DSDMWriteOptions) -> bytes:
        return await self._serialise_root(node, options)