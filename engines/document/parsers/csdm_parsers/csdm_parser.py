# engines/document/parsers/csdm_parsers/csdm_parser.py
from __future__ import annotations
import traceback
from pathlib import Path
from ...parsers.base import BaseDocumentParser
from ...models.base import BaseDocument
from ...models.csdm_core import CSDMDocument
from ...models.media_types import MEDIA_TYPES
from .oda_bridge import ODABridge
from .csdm_loader import CSDMLoader
from .csdm_relationships import CSDMRelationshipResolver

class CSDMDocumentParser(BaseDocumentParser):
    FORMAT = ["dwg", "dwf", "dxf", "dcf"]
    NAME = "CSDMParser"
    VERSION = "1.0.0"

    def parse(self, file_path: str) -> BaseDocument:
        try:
            oda = ODABridge()
            dwg = oda.load_file(file_path)
            p = Path(file_path)

            loader = CSDMLoader(dwg, title=p.name, document_id=file_path, media_type=MEDIA_TYPES["dwg"])
            csdm_doc: CSDMDocument = loader.load_all()

            resolver = CSDMRelationshipResolver(csdm_doc)
            resolver.resolve_all()

            csdm_doc.file_extension = p.suffix
            return csdm_doc
        except Exception as e:
            traceback.print_exc()
            raise RuntimeError(f"Failed to parse DWG file: {file_path}\n{e}")
