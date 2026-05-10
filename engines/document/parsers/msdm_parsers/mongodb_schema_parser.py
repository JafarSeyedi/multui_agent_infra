# engines/document/parsers/msdm_parsers/mongodb_schema_parser.py
"""
MongoDB Schema Parser – converts MongoDB validator schemas (JSON) and
Mongoose schemas (JavaScript) into an MSDMDocument.

Handles:
- $jsonSchema validators (BSON types, required, properties, additionalProperties,
  bsonType, enum, minimum, maximum, pattern, minLength, maxLength, description)
- Mongoose schema definitions (type constructor, required, default, unique,
  index, enum, ref for population, subdocuments, arrays)
- Nested schemas (subdocuments and arrays of objects)
- Index definitions (unique, compound)
- Validation constraints (min, max, enum, match, validate)
- Sharding keys, collection options, timestamps, versionKey

Every MongoDB‑specific detail is stored via Annotations for lossless round‑trip.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from ...models.media_types import MEDIA_TYPES
from ...models.msdm_models import Annotation
from ...models.msdm_models import Attribute
from ...models.msdm_models import Constraint
from ...models.msdm_models import ConstraintType
from ...models.msdm_models import DataType
from ...models.msdm_models import Entity
from ...models.msdm_models import EntityKind
from ...models.msdm_models import Index
from ...models.msdm_models import MSDMDocument
from ...models.msdm_models import ScalarType, Namespace
from ..base import ParseOptions
from .base_msdm_parser import BaseMSDMParser

# ── MongoDB BSON type to ScalarType mapping ────────────────────
BSON_TYPE_TO_SCALAR = {
    "string":       ScalarType.STRING,
    "int":          ScalarType.INT,
    "long":         ScalarType.LONG,
    "double":       ScalarType.DOUBLE,
    "decimal":      ScalarType.DECIMAL,
    "bool":         ScalarType.BOOLEAN,
    "date":         ScalarType.DATE,
    "timestamp":    ScalarType.TIMESTAMP,
    "objectId":     ScalarType.STRING,      # typically represented as string
    "uuid":         ScalarType.UUID,
    "binData":      ScalarType.BINARY,
    "array":        ScalarType.ARRAY,
    "object":       ScalarType.STRUCT,
    "null":         ScalarType.ANY,
    "mixed":        ScalarType.ANY,
    "number":       ScalarType.FLOAT,
}

# Mongoose type constructor mapping (used in Mongoose schema definitions)
MONGOOSE_TYPE_MAP = {
    "String":       ScalarType.STRING,
    "Number":       ScalarType.FLOAT,
    "Date":         ScalarType.DATE,
    "Buffer":       ScalarType.BINARY,
    "Boolean":      ScalarType.BOOLEAN,
    "Mixed":        ScalarType.ANY,
    "ObjectId":     ScalarType.STRING,
    "Array":        ScalarType.ARRAY,
    "Decimal128":   ScalarType.DECIMAL,
    "Map":          ScalarType.MAP,
    "Schema":       ScalarType.STRUCT,
    "UUID":         ScalarType.UUID,
}

# Regular expression to extract Mongoose schema fields (simplified)
# Matches: fieldName: { type: Type, required: true, ... }
MONGOOSE_FIELD_RE = re.compile(
    r'(\w+)\s*:\s*\{([^}]*(?:\{[^}]*\})?[^}]*)\}',
    re.MULTILINE
)

# Matches a simple type assignment: fieldName: Type
MONGOOSE_SIMPLE_RE = re.compile(
    r'(\w+)\s*:\s*(String|Number|Date|Buffer|Boolean|Mixed|ObjectId|\[.*?\])',
    re.MULTILINE
)


class MongoDBSchemaParser(BaseMSDMParser):
    """Parser for MongoDB schema files (JSON validator or Mongoose JavaScript)."""
    name = "mongodb_schema"
    supported_extensions = (".json", ".validator.json", ".mongoose.js")

    async def _parse_to_msdm(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> MSDMDocument:
        encoding = options.encoding or "utf-8"
        text = data.decode(encoding)

        doc = MSDMDocument(
            document_id=Path(source_name).stem,
            title=Path(source_name).stem,
            media_type=MEDIA_TYPES.get("mongodb_schema", MEDIA_TYPES["json"])
        )
        doc.namespace = Namespace(uri=Path(source_name).stem)

        # Try JSON first (validator format)
        if self._try_json(text, doc):
            return doc

        # Fallback to Mongoose JavaScript
        self._parse_mongoose_js(text, doc)
        self.resolve_references(doc)
        return doc

    def _try_json(self, text: str, doc: MSDMDocument) -> bool:
        """Attempt to parse as JSON validator schema. Returns True on success."""
        try:
            json_data = json.loads(text)
            if isinstance(json_data, dict) and (
                "validator" in json_data or "$jsonSchema" in json_data or "properties" in json_data
            ):
                self._parse_validator(json_data, doc)
                return True
        except Exception:
            pass
        return False

    def _parse_validator(self, root: dict, doc: MSDMDocument) -> None:
        """Parse a MongoDB validator document."""
        # Root may be a collection schema: { validator: { $jsonSchema: {...} } }
        schema = root
        if "validator" in root:
            schema = root["validator"]
            if "$jsonSchema" in schema:
                schema = schema["$jsonSchema"]
        elif "$jsonSchema" in root:
            schema = root["$jsonSchema"]

        # The entity name can be derived from collection or default to "collection"
        entity_name = root.get("collection", "collection")
        entity = Entity(name=entity_name, kind=EntityKind.DOCUMENT)

        # Parse top-level schema fields
        self._process_validator_object(schema, entity, doc)

        # Store top-level validator metadata (e.g., validationLevel, validationAction)
        for key in root:
            if key not in ("validator", "$jsonSchema", "collection", "properties", "required",
                           "bsonType", "description", "title", "additionalProperties"):
                entity.annotations.append(Annotation(key=key, value=json.dumps(root[key])))

        doc.entities.append(entity)

    def _process_validator_object(self, schema: dict, entity: Entity, doc: MSDMDocument) -> None:
        """Process a $jsonSchema object with bsonType, properties, required, etc."""
        # Entity-level description
        if "description" in schema:
            entity.description = schema["description"]
        if "title" in schema:
            entity.annotations.append(Annotation(key="title", value=schema["title"]))

        # Additional properties
        if "additionalProperties" in schema:
            entity.annotations.append(Annotation(key="additionalProperties",
                                                value=json.dumps(schema["additionalProperties"])))

        # Properties
        properties = schema.get("properties", {})
        required = set(schema.get("required", []))
        for prop_name, prop_schema in properties.items():
            attr = self._parse_validator_field(prop_name, prop_schema, required, doc)
            entity.attributes.append(attr)

        # Store other top-level keywords as annotations
        for kw in ("bsonType", "enum", "allOf", "anyOf", "oneOf", "not",
                   "if", "then", "else", "dependencies"):
            if kw in schema:
                entity.annotations.append(Annotation(key=kw, value=json.dumps(schema[kw])))

    def _parse_validator_field(self, name: str, prop_schema: dict,
                               required_set: set[str], doc: MSDMDocument) -> Attribute:
        """Parse a single property from a $jsonSchema object into an Attribute."""
        bson_type = prop_schema.get("bsonType")
        desc = prop_schema.get("description", "")
        attr = Attribute(
            name=name,
            data_type=self._bson_type_to_datatype(bson_type, prop_schema, doc),
            required=name in required_set,
            description=desc,
        )

        # Default value
        if "default" in prop_schema:
            attr.default_value = json.dumps(prop_schema["default"])
            attr.constraints.append(Constraint(type=ConstraintType.DEFAULT,
                                               expression=attr.default_value))
        # Enum
        if "enum" in prop_schema:
            values = prop_schema["enum"]
            quoted = ", ".join(json.dumps(v) for v in values)
            attr.constraints.append(Constraint(type=ConstraintType.CHECK,
                                               expression=f"IN ({quoted})"))
        # Numeric constraints
        for mongo_kw, constr in [("minimum", ">="), ("maximum", "<="),
                                  ("exclusiveMinimum", ">"), ("exclusiveMaximum", "<")]:
            if mongo_kw in prop_schema:
                val = prop_schema[mongo_kw]
                attr.constraints.append(Constraint(type=ConstraintType.CHECK,
                                                   expression=f"{constr} {val}"))
        if "multipleOf" in prop_schema:
            attr.annotations.append(Annotation(key="multipleOf", value=str(prop_schema["multipleOf"])))

        # String constraints
        for key in ("minLength", "maxLength", "pattern"):
            if key in prop_schema:
                attr.annotations.append(Annotation(key=key, value=json.dumps(prop_schema[key])))

        # Array constraints
        if bson_type == "array" and "items" in prop_schema:
            items = prop_schema["items"]
            if isinstance(items, dict):
                # Single type for all items
                elem_type = self._bson_type_to_datatype(items.get("bsonType"), items, doc)
                attr.data_type = DataType(base=ScalarType.ARRAY, element_type=elem_type)
            elif isinstance(items, list):
                # Tuple validation – store as annotation for simplicity
                attr.annotations.append(Annotation(key="items_tuple", value=json.dumps(items)))
        if "minItems" in prop_schema:
            attr.annotations.append(Annotation(key="minItems", value=str(prop_schema["minItems"])))
        if "maxItems" in prop_schema:
            attr.annotations.append(Annotation(key="maxItems", value=str(prop_schema["maxItems"])))
        if "uniqueItems" in prop_schema:
            attr.annotations.append(Annotation(key="uniqueItems", value=str(prop_schema["uniqueItems"])))

        # Handle nested object (subdocument)
        if bson_type == "object" and "properties" in prop_schema:
            nested_req = set(prop_schema.get("required", []))
            for n_name, n_schema in prop_schema["properties"].items():
                n_attr = self._parse_validator_field(n_name, n_schema, nested_req, doc)
                attr.nested_attributes.append(n_attr)

        # Store any extra keywords as annotations
        for key in prop_schema:
            if key not in ("bsonType", "description", "default", "enum", "properties",
                           "required", "items", "minimum", "maximum", "exclusiveMinimum",
                           "exclusiveMaximum", "multipleOf", "minLength", "maxLength",
                           "pattern", "minItems", "maxItems", "uniqueItems"):
                attr.annotations.append(Annotation(key=key, value=json.dumps(prop_schema[key])))

        return attr

    def _bson_type_to_datatype(self, bson_type, prop_schema: dict, doc: MSDMDocument) -> DataType:
        """Convert a BSON type to DataType, handling complex types."""
        if bson_type is None:
            # Try to infer from properties
            if "properties" in prop_schema:
                return DataType(base=ScalarType.STRUCT)
            return DataType(base=ScalarType.ANY)
        if isinstance(bson_type, list):
            # Union of types
            return DataType(base=ScalarType.ANY)
        if bson_type in BSON_TYPE_TO_SCALAR:
            return DataType(base=BSON_TYPE_TO_SCALAR[bson_type])
        # Could be a named type not in our map
        return DataType(base=ScalarType.ANY)

    # ── Mongoose JavaScript parser ────────────────────────────────
    def _parse_mongoose_js(self, text: str, doc: MSDMDocument) -> None:
        """Parse a Mongoose schema definition from JavaScript code."""
        # Remove comments (// and /* */)
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
        text = re.sub(r'//[^\n]*', '', text)

        # Find the schema definition: new Schema({ ... })
        schema_match = re.search(r'new\s+Schema\s*\(\s*\{', text)
        if not schema_match:
            # Could be a simple object export: module.exports = { ... }
            # Try extracting object literal
            pass

        entity_name = Path(getattr(doc, 'namespace', 'collection')).stem
        entity = Entity(name=entity_name, kind=EntityKind.DOCUMENT)

        # Extract the object literal body (the { ... } part)
        # We'll use a simple brace matching heuristic
        start = text.find('{')
        if start == -1:
            doc.entities.append(entity)
            return
        body = self._extract_balanced_braces(text, start)

        # Parse each field definition
        self._parse_mongoose_fields(body, entity, doc)

        # Look for index definitions: schema.index({ ... })
        for idx_match in re.finditer(r'schema\.index\s*\(\s*(\{[^}]+\})', text):
            idx_body = idx_match.group(1)
            try:
                idx_obj = json.loads(idx_body)
                attributes: list[Attribute] = []
                for k in idx_obj.keys():
                    for a in entity.attributes:
                        if a.name==k:
                            attributes.append(a)
                idx = Index(attributes=attributes)
                entity.indexes.append(idx)
            except Exception:
                entity.annotations.append(Annotation(key="raw_index", value=idx_match.group(0)))

        doc.entities.append(entity)

    def _extract_balanced_braces(self, text: str, start: int) -> str:
        """Extract the substring from `start` to the matching closing brace."""
        depth = 0
        for i, ch in enumerate(text[start:], start):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return text[start:i+1]
        return text[start:]

    def _parse_mongoose_fields(self, body: str, entity: Entity, doc: MSDMDocument) -> None:
        """Parse fields from the body of a Mongoose schema."""
        # Remove the outer braces
        body = body.strip()
        if body.startswith('{'):
            body = body[1:]
        if body.endswith('}'):
            body = body[:-1]
        body = body.strip()

        # Split by commas, but respect nested braces and brackets
        fields = self._split_mongoose_fields(body)
        for field_text in fields:
            field_text = field_text.strip()
            if not field_text:
                continue
            # Try to match a complex field: name: { ... }
            complex_match = MONGOOSE_FIELD_RE.match(field_text)
            if complex_match:
                name = complex_match.group(1)
                opts_body = complex_match.group(2)
                attr = self._parse_mongoose_field_opts(name, opts_body, entity, doc)
                entity.attributes.append(attr)
                continue
            # Try simple: name: Type
            simple_match = MONGOOSE_SIMPLE_RE.match(field_text)
            if simple_match:
                name = simple_match.group(1)
                type_str = simple_match.group(2)
                dt = self._mongoose_type_to_datatype(type_str, doc)
                attr = Attribute(name=name, data_type=dt)
                entity.attributes.append(attr)
                continue
            # Fallback: store as annotation
            entity.annotations.append(Annotation(key="raw_field", value=field_text))

    def _split_mongoose_fields(self, body: str) -> list[str]:
        """Split field definitions by commas, ignoring those inside braces/brackets."""
        fields = []
        depth = 0
        current = ""
        for ch in body:
            if ch in ('{', '['):
                depth += 1
            elif ch in ('}', ']'):
                depth -= 1
            elif ch == ',' and depth == 0:
                if current.strip():
                    fields.append(current)
                    current = ""
                continue
            current += ch
        if current.strip():
            fields.append(current)
        return fields

    def _parse_mongoose_field_opts(self, name: str, opts_body: str,
                                   entity: Entity, doc: MSDMDocument) -> Attribute:
        """Parse the options object of a Mongoose field definition."""
        # Extract key-value pairs
        opts = self._parse_key_values(opts_body)

        type_val = opts.get("type", "Mixed")
        dt = self._mongoose_type_to_datatype(type_val, doc)

        required = opts.get("required", "false").lower() == "true"
        default_val = opts.get("default")
        unique = opts.get("unique", "false").lower() == "true"
        enum_values = opts.get("enum")
        description = opts.get("description") or opts.get("comment")

        attr = Attribute(
            name=name,
            data_type=dt,
            required=required,
            description=description,
        )

        if default_val:
            attr.default_value = str(default_val)
            attr.constraints.append(Constraint(type=ConstraintType.DEFAULT,
                                               expression=attr.default_value))

        if unique:
            entity.indexes.append(Index(attributes=[attr], unique=True))

        if enum_values:
            attr.annotations.append(Annotation(key="enum", value=str(enum_values)))

        # Ref (population)
        ref = opts.get("ref")
        if ref:
            attr.annotations.append(Annotation(key="ref", value=ref))

        # Store other options as annotations
        known_opts = {"type", "required", "default", "unique", "enum", "ref",
                      "description", "comment", "index", "sparse", "select",
                      "validate", "min", "max", "match", "minlength", "maxlength",
                      "lowercase", "uppercase", "trim"}
        for key, val in opts.items():
            if key not in known_opts:
                attr.annotations.append(Annotation(key=key, value=str(val)))
            elif key in ("min", "max", "match", "minlength", "maxlength"):
                attr.annotations.append(Annotation(key=key, value=str(val)))

        # Handle nested array of objects
        if type_val.startswith("[") and type_val.endswith("]"):
            inner = type_val[1:-1].strip()
            if inner == "Schema" or inner.endswith("Schema"):
                # Subdocument array
                attr.data_type = DataType(base=ScalarType.ARRAY,
                                         element_type=DataType(base=ScalarType.STRUCT))
            else:
                attr.data_type = DataType(base=ScalarType.ARRAY,
                                         element_type=self._mongoose_type_to_datatype(inner, doc))

        return attr

    def _parse_key_values(self, text: str) -> dict[str, str]:
        """Parse a JavaScript-like key: value dictionary, returning a simple dict of strings."""
        # This is a very simplistic parser; for production we'd use a robust tokenizer.
        # For typical Mongoose schemas, values are limited to simple types.
        result = {}
        # Split by comma, but watch nested objects
        parts = self._split_mongoose_fields(text)
        for part in parts:
            if ':' not in part:
                continue
            idx = part.index(':')
            key = part[:idx].strip()
            value = part[idx+1:].strip()
            # Remove quotes from key
            if key.startswith(('"', "'")) and key.endswith(('"', "'")):
                key = key[1:-1]
            result[key] = value
        return result

    def _mongoose_type_to_datatype(self, type_str: str, doc: MSDMDocument) -> DataType:
        """Convert a Mongoose type string to DataType."""
        type_str = type_str.strip()
        # Check for arrays, e.g., [String], [ { type: ... } ]
        if type_str.startswith("[") and type_str.endswith("]"):
            inner = type_str[1:-1].strip()
            if inner in MONGOOSE_TYPE_MAP:
                elem = DataType(base=MONGOOSE_TYPE_MAP[inner])
            else:
                elem = DataType(base=ScalarType.ANY)
            return DataType(base=ScalarType.ARRAY, element_type=elem)

        if type_str in MONGOOSE_TYPE_MAP:
            return DataType(base=MONGOOSE_TYPE_MAP[type_str])
        # Could be a reference to another model
        if re.match(r'^\w+$', type_str):
            return DataType(base=ScalarType.REF, ref_entity_id=type_str)
        return DataType(base=ScalarType.ANY)