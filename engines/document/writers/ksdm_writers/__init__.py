"""KSDM writers."""

from __future__ import annotations

import json
import csv
import io
from typing import Any
from engines.document.models.ksdm_models import Entity as Entity, EntityType as EntityType, KSDMDocument, Relation as Relation, RelationType as RelationType


class KSDMJSONWriter:
    """Writer for KSDM JSON format."""
    
    async def write(self, doc: KSDMDocument) -> bytes:
        data = {
            "version": "1.0",
            "entities": [
                {
                    "id": e.id,
                    "type": e.type.value if e.type else "Unknown",
                    "label": e.label,
                    "properties": e.properties,
                    "embedding": e.embedding,
                }
                for e in doc.entities
            ],
            "relations": [
                {
                    "id": r.id,
                    "source_id": r.source_id,
                    "target_id": r.target_id,
                    "type": r.type.value if r.type else "related",
                    "weight": r.weight,
                    "timestamp": r.timestamp,
                }
                for r in doc.relations
            ],
        }
        return json.dumps(data).encode("utf-8")


class KSDMYAMLWriter:
    """Writer for KSDM YAML format."""
    
    async def write(self, doc: KSDMDocument) -> bytes:
        import yaml
        data = {
            "version": "1.0",
            "entities": [{"id": e.id, "type": e.type.value if e.type else "Unknown"} for e in doc.entities],
            "relations": [{"id": r.id, "source_id": r.source_id, "target_id": r.target_id} for r in doc.relations],
        }
        return yaml.dump(data).encode("utf-8")


class CSVGraphWriter:
    """Writer for CSV graph format."""
    
    async def write(self, doc: KSDMDocument) -> bytes:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["source_id", "target_id", "relation_type", "weight", "timestamp"])
        for r in doc.relations:
            writer.writerow([r.source_id, r.target_id, r.type.value if r.type else "", r.weight or "", r.timestamp or ""])
        return output.getvalue().encode("utf-8")


class RMLYAMLWriter:
    """Writer for RML YAML format."""
    
    async def write(self, doc: KSDMDocument) -> bytes:
        import yaml
        data: dict[str, Any] = {"mappings": doc.ontology.get("rml_mapping", []) if doc.ontology else []}
        return yaml.dump(data).encode("utf-8")
