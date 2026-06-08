import yaml
from pathlib import Path
from typing import Any, BinaryIO, TextIO

from engines.document.parsers.base import BaseDocumentParser, ParseResult
from engines.document.models.media_types import MEDIA_TYPES
from engines.document.models.ksdm_models import (
    KsdDocument,
    RmlLogicalSource,
    RmlMapping,
    RmlPredicateObjectMap,
    RmlSubjectMap,
    RmlSubjectMapRef,
)


class RmlParser(BaseDocumentParser):
    supported_format = MEDIA_TYPES["rml_yaml"]

    def can_parse(self, source: str | Path) -> bool:
        if isinstance(source, str) and source.endswith(('.rml.yaml', '.rml.yml', '.rml.json')):
            return True
        try:
            if Path(source).exists():
                data = Path(source).read_bytes()[:50]
                return b"base_iri" in data or b"logicalSources" in data or b"mappings" in data
        except Exception:
            pass
        return False

    def parse(self, source: str | Path | BinaryIO | TextIO, **options: Any) -> ParseResult:
        try:
            if isinstance(source, (str, Path)):
                raw: str = Path(source).read_text(encoding='utf-8')
            elif hasattr(source, 'read'):
                _data: Any = source.read()
                raw = _data.decode('utf-8') if isinstance(_data, bytes) else str(_data)
            else:
                raise Exception("Unsupported source type")
            data = yaml.safe_load(raw) if isinstance(raw, str) else {}
            if not isinstance(data, dict):
                data = {}
            logical_sources = []
            for name, src in data.get('logicalSources', {}).items() if isinstance(data.get('logicalSources'), dict) else []:
                if isinstance(src, dict):
                    logical_sources.append(RmlLogicalSource(
                        source_name=name,
                        iterator=src.get('iterator'),
                        reference_formulation=src.get('referenceFormulation', src.get('reference_formulation')),
                        query=src.get('query'),
                        table_name=src.get('tableName', src.get('table_name'))
                    ))
            subject_maps = []
            for m in data.get('subjectMaps', data.get('subject_maps', [])):
                if isinstance(m, dict):
                    subject_maps.append(RmlSubjectMap(
                        class_type=m.get('class'),
                        graph_map=m.get('graphMap', m.get('graph_map')),
                        uri_template=m.get('template', m.get('uri_template')),
                        prefix_iri=m.get('prefixIRI', m.get('prefix_iri'))
                    ))
            pomaps = []
            for m in data.get('predicateObjectMaps', data.get('predicate_object_maps', [])):
                if isinstance(m, dict):
                    pomaps.append(RmlPredicateObjectMap(
                        predicate=m.get('predicate'),
                        object_map=m.get('objectMap', m.get('object_map')),
                        datatype=m.get('datatype'),
                        language=m.get('language'),
                        parent_triples_map=m.get('parentTriplesMap', m.get('parent_triples_map')) or ''
                    ))
            refs = []
            for m in data.get('references', []):
                if isinstance(m, dict):
                    ptm: str = m.get('parentTriplesMap', m.get('parent_triples_map', '')) or ''
                    refs.append(RmlSubjectMapRef(parent_triples_map=ptm))
            mapping = RmlMapping(
                base_iri=data.get('baseIRI', data.get('base_iri')),
                prefixes=data.get('prefixes', {}),
                logical_sources=logical_sources,
                subject_maps=subject_maps,
                predicate_object_maps=pomaps,
                references=refs
            )
            doc = KsdDocument(rml_mappings=[mapping])
            return ParseResult(document=doc)
        except Exception as e:
            raise Exception(f"RML parse failed: {e}")
