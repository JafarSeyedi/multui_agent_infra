# engines/document/parsers/osdm_parsers/cep_parser.py
"""
CEP (Complex Event Processing) Parser – converts a CEP JSON file into a
CEPDocument (unified OSDM model).

Mapping rules:
- Top‑level JSON can be a single CEP definition or an array.
  Each definition contains:
    * id, name
    * "streams" → list of EventStream (name, attributes dict)
    * "rules" → list of CEPRule (name, pattern, operator, window_duration,
                  filter_expression, actions list)
- Actions can be plain strings (action ids) or objects with a "script" key
  (representing a Script action). Both are stored in the ActionList.
- Operator is parsed into the CEPOperator enum; if unrecognised it defaults
  to AND.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Optional, Any, List

from .base_osdm_parser import BaseOSDMParser
from ..base import ParseOptions
from ...models.osdm_models import (
    BaseOSDMDocument,
    CEPDocument,
    EventStream,
    CEPRule,
    CEPDefinition,
    CEPOperator,
    ActionList,
    Script,
    ScriptLanguage,
)
from ...models.base import BaseDocument


class CEPParser(BaseOSDMParser):
    """Parser for CEP JSON files (.cep.json)."""

    name = "cep"
    supported_extensions = (".cep.json",)

    async def _parse_to_document(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> BaseOSDMDocument:
        encoding = options.encoding or "utf-8"
        text = data.decode(encoding)
        raw = json.loads(text)

        doc = CEPDocument()

        # Support both a single object and an array of definitions
        if isinstance(raw, list):
            definitions = raw
        else:
            definitions = [raw]

        for entry in definitions:
            cep_def = self._parse_definition(entry)
            doc.cep_definitions.append(cep_def)

        return doc

    def _parse_definition(self, data: dict) -> CEPDefinition:
        streams_data = data.get("streams", [])
        rules_data = data.get("rules", [])

        streams = [self._parse_stream(s) for s in streams_data]
        rules = [self._parse_rule(r) for r in rules_data]

        return CEPDefinition(
            id=data.get("id", ""),
            name=data.get("name", ""),
            streams=streams,
            rules=rules,
        )

    def _parse_stream(self, data: dict) -> EventStream:
        return EventStream(
            name=data.get("name", ""),
            attributes=data.get("attributes", {}),
        )

    def _parse_rule(self, data: dict) -> CEPRule:
        operator_str = data.get("operator", "and").lower()
        # Map common operator strings to CEPOperator
        operator_map = {
            "and": CEPOperator.AND,
            "or": CEPOperator.OR,
            "not": CEPOperator.NOT,
            "sequence": CEPOperator.SEQUENCE,
            "window": CEPOperator.WINDOW,
            "threshold": CEPOperator.THRESHOLD,
            "absence": CEPOperator.ABSENCE,
        }
        operator = operator_map.get(operator_str, CEPOperator.AND)

        # Parse actions
        actions = ActionList()
        raw_actions = data.get("actions", [])
        for action in raw_actions:
            if isinstance(action, str):
                actions.actions.append(action)
            elif isinstance(action, dict) and "script" in action:
                # Store as a Script object
                script = Script(
                    script_body=action["script"],
                    script_language=ScriptLanguage(action.get("language", "Python")),
                )
                actions.actions.append(script)
            else:
                # Fallback: convert to string
                actions.actions.append(str(action))

        return CEPRule(
            name=data.get("name", ""),
            pattern=data.get("pattern", ""),
            operator=operator,
            window_duration=data.get("window_duration"),
            filter_expression=data.get("filter_expression"),
            actions=actions,
        )