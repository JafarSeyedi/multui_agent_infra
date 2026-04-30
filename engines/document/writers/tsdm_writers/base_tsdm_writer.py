# engines/document/writers/tsdm_writers/base_tsdm_writer.py
from abc import abstractmethod
from ..base import BaseDocumentWriter, WriteOptions
from ...models.tsdm_models import TSDMDocument

class BaseTSDMWriter(BaseDocumentWriter):
    name = "tsdm"
    supported_extensions = (".tsdm.json", ".tools.json")

    @abstractmethod
    async def _write_design(self, document: TSDMDocument) -> bytes:
        ...