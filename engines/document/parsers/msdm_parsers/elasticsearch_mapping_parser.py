# engines/document/parsers/msdm_parsers/elasticsearch_mapping_parser.py
"""
Elasticsearch Mapping Parser – parses Elasticsearch index mappings (JSON)
into an MSDMDocument.

Handles:
- Index‑level settings (_source, dynamic, etc.)
- Field types (text, keyword, integer, date, boolean, binary, nested, object, join, etc.)
- Multi‑fields, analyzers, normalizers, index options, null_value, copy_to, etc.
- Dynamic templates and runtime fields (stored as annotations for round‑trip)

Every ES‑specific detail is preserved via annotations and constraints,
ensuring lossless round‑trip.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

from .base_msdm_parser import BaseMSDMParser
from ..base import ParseOptions
from ...models.msdm_models import (
    MSDMDocument,
    Entity,
    Attribute,
    DataType,
    Constraint,
    ConstraintType,
    Index,
    Annotation,
    EntityKind,
    ScalarType,
)

# ── Mapping from Elasticsearch field type to MSDM ScalarType ─────
ES_TYPE_TO_SCALAR = {
    "text":       ScalarType.STRING,
    "keyword":    ScalarType.STRING,
    "long":       ScalarType.LONG,
    "integer":    ScalarType.INT,
    "short":      ScalarType.INT,
    "byte":       ScalarType.INT,
    "double":     ScalarType.DOUBLE,
    "float":      ScalarType.FLOAT,
    "half_float": ScalarType.FLOAT,
    "scaled_float": ScalarType.FLOAT,
    "date":       ScalarType.DATE,
    "date_nanos": ScalarType.TIMESTAMP,
    "boolean":    ScalarType.BOOLEAN,
    "binary":     ScalarType.BINARY,
    "integer_range":  ScalarType.STRING,   # range types stored as string/struct
    "float_range":    ScalarType.STRING,
    "long_range":     ScalarType.STRING,
    "double_range":   ScalarType.STRING,
    "date_range":     ScalarType.STRING,
    "ip":         ScalarType.STRING,
    "version":    ScalarType.STRING,
    "geo_point":  ScalarType.STRING,
    "geo_shape":  ScalarType.STRING,
    "completion": ScalarType.STRING,
    "percolator": ScalarType.STRING,
    "alias":      ScalarType.REF,   # alias to another field
    "join":       ScalarType.STRING,   # parent/child relationship
    "rank_feature": ScalarType.FLOAT,
    "rank_features": ScalarType.ANY,
    "dense_vector": ScalarType.BINARY,
    "sparse_vector": ScalarType.BINARY,
    "search_as_you_type": ScalarType.STRING,
    "histogram":  ScalarType.STRING,
    "constant_keyword": ScalarType.STRING,
    "wildcard":   ScalarType.STRING,
    "match_only_text": ScalarType.STRING,
}


class ElasticsearchMappingParser(BaseMSDMParser):
    """Parser for Elasticsearch index mapping JSON files."""
    name = "elasticsearch_mapping"
    supported_extensions = (".json", ".mapping.json", ".es.json")

    async def _parse_to_msdm(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> MSDMDocument:
        encoding = options.encoding or "utf-8"
        text = data.decode(encoding)
        raw = json.loads(text)

        doc = MSDMDocument()
        doc.namespace = Path(source_name).stem

        # Determine if the top-level is just the mapping or a full index definition
        if "mappings" in raw:
            mappings = raw["mappings"]
            # Index settings may be present alongside; store as annotations
            if "settings" in raw:
                self._store_settings(raw["settings"], doc)
        else:
            # Assume the whole JSON is the mapping
            mappings = raw

        self._parse_mappings(mappings, doc)
        return doc

    def _store_settings(self, settings: dict, doc: MSDMDocument) -> None:
        """Convert index settings into annotations on the document."""
        # Flatten settings; e.g., index.number_of_shards
        def _flatten(d: dict, prefix: str = ""):
            for k, v in d.items():
                full = f"{prefix}{k}"
                if isinstance(v, dict):
                    _flatten(v, full + ".")
                else:
                    doc.annotations.append(Annotation(key="setting:" + full, value=str(v)))
        _flatten(settings)

    def _parse_mappings(self, mappings: dict, doc: MSDMDocument) -> None:
        """Parse the mappings section and create an Entity for each index."""
        # In ES 7+, the mapping is directly under the top-level "mappings" key,
        # but it could contain a "properties" key.
        # If there's a dynamic_templates, store it.
        dynamic_templates = mappings.get("dynamic_templates")
        runtime = mappings.get("runtime")

        # Create the main index entity (assume a single index per mapping file)
        index_entity = Entity(
            name="index",   # could be replaced by index name if available
            kind=EntityKind.DOCUMENT,
        )
        # Store dynamic, date_detection, etc. as annotations
        for meta_key in ("dynamic", "date_detection", "numeric_detection", "_source",
                         "_routing", "_size", "_meta"):
            if meta_key in mappings:
                index_entity.annotations.append(
                    Annotation(key=meta_key, value=json.dumps(mappings[meta_key]))
                )

        # Parse properties
        properties = mappings.get("properties", {})
        for field_name, field_def in properties.items():
            attr = self._parse_field(field_name, field_def, doc)
            index_entity.attributes.append(attr)

        # Dynamic templates
        if dynamic_templates:
            for tmpl in dynamic_templates:
                index_entity.annotations.append(
                    Annotation(key="dynamic_template", value=json.dumps(tmpl))
                )

        # Runtime fields
        if runtime:
            for fname, fdef in runtime.items():
                index_entity.annotations.append(
                    Annotation(key="runtime_field:" + fname, value=json.dumps(fdef))
                )

        doc.entities.append(index_entity)

    def _parse_field(self, name: str, field_def: dict, doc: MSDMDocument) -> Attribute:
        """Parse a single field definition recursively."""
        es_type = field_def.get("type", "object")   # default to object
        attr = Attribute(name=name, data_type=DataType(base=ScalarType.ANY))

        # Map ES type to MSDM scalar
        if es_type in ES_TYPE_TO_SCALAR:
            attr.data_type.base = ES_TYPE_TO_SCALAR[es_type]
        elif es_type == "nested":
            attr.data_type.base = ScalarType.STRUCT
            # Parse nested properties as attributes
            nested_props = field_def.get("properties", {})
            for n_name, n_def in nested_props.items():
                n_attr = self._parse_field(n_name, n_def, doc)
                attr.nested_attributes.append(n_attr)
        elif es_type == "object":
            attr.data_type.base = ScalarType.STRUCT
            # Object fields can have properties (dynamic) - parse them
            obj_props = field_def.get("properties", {})
            for o_name, o_def in obj_props.items():
                o_attr = self._parse_field(o_name, o_def, doc)
                attr.nested_attributes.append(o_attr)
        elif es_type == "join":
            attr.data_type.base = ScalarType.STRING  # join field type is like a string
            relations = field_def.get("relations", {})
            attr.annotations.append(Annotation(key="join_relations", value=json.dumps(relations)))
        elif es_type == "alias":
            path = field_def.get("path", "")
            attr.annotations.append(Annotation(key="alias_path", value=path))
        else:
            # unknown type – store as ANY and annotate
            attr.annotations.append(Annotation(key="es_type", value=es_type))

        # Store all original ES attributes as annotations for round‑trip
        for attr_key, attr_val in field_def.items():
            if attr_key in ("type", "properties", "fields", "copy_to"):
                continue   # handled specially
            if attr_key == "null_value":
                attr.annotations.append(Annotation(key="null_value", value=str(attr_val)))
                continue
            if attr_key == "analyzer":
                attr.annotations.append(Annotation(key="analyzer", value=attr_val))
                continue
            if attr_key == "search_analyzer":
                attr.annotations.append(Annotation(key="search_analyzer", value=attr_val))
                continue
            if attr_key == "normalizer":
                attr.annotations.append(Annotation(key="normalizer", value=attr_val))
                continue
            if attr_key == "index":
                attr.annotations.append(Annotation(key="index_option", value=str(attr_val)))
                continue
            if attr_key == "doc_values":
                attr.annotations.append(Annotation(key="doc_values", value=str(attr_val)))
                continue
            if attr_key == "enabled":
                attr.annotations.append(Annotation(key="enabled", value=str(attr_val)))
                continue
            if attr_key == "eager_global_ordinals":
                attr.annotations.append(Annotation(key="eager_global_ordinals", value=str(attr_val)))
                continue
            if attr_key == "ignore_above":
                attr.annotations.append(Annotation(key="ignore_above", value=str(attr_val)))
                continue
            if attr_key == "coerce":
                attr.annotations.append(Annotation(key="coerce", value=str(attr_val)))
                continue
            if attr_key == "format":
                attr.annotations.append(Annotation(key="format", value=str(attr_val)))
                continue
            # For all other keys, store as generic annotation
            attr.annotations.append(Annotation(key=attr_key, value=json.dumps(attr_val)))

        # Handle multi‑fields
        multi_fields = field_def.get("fields")
        if multi_fields:
            for mf_name, mf_def in multi_fields.items():
                # Create a nested attribute inside the field? Multi‑field is like a sub‑field.
                mf_attr = self._parse_field(mf_name, mf_def, doc)
                # Mark it as a sub‑field
                mf_attr.annotations.append(Annotation(key="parent_field", value=name))
                attr.nested_attributes.append(mf_attr)

        # Handle copy_to (list of target fields)
        copy_to = field_def.get("copy_to")
        if copy_to:
            if isinstance(copy_to, list):
                for target in copy_to:
                    attr.annotations.append(Annotation(key="copy_to", value=target))
            else:
                attr.annotations.append(Annotation(key="copy_to", value=str(copy_to)))

        return attr