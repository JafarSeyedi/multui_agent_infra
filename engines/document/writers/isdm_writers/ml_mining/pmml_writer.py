import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, cast, BinaryIO, TextIO

from engines.document.writers.base import BaseKnowledgeWriter, BaseDocument
from engines.document.models.media_types import MEDIA_TYPES
from engines.document.models.isdm_models import MlMiningDocument


class PmmlWriter(BaseKnowledgeWriter):
    supported_format = MEDIA_TYPES["pmml_xml"]

    def can_write(self, document) -> bool:
        return isinstance(document, MlMiningDocument)

    async def write(self, document: BaseDocument, destination: str | Path | BinaryIO | TextIO | None = None, **options: Any) -> bytes:
        pmml_ns = 'http://www.dmg.org/PMML-4_2'
        root = ET.Element('PMML')
        root.set('version', '4.2')
        root.set('xmlns', pmml_ns)
        pmml_model = getattr(document, 'pmml_model', None)
        if pmml_model is not None:
            model_elem = ET.SubElement(root, 'MiningModel')
            model_elem.set('modelName', pmml_model.model_name or '')
            model_elem.set('modelType', pmml_model.model_type.value if pmml_model.model_type else 'decisionTree')
            model_elem.set('functionName', pmml_model.function)
            if pmml_model.mining_schema:
                ms_elem = ET.SubElement(model_elem, 'MiningSchema')
                for mf in pmml_model.mining_schema.fields:
                    mf_elem = ET.SubElement(ms_elem, 'MiningField')
                    mf_elem.set('name', mf.name)
                    mf_elem.set('usageType', mf.usage_type)
                    if mf.importance:
                        mf_elem.set('importance', str(mf.importance))
                    if mf.missing_value_replacement:
                        mf_elem.set('missingValueReplacement', str(mf.missing_value_replacement))
        else:
            model_elem = ET.SubElement(root, 'MiningModel')
            model_elem.set('modelType', document.model_type.value if hasattr(document, 'model_type') and document.model_type else 'decisionTree')
        ET.indent(ET.ElementTree(root), space='  ')
        xml_bytes = ET.tostring(root, encoding='unicode').encode('utf-8')
        if destination is not None:
            if isinstance(destination, (str, Path)):
                Path(destination).write_bytes(xml_bytes)
            else:
                cast(BinaryIO, destination).write(xml_bytes)
        return xml_bytes
