from typing import Any

from engines.document.models.ksdm_models import KSDMMetricsDocument
from engines.document.models.ksdm_models import KsdDocument
from engines.document.parsers.base import BaseDocumentParser
from engines.document.writers.base import BaseDocumentWriter, WriteResult


class KnowledgeMemoryEngine:
    def __init__(self) -> None:
        self._parsers: dict[str, BaseDocumentParser] = {}
        self._writers: dict[str, BaseDocumentWriter] = {}

    async def parse(self, source: str, fmt: str | None = None, **options: Any) -> KSDMMetricsDocument | KsdDocument:
        raise NotImplementedError

    async def write(self, document: KSDMMetricsDocument | KsdDocument, destination: str, fmt: str | None = None, **options: Any) -> WriteResult:
        raise NotImplementedError

    def register_parser(self, fmt: str, parser: BaseDocumentParser) -> None:
        self._parsers[fmt] = parser

    def register_writer(self, fmt: str, writer: BaseDocumentWriter) -> None:
        self._writers[fmt] = writer
