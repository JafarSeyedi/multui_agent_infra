# engines/document/parsers/msdm_parsers/thrift_idl_parser.py
"""
Apache Thrift IDL Parser (.thrift) – converts .thrift files into an MSDMDocument.

Handles:
- include, namespace, cpp_include, php_namespace etc. (stored as document annotations)
- typedef (creates a simple Entity with one attribute)
- enum
- struct (fields with optional/required, default values, type annotations)
- union (like struct but fields are mutually exclusive – stored as a STRUCT with oneof annotation)
- exception (similar to struct)
- service (stored as annotations for round‑trip; MSDM does not model service operations)
- const (stored as annotations)
- comments (stripped)

Every Thrift construct is mapped to MSDM Entity (kind=OBJECT), Attribute, Constraint,
and Annotation objects for lossless round‑trip.
"""

from __future__ import annotations
import re
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

from .base_msdm_parser import BaseMSDMParser
from engines.document.parsers.base import ParseOptions
from engines.document.models.msdm_models import (
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
    Relationship,
)

# ── Thrift primitive type mapping ─────────────────────────────────
THRIFT_TYPE_MAP = {
    "bool":    ScalarType.BOOLEAN,
    "byte":    ScalarType.INT,          # 8-bit integer
    "i8":      ScalarType.INT,
    "i16":     ScalarType.INT,
    "i32":     ScalarType.INT,
    "i64":     ScalarType.LONG,
    "double":  ScalarType.DOUBLE,
    "string":  ScalarType.STRING,
    "binary":  ScalarType.BINARY,
}

# Combined pattern for splitting statements (semicolons) and tokenizing.
# We'll use a more manual approach: split by lines, then group multi‑line blocks.

# Regular expressions
RE_SINGLE_LINE_COMMENT = re.compile(r'//[^\n]*')
RE_BLOCK_COMMENT = re.compile(r'/\*.*?\*/', re.DOTALL)
RE_INCLUDE = re.compile(r'include\s+"([^"]+)"')
RE_NAMESPACE = re.compile(r'namespace\s+(\*|\w+)\s+([\w.]+)')
RE_CPP_INCLUDE = re.compile(r'cpp_include\s+"([^"]+)"')
RE_PHP_NAMESPACE = re.compile(r'php_namespace\s+([\w\\]+)')
RE_TYPEDEF = re.compile(r'typedef\s+([\w.<>, ]+)\s+(\w+)', re.IGNORECASE)
RE_ENUM = re.compile(r'enum\s+(\w+)\s*\{([^}]*)\}', re.IGNORECASE | re.DOTALL)
RE_STRUCT = re.compile(r'(struct|union|exception)\s+(\w+)\s*\{([^}]*)\}', re.IGNORECASE | re.DOTALL)
RE_CONST = re.compile(r'const\s+([\w.<>]+)\s+(\w+)\s*=\s*(.+?);', re.IGNORECASE | re.DOTALL)
RE_SERVICE = re.compile(r'service\s+(\w+)(?:\s+extends\s+(\w+))?\s*\{([^}]*)\}', re.IGNORECASE | re.DOTALL)

# Field inside struct/union/exception:  [field_id:] [required|optional] type name [= default]
RE_FIELD = re.compile(
    r'^\s*(\d+\s*:\s*)?(required|optional)?\s*([\w.<>]+)\s+(\w+)\s*(?:=\s*(.+?))?\s*[;,]?\s*$',
    re.IGNORECASE
)


