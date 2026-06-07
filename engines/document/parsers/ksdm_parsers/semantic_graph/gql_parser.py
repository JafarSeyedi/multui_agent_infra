from pathlib import Path
from typing import Any, BinaryIO, TextIO

from engines.document.parsers.base import BaseKnowledgeParser, KnowledgeParseError, ParseResult
from engines.document.models.media_types import MEDIA_TYPES


class GqlParser(BaseKnowledgeParser):
    supported_format = MEDIA_TYPES["gql_query"]

    def can_parse(self, source: str | Path) -> bool:
        if isinstance(source, str) and source.endswith('.gql'):
            return True
        try:
            if Path(source).exists():
                data = Path(source).read_bytes()
                text = data.decode('utf-8', errors='ignore') if isinstance(data, bytes) else data
                return 'nodeType' in text or 'edgeType' in text or 'CREATE' in text or 'property' in text
        except Exception:
            pass
        return False

    def parse(self, source: str | Path | BinaryIO | TextIO, **options: Any) -> ParseResult:
        raise KnowledgeParseError("GQL (ISO/IEC 39075) parsing is not yet fully implemented. The standard was published in 2024 and parser support is in development.")
