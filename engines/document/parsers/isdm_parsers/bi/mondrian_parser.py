import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, BinaryIO, TextIO

from engines.document.parsers.base import BaseKnowledgeParser, KnowledgeParseError, ParseResult
from engines.document.models.media_types import MEDIA_TYPES
from engines.document.models.isdm_models import (
    BiAggregationDocument,
    BiAggregationKind,
    MondrianDimension,
    MondrianDimensionHierarchy,
    MondrianLevel,
    MondrianMeasure,
    MondrianSchema,
)


class MondrianSchemaParser(BaseKnowledgeParser):
    supported_format = MEDIA_TYPES["mondrian_schema_xml"]

    def can_parse(self, source: str | Path) -> bool:
        if isinstance(source, str) and source.endswith(('.mondrian.xml', '.schema.xml', '.xml')):
            return True
        try:
            data = Path(source).read_bytes()[:200] if Path(source).exists() else b""
            return b"mondrian" in data.lower() or b"<Schema" in data
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
                raise KnowledgeParseError("Unsupported source type")
            root = ET.fromstring(data)
            schema_name = root.get('name', root.get('schemaName', ''))
            schema_table = None
            schema_elem = root.find('.//Schema') or root.find('.//schema')
            if schema_elem is not None:
                schema_name = schema_elem.get('name', schema_name)
                schema_table = schema_elem.get('table')
            schema = MondrianSchema(name=schema_name, table=schema_table)
            for cube_elem in (root.findall('.//Cube') + root.findall('.//cube')):
                cube_elem.get('name', '')
                for dim_elem in (cube_elem.findall('.//Dimension') + cube_elem.findall('.//dimension')):
                    hierarchy_elems = dim_elem.findall('.//Hierarchy') + dim_elem.findall('.//hierarchy')
                    hierarchy = None
                    if hierarchy_elems:
                        h = hierarchy_elems[0]
                        has_all = h.get('hasAll', 'true').lower() != 'false'
                        pk = h.get('primaryKey')
                        levels = []
                        for lvl_elem in (h.findall('.//Level') + h.findall('.//level')):
                            levels.append(MondrianLevel(
                                name=lvl_elem.get('name', ''),
                                table=lvl_elem.get('table', ''),
                                column=lvl_elem.get('column', ''),
                                name_column=lvl_elem.get('nameColumn'),
                                unique_members=lvl_elem.get('uniqueMembers', 'true').lower() != 'false',
                                level_type=lvl_elem.get('levelType', 'Regular')
                            ))
                        hierarchy = MondrianDimensionHierarchy(has_all=has_all, primary_key=pk, levels=levels)
                    schema.dimensions.append(MondrianDimension(
                        name=dim_elem.get('name', ''),
                        type=dim_elem.get('type', 'StandardDimension'),
                        hierarchy=hierarchy
                    ))
                for measure_elem in (cube_elem.findall('.//Measure') + cube_elem.findall('.//measure')):
                    schema.measures.append(MondrianMeasure(
                        name=measure_elem.get('name', ''),
                        column=measure_elem.get('column', ''),
                        aggregator_name=measure_elem.get('aggregator', 'sum'),
                        visible=measure_elem.get('visible', 'true').lower() != 'false'
                    ))
            doc = BiAggregationDocument(bi_aggregation_kind=BiAggregationKind.MONDRIAN_SCHEMA, mondrian_schema=schema)
            return ParseResult(document=doc)
        except Exception as e:
            raise KnowledgeParseError(f"Mondrian schema parse failed: {e}")
