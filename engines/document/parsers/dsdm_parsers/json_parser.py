# engines/document/parsers/dsdm_parsers/json_parser.py
import json
from .base_dsdm_parser import BaseDSDMParser, DSDMParseOptions
from .dsdm_utils import build_node_from_python
from ...models.dsdm_models import DataNode, DataDocument, DataNodeKind
from typing import Any

class JSONParser(BaseDSDMParser):
    name = "json"
    supported_extensions = (".json",)

    async def _parse_to_datanode(self, raw_bytes: bytes, options: DSDMParseOptions) -> DataNode:
        data = json.loads(raw_bytes.decode(options.encoding))
        # Schema binding will be done by base after this call
        return build_node_from_python(data, path="$")

    def _detect_media_type(self, source_name: str) -> str:
        return "application/json"