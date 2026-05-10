# engines/document/writers/dsdm_writers/cbor_writer.py
"""CBOR writer."""
import cbor2
from ...parsers.dsdm_parsers.dsdm_utils import node_to_python
from ...models.dsdm_models import DataNode
from .base_dsdm_writer import BaseDSDMWriter, DSDMWriteOptions

class CBORWriter(BaseDSDMWriter):
    name = "cbor"
    supported_extensions = (".cbor",)
    media_type_str = "application/cbor"

    def get_supported_media_types(self) -> list[str]:
        return [self.media_type_str]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    async def _serialise_root(self, root_node: DataNode, options: DSDMWriteOptions) -> bytes:
        py_obj = node_to_python(root_node)
        return cbor2.dumps(py_obj)

    async def _serialise_node(self, node: DataNode, options: DSDMWriteOptions) -> bytes:
        return await self._serialise_root(node, options)