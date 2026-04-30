# engines/document/writers/msdm_writers/elasticsearch_mapping_writer.py
"""
Elasticsearch Mapping Writer – converts an MSDMDocument into an Elasticsearch
index mapping JSON (and optional settings).  Handles nested objects, multi‑fields,
all ES‑specific field options (analyzer, null_value, etc.) stored as annotations,
dynamic templates, runtime fields, and index settings.

The writer outputs a JSON object representing the mapping.  If the document
contains multiple DOCUMENT‑kind entities they are written as an array.
Soft‑delete is not ddl‑based; deleted attributes are omitted from the output.
"""

from __future__ import annotations
import json
from typing import Optional, Dict, Any, List, Union

from .base_msdm_writer import BaseMSDMWriter, WriteTarget, SoftDeleteStrategy
from ..base import WriteOptions
from ...models.msdm_models import (
    MSDMDocument,
    Entity,
    Attribute,
    DataType,
    ScalarType,
    Annotation,
)
try:
    from elasticsearch import AsyncElasticsearch
    ES_AVAILABLE = True
except ImportError:
    ES_AVAILABLE = False



# ── ScalarType → default Elasticsearch field type ─────────────────
SCALAR_TO_ES_TYPE = {
    ScalarType.STRING:    "keyword",       # safer default; can be overridden by annotation
    ScalarType.INT:       "integer",
    ScalarType.LONG:      "long",
    ScalarType.FLOAT:     "float",
    ScalarType.DOUBLE:    "double",
    ScalarType.BOOLEAN:   "boolean",
    ScalarType.DATE:      "date",
    ScalarType.TIME:      "date",          # ES doesn't have a time type; use date
    ScalarType.TIMESTAMP: "date",
    ScalarType.BINARY:    "binary",
    ScalarType.DECIMAL:   "scaled_float",  # could use double
    ScalarType.UUID:      "keyword",
    ScalarType.ANY:       "object",        # fallback
    # Composite types handled separately
}

# Annotations that map 1:1 to Elasticsearch field mapping keys
_ES_FIELD_ANNOTATIONS = {
    "analyzer", "search_analyzer", "normalizer", "index_options",
    "null_value", "copy_to", "doc_values", "eager_global_ordinals",
    "enabled", "format", "ignore_above", "coerce", "term_vector",
    "similarity", "store", "fielddata", "index", "boost",
    "position_increment_gap", "ignore_malformed",
}


