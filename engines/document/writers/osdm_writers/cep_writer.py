# engines/document/writers/osdm_writers/cep_writer.py
"""
Complex Event Processing (CEP) Writer – converts OSDM CEPDefinition objects into
a generic JSON representation suitable for CEP engines (Esper, Flink, etc.).
Multiple definitions are written as a JSON array.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, cast

from .base_osdm_writer import BaseOSDMWriter, OSDMWriteOptions
from ...models.osdm_models import (
    BaseOSDMDocument, CEPDocument,
    CEPDefinition,
    CEPRule,
    EventStream,
    ActionList,
)
from ...models.base import BaseDocument


class CEPWriter(BaseOSDMWriter):
    """Serialises OSDM CEP definitions to JSON."""

    name = "cep"
    supported_extensions = (".cep.json",)

    def __init__(self, options: Optional[OSDMWriteOptions] = None):
        super().__init__(options)

    async def _write_design(self, base_document: BaseOSDMDocument) -> bytes:
        document = cast(CEPDocument, base_document)
        definitions = None
        if document:
            definitions = document.cep_definitions
        if not definitions:
            output = {"message": "No CEP definitions found."}
        elif len(definitions) == 1:
            output = self._definition_to_dict(definitions[0])
        else:
            output = [self._definition_to_dict(d) for d in definitions]
        json_str = json.dumps(output, indent=2, ensure_ascii=False)
        return json_str.encode(self.options.encoding or "utf-8")

    def get_supported_media_types(self) -> list[str]:
        return ["application/json"]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    def _definition_to_dict(self, cep_def: CEPDefinition) -> dict:
        return {
            "id": cep_def.id,
            "name": cep_def.name,
            "streams": [self._stream_to_dict(s) for s in cep_def.streams],
            "rules": [self._rule_to_dict(r) for r in cep_def.rules],
        }

    def _stream_to_dict(self, stream: EventStream) -> dict:
        return {
            "name": stream.name,
            "attributes": stream.attributes,
        }

    def _rule_to_dict(self, rule: CEPRule) -> dict:
        return {
            "name": rule.name,
            "pattern": rule.pattern,
            "operator": rule.operator.value if rule.operator else "and",
            "window_duration": rule.window_duration,
            "filter_expression": rule.filter_expression,
            "actions": self._actions_to_list(rule.actions),
        }

    def _actions_to_list(self, actions: ActionList) -> list:
        result = []
        for act in actions.actions:
            if isinstance(act, str):
                result.append(act)
            else:
                # Script object – include its content
                result.append({
                    "script": act.script_body,
                    "language": act.script_language.value if act.script_language else None,
                })
        return result