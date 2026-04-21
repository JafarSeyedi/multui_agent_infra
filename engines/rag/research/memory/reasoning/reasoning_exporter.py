# rag/research/memory/reasoning/reasoning_exporter.py

from __future__ import annotations

import json
from typing import Dict


class ReasoningExporter:

    @staticmethod
    def to_json(trace: Dict):

        return json.dumps(trace, indent=2)

    @staticmethod
    def summary(trace: Dict):

        lines = []

        def walk(node, depth=0):

            prefix = "  " * depth

            lines.append(f"{prefix}{node['name']}")

            for e in node["events"]:
                lines.append(
                    f"{prefix}  [{e['type']}] {e['message']}"
                )

            for c in node["children"]:
                walk(c, depth + 1)

        walk(trace)

        return "\n".join(lines)

