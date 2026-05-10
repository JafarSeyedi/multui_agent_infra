# engines/document/parsers/dsdm_parsers/xml_parser.py
import xml.etree.ElementTree as ET
from io import BytesIO
from .base_dsdm_parser import BaseDSDMParser, DSDMParseOptions
from .dsdm_utils import scalar_value
from ...models.dsdm_models import DataNode, DataNodeKind

class XMLParser(BaseDSDMParser):
    name = "xml"
    supported_extensions = (".xml",)

    async def _parse_to_datanode(self, raw_bytes: bytes, options: DSDMParseOptions) -> DataNode:
        tree = ET.parse(BytesIO(raw_bytes))
        return self._elem_to_datanode(tree.getroot(), path="$")

    def _elem_to_datanode(self, elem: ET.Element, path: str) -> DataNode:
        tag = elem.tag
        ns = None
        if '}' in tag:
            ns, localname = tag[1:].split('}', 1)
            name = localname
        else:
            name = tag
        node = DataNode(node_id=f"node:{path}", kind=DataNodeKind.XML_ELEMENT,
                        path=path, name=name, namespace=ns)
        for attr_name, attr_value in elem.attrib.items():
            attr_ns = None
            attr_local = attr_name
            if '}' in attr_name:
                attr_ns, attr_local = attr_name[1:].split('}', 1)
            attr_path = f"{path}@{attr_local}"
            node.attributes.append(DataNode(
                node_id=f"node:{attr_path}",
                kind=DataNodeKind.XML_ATTRIBUTE,
                path=attr_path, name=attr_local, namespace=attr_ns,
                value=scalar_value(attr_value),
            ))
        if elem.text and elem.text.strip():
            text_path = f"{path}#text"
            node.children.append(DataNode(
                node_id=f"node:{text_path}", kind=DataNodeKind.XML_TEXT,
                path=text_path, name="#text", value=scalar_value(elem.text),
            ))
        for child_elem in elem:
            child_path = f"{path}.{name}" if path != "$" else f"$.{name}"
            node.children.append(self._elem_to_datanode(child_elem, child_path))
        return node

    def _detect_media_type(self, source_name: str) -> str:
        return "application/xml"