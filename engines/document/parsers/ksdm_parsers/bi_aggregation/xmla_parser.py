import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, BinaryIO, TextIO

from engines.document.parsers.base import BaseDocumentParser, ParseResult
from engines.document.models.media_types import MEDIA_TYPES
from engines.document.models.ksdm_models import (
    BiAggregationDocument,
    BiAggregationKind,
    XmlaDiscoverRequest,
    XmlaDiscoverResponse,
)


class XmlaDiscoverParser(BaseDocumentParser):
    supported_format = MEDIA_TYPES["xmla_discover_xml"]

    def can_parse(self, source: str | Path) -> bool:
        if isinstance(source, Path):
            source = str(source)
        if isinstance(source, str) and source.endswith(('.xmla_discover.xml', '.xmla.xml', '.xml')):
            return True
        try:
            data = Path(source).read_bytes()[:200] if Path(source).exists() else b""
            return b"<DiscoverResponse" in data or b"<Envelope" in data
        except Exception:
            return False

    def parse(self, source: str | Path | BinaryIO | TextIO, **options: Any) -> ParseResult:
        try:
            if isinstance(source, (str, Path)):
                data: bytes = Path(source).read_bytes()
            elif hasattr(source, 'read'):
                _raw = source.read()
                data = _raw.encode('utf-8') if isinstance(_raw, str) else _raw
            else:
                raise Exception("Unsupported source type")
            
            root = ET.fromstring(data)
            
            ns = {
                'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
                'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
                'xsd': 'http://www.w3.org/2001/XMLSchema',
                'rs': 'urn:schemas-microsoft-com:xml-sql',
            }
            
            discover_response = root.find('.//DiscoverResponse', ns)
            if discover_response is None:
                discover_response = root
                
            request_type = ""
            rows = []
            schema_rowset = None
            
            try:
                request_type_elem = discover_response.find('.//RequestType', ns)
                if request_type_elem is not None:
                    request_type = request_type_elem.text or ""
            except Exception:
                pass
                
            try:
                rows_elem = discover_response.findall('.//row', ns)
                for row in rows_elem:
                    row_data = {}
                    for child in row:
                        row_data[child.tag.split('}')[-1] if '}' in child.tag else child.tag] = child.text or ""
                    rows.append(row_data)
            except Exception:
                pass
                
            discover_req = XmlaDiscoverRequest(request_type=request_type)
            discover_resp = XmlaDiscoverResponse(request_type=request_type, rows=rows, schema_rowset=schema_rowset)
            
            doc = BiAggregationDocument(
                title=Path(source).stem if isinstance(source, (str, Path)) else "xmla_document",
                document_id=str(Path(source).stem) if isinstance(source, (str, Path)) else "unknown",
                media_type=MEDIA_TYPES["xmla_discover_xml"],
                bi_aggregation_kind=BiAggregationKind.XMLA_CUBE,
                xmla_discover_request=discover_req,
                xmla_discover_response=discover_resp,
            )
            return ParseResult(document=doc)
        except Exception as e:
            raise Exception(f"XMLA parse failed: {e}")
