# engines/masking/models/masking_models.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MaskingRule:
    field_path: str
    replacement: str = "***"
    enabled: bool = True


@dataclass
class AnonymizationResult:
    original: str = ""
    anonymized: str = ""
    transformations: list[dict[str, Any]] = field(default_factory=list)
