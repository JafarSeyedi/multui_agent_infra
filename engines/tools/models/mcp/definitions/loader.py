from __future__ import annotations

import os
from typing import Any

import yaml


_DEFINITIONS_DIR = os.path.dirname(os.path.abspath(__file__))


def load_mcp_definitions() -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    if not os.path.isdir(_DEFINITIONS_DIR):
        return results
    for fname in sorted(os.listdir(_DEFINITIONS_DIR)):
        if fname.endswith(".yaml") or fname.endswith(".yml"):
            fpath = os.path.join(_DEFINITIONS_DIR, fname)
            with open(fpath) as f:
                data = yaml.safe_load(f)
            if isinstance(data, dict):
                results.append(data)
    return results


def get_mcp_definition(def_id: str) -> dict[str, Any] | None:
    for d in load_mcp_definitions():
        if d.get("id") == def_id:
            return d
    return None
