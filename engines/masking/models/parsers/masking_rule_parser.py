# engines/masking/models/parsers/masking_rule_parser.py
from __future__ import annotations

from ..masking_models import MaskingRule


def parse_masking_rule(data: dict) -> MaskingRule:
    return MaskingRule(
        field_path=data["field_path"],
        replacement=data.get("replacement", "***"),
        enabled=data.get("enabled", True),
    )
