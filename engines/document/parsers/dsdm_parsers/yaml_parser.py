# engines/document/parsers/dsdm_parsers/yaml_parser.py
import yaml
from .base_dsdm_parser import BaseDSDMParser, DSDMParseOptions
from .dsdm_utils import build_node_from_python
from ...models.dsdm_models import DataNode

class YAMLParser(BaseDSDMParser):
    name = "yaml"
    supported_extensions = (".yaml", ".yml")

    async def _parse_to_datanode(self, raw_bytes: bytes, options: DSDMParseOptions) -> DataNode:
        data = yaml.safe_load(raw_bytes.decode(options.encoding))
        return build_node_from_python(data, path="$")

    def _detect_media_type(self, source_name: str) -> str:
        return "application/x-yaml"