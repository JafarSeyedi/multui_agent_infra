# engines/document/writers/dsdm_writers/yaml_writer.py
"""YAML writer."""
import yaml
from ...parsers.dsdm_parsers.dsdm_utils import node_to_python
from ...models.dsdm_models import DataNode
from .base_dsdm_writer import BaseDSDMWriter, DSDMWriteOptions

class YAMLWriter(BaseDSDMWriter):
    name = "yaml"
    supported_extensions = (".yaml", ".yml")
    media_type_str = "application/x-yaml"

    def get_supported_media_types(self) -> list[str]:
        return [self.media_type_str]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    async def _serialise_root(self, root_node: DataNode, options: DSDMWriteOptions) -> bytes:
        py_obj = node_to_python(root_node)
        return yaml.dump(py_obj, allow_unicode=True).encode(options.encoding)

    async def _serialise_node(self, node: DataNode, options: DSDMWriteOptions) -> bytes:
        return await self._serialise_root(node, options)