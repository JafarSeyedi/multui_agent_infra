from typing import Any

from engines.document.models.isdm_models import ISDMDocument
from engines.document.models.ksdm_models import KsdDocument
from engines.document.parsers.base import BaseKnowledgeParser
from engines.document.writers.base import BaseKnowledgeWriter, WriteResult


class KnowledgeMemoryEngine:
    def __init__(self) -> None:
        self._parsers: dict[str, BaseKnowledgeParser] = {}
        self._writers: dict[str, BaseKnowledgeWriter] = {}

    async def parse(self, source: str, fmt: str | None = None, **options: Any) -> ISDMDocument | KsdDocument:
        raise NotImplementedError

    async def write(self, document: ISDMDocument | KsdDocument, destination: str, fmt: str | None = None, **options: Any) -> WriteResult:
        raise NotImplementedError

    def register_parser(self, fmt: str, parser: BaseKnowledgeParser) -> None:
        self._parsers[fmt] = parser

    def register_writer(self, fmt: str, writer: BaseKnowledgeWriter) -> None:
        self._writers[fmt] = writer