class ElasticsearchMappingWriter(BaseMSDMWriter):
    """Writer for Elasticsearch index mapping files (.mapping.json)."""
    name = "elasticsearch_mapping"
    supported_extensions = (".json", ".mapping.json", ".es.json")

    def __init__(
        self,
        options: Optional[WriteOptions] = None,
        target_mode: WriteTarget = WriteTarget.DESIGN_FILE,
        soft_delete_strategy: SoftDeleteStrategy = SoftDeleteStrategy.NONE,
    ):
        super().__init__(options, target_mode, soft_delete_strategy)

    # ── Public API ─────────────────────────────────────────────────
    async def _write_design(self, document: MSDMDocument) -> bytes:
        # Collect DOCUMENT‑kind entities; if none, use all entities
        doc_entities = [e for e in document.entities if e.kind.value == "document"]
        if not doc_entities:
            doc_entities = document.entities   # fallback

        results = []
        for entity in doc_entities:
            index_def = self._build_index_definition(entity, document)
            results.append(index_def)

        if len(results) == 1:
            output = results[0]
        else:
            output = results

        json_bytes = json.dumps(output, indent=2, ensure_ascii=False).encode(
            self.options.encoding or "utf-8"
        )
        return json_bytes

    async def get_supported_media_types(self) -> list[str]:
        return ["application/json"]

    async def get_supported_extensions(self) -> list[str]:
        return self.supported_extensions

    # ── Index definition (settings + mappings) ────────────────────
    def _build_index_definition(self, entity: Entity, doc: MSDMDocument) -> dict:
        index_def: Dict[str, Any] = {}

        # Settings from document‑level annotations (key starts with "setting:")
        settings = self._extract_settings(doc.annotations)
        if settings:
            index_def["settings"] = settings

        # Mappings
        mapping = {}
        # Dynamic, date_detection, etc. stored as entity annotations
        for ann in entity.annotations:
            if ann.key in ("dynamic", "date_detection", "numeric_detection",
                           "_source", "_routing", "_size", "_meta"):
                mapping[ann.key] = json.loads(ann.value)

        # Properties
        properties = {}
        for attr in entity.attributes:
            if self._is_soft_deleted(attr):
                continue   # skip deleted attributes
            field_def = self._attribute_to_es_field(attr)
            properties[attr.name] = field_def
        mapping["properties"] = properties

        # Dynamic templates
        dynamic_templates = self._extract_dynamic_templates(entity.annotations)
        if dynamic_templates:
            mapping["dynamic_templates"] = dynamic_templates

        # Runtime fields
        runtime = self._extract_runtime_fields(entity.annotations)
        if runtime:
            mapping["runtime"] = runtime

        index_def["mappings"] = mapping
        return index_def

    # ── Attribute → ES field definition ────────────────────────────
    def _attribute_to_es_field(self, attr: Attribute) -> dict:
        field = {}

        # Determine ES type
        es_type = self._get_es_type(attr)
        field["type"] = es_type

        # For text/keyword, copy sub‑fields if present (multi‑field)
        multi_fields = self._extract_multi_fields(attr.nested_attributes)
        if multi_fields:
            field["fields"] = multi_fields

        # Nested object or nested type
        if es_type in ("object", "nested") and attr.nested_attributes:
            # If explicit nested type, keep type
            # Build properties from nested attributes (those not marked as parent_field)
            nested_props = {}
            for na in attr.nested_attributes:
                if self._is_soft_deleted(na):
                    continue
                # Skip multi‑field sub‑fields that are already handled
                if any(a.key == "parent_field" and a.value == attr.name for a in na.annotations):
                    continue
                nested_props[na.name] = self._attribute_to_es_field(na)
            if nested_props:
                field["properties"] = nested_props

        # Apply ES‑specific annotations
        for ann in attr.annotations:
            if ann.key in _ES_FIELD_ANNOTATIONS:
                try:
                    val = json.loads(ann.value)
                except (json.JSONDecodeError, TypeError):
                    val = ann.value
                # Special handling for 'index' (boolean)
                if ann.key == "index" and isinstance(val, str):
                    val = val.lower() == "true"
                field[ann.key] = val
            elif ann.key == "es_type":
                # Already used, skip
                continue
            elif ann.key in ("multi_field", "parent_field"):
                continue   # handled separately
            # Other annotations are stored in _meta if we want round‑trip
            # but mapping doesn't have arbitrary keys; we'll put in _meta
            if ann.key not in ("description", "comment", "static", "visibility"):
                # Add to _meta if not already a recognized es option
                if "_meta" not in field:
                    field["_meta"] = {}
                field["_meta"][ann.key] = ann.value

        # Description as meta?
        if attr.description and "_meta" not in field:
            field["_meta"] = {"description": attr.description}

        return field

    # ── Determine ES type ──────────────────────────────────────────
    def _get_es_type(self, attr: Attribute) -> str:
        # 1) Explicit annotation "es_type"
        es_ann = next((a for a in attr.annotations if a.key == "es_type"), None)
        if es_ann:
            return es_ann.value

        # 2) Based on DataType
        dt = attr.data_type
        base = dt.base

        if base == ScalarType.ARRAY:
            # ES doesn't have array type; arrays are just multi‑valued fields.
            # Return the type of the element
            if dt.element_type:
                # Create a temporary attr to get type
                tmp_attr = Attribute(name="tmp", data_type=dt.element_type)
                return self._get_es_type(tmp_attr)
            return "keyword"   # fallback

        if base == ScalarType.STRUCT:
            # Check if there is an annotation that explicitly marks nested
            if any(a.key == "es_type" and a.value == "nested" for a in attr.annotations):
                return "nested"
            return "object"

        if base == ScalarType.MAP:
            # Typically mapped as object with dynamic mapping
            return "object"

        if base == ScalarType.REF:
            # Reference to another entity – treat as object? It depends; we could use join type.
            # Simpler: return "keyword" for the id
            return "keyword"

        if base in SCALAR_TO_ES_TYPE:
            return SCALAR_TO_ES_TYPE[base]

        return "keyword"   # ultimate fallback

    # ── Multi‑fields extraction ────────────────────────────────────
    def _extract_multi_fields(self, nested_attrs: List[Attribute]) -> dict:
        """Extract multi‑fields from nested attributes that have annotation 'parent_field'."""
        fields = {}
        for na in nested_attrs:
            parent_name = next((a.value for a in na.annotations if a.key == "parent_field"), None)
            if parent_name:
                # This is a sub‑field
                sub_def = self._attribute_to_es_field(na)
                fields[na.name] = sub_def
        return fields if fields else {}

    # ── Soft‑delete detection ──────────────────────────────────────
    def _is_soft_deleted(self, attr: Attribute) -> bool:
        """Return True if the attribute is marked as deleted via annotation."""
        return any(a.key == "deleted" for a in attr.annotations)

    # ── Document‑level settings extraction ─────────────────────────
    def _extract_settings(self, annotations: List[Annotation]) -> dict:
        settings = {}
        for ann in annotations:
            if ann.key.startswith("setting:"):
                key = ann.key[8:]   # remove "setting:"
                val = ann.value
                # Convert dots to nested dict
                self._set_dot_path(settings, key, val)
        return settings

    @staticmethod
    def _set_dot_path(d: dict, key: str, value: str) -> None:
        """Set a nested dict value using a dot‑separated path."""
        parts = key.split(".")
        for part in parts[:-1]:
            d = d.setdefault(part, {})
        d[parts[-1]] = value

    def _extract_dynamic_templates(self, annotations: List[Annotation]) -> list:
        templates = []
        for ann in annotations:
            if ann.key == "dynamic_template":
                try:
                    template = json.loads(ann.value)
                    templates.append(template)
                except json.JSONDecodeError:
                    pass
        return templates

    def _extract_runtime_fields(self, annotations: List[Annotation]) -> dict:
        runtime = {}
        for ann in annotations:
            if ann.key.startswith("runtime_field:"):
                field_name = ann.key[13:]
                try:
                    runtime[field_name] = json.loads(ann.value)
                except json.JSONDecodeError:
                    pass
        return runtime

    async def apply_to_database(self, document: MSDMDocument, connection: ConnectionConfig = None):
        if not ES_AVAILABLE:
            raise ImportError("elasticsearch is required. pip install elasticsearch")
        if connection is None:
            raise ValueError("ConnectionConfig required")

        hosts = [f"{connection.host or 'localhost'}:{connection.port or 9200}"]
        es = AsyncElasticsearch(hosts=hosts)
        try:
            # For each entity representing an index, create/update its mapping
            for entity in document.entities:
                if entity.kind != EntityKind.DOCUMENT:
                    continue
                index_name = entity.name
                exists = await es.indices.exists(index=index_name)
                if not exists:
                    # Create index with mapping
                    mapping_body = self._build_index_definition(entity, document)
                    await es.indices.create(index=index_name, body=mapping_body)
                else:
                    # Update mapping? ES mapping updates are limited; we can put mapping for new fields.
                    # For simplicity, we reindex? Not safe. We'll just update settings maybe.
                    # If soft-delete requires removing fields, we can't remove mapping fields; we'd need reindex.
                    # We'll skip heavy migration for now.
                    pass
            # Remove indices not in the document
            model_indices = {e.name for e in document.entities if e.kind == EntityKind.DOCUMENT}
            existing_indices = set((await es.indices.get(index="*")).keys())
            for idx in existing_indices - model_indices:
                await self._handle_index_deletion(es, idx)
        finally:
            await es.close()

    async def _handle_index_deletion(self, es, index_name: str):
        if self.soft_delete_strategy == SoftDeleteStrategy.NONE:
            await es.indices.delete(index=index_name)
        elif self.soft_delete_strategy == SoftDeleteStrategy.PREFIX:
            new_name = f"_deleted_{index_name}"
            # reindex into new name? Not directly; we could create alias? Simpler: rename es indices is not native; we'll skip.
            pass        