class ThriftIDLParser(BaseMSDMParser):
    """Parser for Apache Thrift IDL (.thrift)."""
    name = "thrift_idl"
    supported_extensions = (".thrift",)

    async def _parse_to_msdm(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> MSDMDocument:
        encoding = options.encoding or "utf-8"
        text = data.decode(encoding)

        doc = MSDMDocument()
        doc.namespace = Path(source_name).stem

        # Strip comments first
        text = RE_BLOCK_COMMENT.sub('', text)
        text = RE_SINGLE_LINE_COMMENT.sub('', text)

        # Parse line by line, or better: process block statements
        # We'll extract blocks with regex, then process remaining lines for file‑level directives.
        self._process_file_directives(text, doc)

        # Process typedefs
        for m in RE_TYPEDEF.finditer(text):
            self._parse_typedef(m, doc)

        # Process enums
        for m in RE_ENUM.finditer(text):
            self._parse_enum(m, doc)

        # Process structs, unions, exceptions
        for m in RE_STRUCT.finditer(text):
            self._parse_struct(m, doc)

        # Process consts
        for m in RE_CONST.finditer(text):
            self._parse_const(m, doc)

        # Process services (store as annotations)
        for m in RE_SERVICE.finditer(text):
            self._parse_service(m, doc)

        return doc

    def _process_file_directives(self, text: str, doc: MSDMDocument) -> None:
        """Extract include, namespace, cpp_include, php_namespace."""
        for prefix, regex in [
            ("include", RE_INCLUDE),
            ("cpp_include", RE_CPP_INCLUDE),
        ]:
            for m in regex.finditer(text):
                doc.annotations.append(Annotation(key=prefix, value=m.group(1)))

        for m in RE_NAMESPACE.finditer(text):
            lang = m.group(1)
            ns = m.group(2)
            doc.annotations.append(Annotation(key=f"namespace_{lang}", value=ns))
            if lang == '*' or lang == doc.namespace or not doc.namespace:
                doc.namespace = ns  # set global namespace

        for m in RE_PHP_NAMESPACE.finditer(text):
            doc.annotations.append(Annotation(key="php_namespace", value=m.group(1)))

    def _parse_typedef(self, m: re.Match, doc: MSDMDocument) -> None:
        """typedef type name → creates a simple Entity with one attribute."""
        original_type = m.group(1).strip()
        new_name = m.group(2)
        entity = Entity(name=new_name, kind=EntityKind.OBJECT)
        dt = self._thrift_type_to_datatype(original_type, doc)
        attr = Attribute(name="value", data_type=dt, required=True)
        entity.attributes.append(attr)
        doc.entities.append(entity)

    def _parse_enum(self, m: re.Match, doc: MSDMDocument) -> None:
        """Parse an enum block."""
        name = m.group(1)
        body = m.group(2)
        entity = Entity(name=name, kind=EntityKind.OBJECT)
        values = []
        for line in body.splitlines():
            line = line.strip().rstrip(',').strip()
            if not line:
                continue
            # Each line is either VALUE or VALUE = number
            parts = line.split('=')
            val_name = parts[0].strip()
            values.append(val_name)
        # Create a single attribute with a CHECK constraint listing enum values
        attr = Attribute(name="value", data_type=DataType(base=ScalarType.INT), required=True)
        quoted = ", ".join(repr(v) for v in values)
        attr.constraints.append(Constraint(type=ConstraintType.CHECK, expression=f"IN ({quoted})"))
        entity.attributes.append(attr)
        doc.entities.append(entity)

    def _parse_struct(self, m: re.Match, doc: MSDMDocument) -> None:
        """Parse struct/union/exception."""
        kind_str = m.group(1).lower()
        name = m.group(2)
        body = m.group(3)

        entity = Entity(name=name, kind=EntityKind.OBJECT)
        if kind_str == "union":
            entity.annotations.append(Annotation(key="thrift_union", value="true"))
        elif kind_str == "exception":
            entity.annotations.append(Annotation(key="thrift_exception", value="true"))

        # Parse fields
        lines = self._split_field_lines(body)
        for line in lines:
            line = line.strip()
            if not line:
                continue
            field_m = RE_FIELD.match(line)
            if not field_m:
                entity.annotations.append(Annotation(key="raw_field", value=line))
                continue
            # field_id is optional
            field_id = field_m.group(1)  # may be None
            label = field_m.group(2)     # required/optional
            type_str = field_m.group(3).strip()
            field_name = field_m.group(4)
            default_val = field_m.group(5)

            dt = self._thrift_type_to_datatype(type_str, doc)
            attr = Attribute(
                name=field_name,
                data_type=dt,
                required=label == "required",
            )
            if field_id:
                attr.annotations.append(Annotation(key="field_id", value=field_id.strip(': ')))
            if label:
                attr.annotations.append(Annotation(key="label", value=label))
            if default_val:
                attr.default_value = default_val.strip()
                attr.constraints.append(Constraint(type=ConstraintType.DEFAULT,
                                                   expression=attr.default_value))
            entity.attributes.append(attr)

        doc.entities.append(entity)

    def _split_field_lines(self, body: str) -> List[str]:
        """Split the body of a struct into field definitions, handling nested generics."""
        # Simple approach: split by comma/newline, but ensure we don't break inside <...>
        fields = []
        current = ""
        depth = 0
        for ch in body:
            if ch == '<':
                depth += 1
            elif ch == '>':
                depth -= 1
            elif (ch == ',' or ch == '\n') and depth == 0:
                if current.strip():
                    fields.append(current)
                    current = ""
                continue
            current += ch
        if current.strip():
            fields.append(current)
        return fields

    def _parse_const(self, m: re.Match, doc: MSDMDocument) -> None:
        """Store const as document annotation."""
        type_str = m.group(1)
        name = m.group(2)
        value = m.group(3).rstrip(';')
        doc.annotations.append(Annotation(key="const", value=f"{type_str} {name} = {value}"))

    def _parse_service(self, m: re.Match, doc: MSDMDocument) -> None:
        """Store service definition as annotations (round‑trip)."""
        name = m.group(1)
        extends = m.group(2) or ""
        body = m.group(3).strip()
        # We'll preserve the whole block as an annotation; could also parse methods if needed.
        service_def = f"service {name}"
        if extends:
            service_def += f" extends {extends}"
        service_def += " {\n" + body + "\n}"
        doc.annotations.append(Annotation(key="service", value=service_def))

    def _thrift_type_to_datatype(self, type_str: str, doc: MSDMDocument) -> DataType:
        """Convert a Thrift type string to DataType, handling containers and references."""
        type_str = type_str.strip()
        # Handle list<...>, set<...>, map<K,V>
        m = re.match(r'(list|set)<(.+)>', type_str, re.IGNORECASE)
        if m:
            elem = self._thrift_type_to_datatype(m.group(2).strip(), doc)
            return DataType(base=ScalarType.ARRAY, element_type=elem)

        m = re.match(r'map<(.+),(.+)>', type_str, re.IGNORECASE)
        if m:
            key = self._thrift_type_to_datatype(m.group(1).strip(), doc)
            val = self._thrift_type_to_datatype(m.group(2).strip(), doc)
            return DataType(base=ScalarType.MAP, key_type=key, value_type=val)

        # Primitive
        if type_str.lower() in THRIFT_TYPE_MAP:
            return DataType(base=THRIFT_TYPE_MAP[type_str.lower()])
        # Otherwise, it's a reference to another struct/enum/typedef
        return DataType(base=ScalarType.REF, ref_entity=type_str)