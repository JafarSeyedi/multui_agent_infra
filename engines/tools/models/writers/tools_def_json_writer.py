# engines/document/writers/tsdm_writers/base_tsdm_writer.py
from abc import abstractmethod

from engines.tools.models.tools_def_models import TSDMDocument
from engines.document.writers.base import BaseDocumentWriter

class BaseTSDMWriter(BaseDocumentWriter):
    name = "tsdm"
    supported_extensions = (".tsdm.json", ".tools.json")

    @abstractmethod
    async def _write_design(self, document: TSDMDocument) -> bytes:
        ...
