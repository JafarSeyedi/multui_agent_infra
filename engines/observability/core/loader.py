from __future__ import annotations

import os
from typing import Any

import yaml


_ENGINES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_OBSERVABILITY_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def discover_trace_definitions() -> dict[str, dict[str, Any]]:
    definitions: dict[str, dict[str, Any]] = {}
    if not os.path.isdir(_ENGINES_DIR):
        return definitions
    for engine_name in sorted(os.listdir(_ENGINES_DIR)):
        engine_path = os.path.join(_ENGINES_DIR, engine_name)
        trace_file = os.path.join(engine_path, "trace_definitions.yaml")
        if os.path.isfile(trace_file):
            with open(trace_file) as f:
                data = yaml.safe_load(f)
            if isinstance(data, dict):
                definitions[engine_name] = data
    return definitions


def load_config() -> dict[str, Any]:
    config_path = os.path.join(_OBSERVABILITY_DIR, "config", "observability.yaml")
    if os.path.isfile(config_path):
        with open(config_path) as f:
            return yaml.safe_load(f) or {}
    return {"backend": "agentops"}
