# engines/masking/models/writers/masking_rule_writer.py
from __future__ import annotations

from ..masking_models import MaskingRule


def write_masking_rule(rule: MaskingRule) -> dict:
    return {"field_path": rule.field_path, "replacement": rule.replacement, "enabled": rule.enabled}
