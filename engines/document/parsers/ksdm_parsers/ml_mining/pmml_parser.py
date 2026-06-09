import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, BinaryIO, TextIO

from engines.document.parsers.base import BaseDocumentParser, ParseResult
from engines.document.models.media_types import MEDIA_TYPES
from engines.document.models.ksdm_models import (
    MlMiningDocument,
    MiningModelType,
    PmmlMiningField,
    PmmlMiningSchema,
    PmmlModel,
    PmmlVersion,
)


class PmmlParser(BaseDocumentParser):
    supported_format = MEDIA_TYPES["pmml_xml"]

    def can_parse(self, source: str | Path) -> bool:
        if isinstance(source, str) and source.endswith(('.pmml', '.pmml.xml')):
            return True
        try:
            data = Path(source).read_bytes()[:200] if Path(source).exists() else b""
            return b"<PMML" in data or b"pmml" in data.lower()
        except Exception:
            return False

    def parse(self, source: str | Path | BinaryIO | TextIO, **options: Any) -> ParseResult:
        try:
            if isinstance(source, (str, Path)):
                data = Path(source).read_bytes()
            elif hasattr(source, 'read'):
                content = source.read()
                if isinstance(content, str):
                    data = content.encode('utf-8')
                else:
                    data = content
            else:
                raise Exception("Unsupported source type")
            root = ET.fromstring(data)
            ns = {'pmml': 'http://www.dmg.org/PMML-4_2'}
            pmml_version = PmmlVersion.V4_2
            version_str = root.get('version', '4.2')
            if version_str == '4.1':
                pmml_version = PmmlVersion.V4_1
            model_data = {}
            pmml_model = None
            models = root.findall('.//pmml:MiningModel', ns) + root.findall('.//MiningModel')
            if models:
                m = models[0]
                model_type_str = m.get('modelType', 'decisionTree').lower().replace('-', '_').replace(' ', '_')
                try:
                    model_type = MiningModelType(model_type_str)
                except ValueError:
                    model_type = MiningModelType.DECISION_TREE
                mining_schema_elems = m.findall('.//pmml:MiningSchema', ns) + m.findall('.//MiningSchema')
                mining_fields = []
                if mining_schema_elems:
                    ms = mining_schema_elems[0]
                    for mf in (ms.findall('.//pmml:MiningField', ns) + ms.findall('.//MiningField')):
                        imp = mf.get('importance')
                        mining_fields.append(PmmlMiningField(
                            name=mf.get('name', ''),
                            usage_type=mf.get('usageType', 'active'),
                            importance=float(imp) if imp else None,
                            missing_value_replacement=mf.get('missingValueReplacement')
                        ))
                pmml_model = PmmlModel(
                    model_name=m.get('modelName'),
                    model_type=model_type,
                    function=m.get('functionName', 'classification'),
                    pmml_version=pmml_version,
                    mining_schema=PmmlMiningSchema(fields=mining_fields) if mining_fields else None
                )
            model_data['pmml_model'] = pmml_model
            doc = MlMiningDocument(
                model_type=model_type,
                model_data=data,
                pmml_model=pmml_model,
                title=str(Path(source).stem) if isinstance(source, (str, Path)) else "Untitled",
                document_id=str(Path(source).stem) if isinstance(source, (str, Path)) else "unknown",
                media_type=MEDIA_TYPES["pmml_xml"]
            )
            return ParseResult(document=doc)
        except Exception as e:
            raise Exception(f"PMML parse failed: {e}")
