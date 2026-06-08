from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, BinaryIO, TextIO

import yaml

from engines.document.models.ksdm_models import KsdDocument
from engines.document.writers.base import BaseDocument, BaseDocumentWriter


class RmlWriter(BaseDocumentWriter):
    supported_format = None

    def can_write(self, document) -> bool:
        return isinstance(document, KsdDocument) and bool(getattr(document, 'rml_mappings', []))

    def write(self, document: BaseDocument, destination: str | Path | BinaryIO | TextIO | None = None, **options: Any) -> bytes:
        mappings = []
        for m in getattr(document, 'rml_mappings', []):
            mapping = {'baseIRI': m.base_iri, 'prefixes': dict(m.prefixes)}
            logical_sources = {}
            for ls in m.logical_sources:
                logical_sources[ls.source_name or 'source'] = {
                    'reference': ls.reference_formulation,
                    **({'query': ls.query} if ls.query else {}),
                    **({'tableName': ls.table_name} if ls.table_name else {})
                }
            if logical_sources:
                mapping['logicalSources'] = logical_sources
            subject_maps = []
            for sm in m.subject_maps:
                sm_dict = {}
                if sm.class_type:
                    sm_dict['class'] = sm.class_type
                if sm.uri_template:
                    sm_dict['template'] = sm.uri_template
                if sm_dict:
                    subject_maps.append(sm_dict)
            if subject_maps:
                mapping['subjectMaps'] = subject_maps
            poms = []
            for pom in m.predicate_object_maps:
                pom_dict = {}
                if pom.predicate:
                    pom_dict['predicate'] = pom.predicate
                if pom.object_map:
                    pom_dict['objectMap'] = pom.object_map
                if pom_dict:
                    poms.append(pom_dict)
            if poms:
                mapping['predicateObjectMaps'] = poms
            mappings.append(mapping)
        out = {'mappings': mappings} if mappings else {}
        output_bytes = yaml.dump(out, default_flow_style=False, allow_unicode=True, sort_keys=False).encode('utf-8')
        if destination is not None:
            if isinstance(destination, (str, Path)):
                Path(destination).write_bytes(output_bytes)
            else:
                destination.write(output_bytes.decode('utf-8'))  # type: ignore
        return output_bytes

    async def write_stream(self, document: BaseDocument) -> AsyncIterator[bytes]:
        yield self.write(document)

    async def write_to_file(self, document: BaseDocument, target: Path, options: dict[str, Any] | None = None) -> None:
        target.write_bytes(self.write(document))

    def get_supported_media_types(self) -> list[str]:
        return ["application/x-yaml"]

    def get_supported_extensions(self) -> list[str]:
        return [".rml.yaml", ".rml.yml"]
