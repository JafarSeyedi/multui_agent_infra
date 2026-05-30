"""DMN hit policies for decision tables."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class HitPolicy(str, Enum):
    UNIQUE = "UNIQUE"
    FIRST = "FIRST"
    PRIORITY = "PRIORITY"
    COLLECT = "COLLECT"
    ANY = "ANY"


def apply_hit_policy(policy: HitPolicy, matches: list[dict[str, Any]], context: dict[str, Any]) -> list[dict[str, Any]] | dict[str, Any] | None:
    if not matches:
        return None
    if policy in {HitPolicy.UNIQUE, HitPolicy.ANY, HitPolicy.FIRST}:
        return matches[0]
    return matches
