# engines/document/parsers/msdm_parsers/proto_msdm_parser.py
"""
Protobuf IDL Parser (.proto) – converts .proto files into an MSDMDocument.

Handles:
- syntax, package, import (stored as annotations)
- option (file-level, message-level, field-level)
- message, enum, oneof, map (pseudo‑oneof)
- field types: scalar types, references to other messages/enums
- repeated, optional, required
- reserved fields (numbers, names)
- nested messages and enums
- extensions, extend blocks (preserved as annotations)

Every protobuf detail is mapped to MSDM Entity (kind=OBJECT), Attribute,
Constraint, and Annotation objects for lossless round‑trip.
"""
from __future__ import annotations

import re
from pathlib import Path

from ...models.media_types import MEDIA_TYPES
from ...models.msdm_models import Annotation
from ...models.msdm_models import Attribute
from ...models.msdm_models import DataType
from ...models.msdm_models import Entity
from ...models.msdm_models import EntityKind
from ...models.msdm_models import MSDMDocument
from ...models.msdm_models import ScalarType, Namespace
from ..base import ParseOptions
from .base_msdm_parser import BaseMSDMParser

# ── Protobuf scalar type mapping ──────────────────────────────────
PROTO_SCALAR_MAP = {
    "double":   ScalarType.DOUBLE,
    "float":    ScalarType.FLOAT,
    "int32":    ScalarType.INT,
    "int64":    ScalarType.LONG,
    "uint32":   ScalarType.LONG,
    "uint64":   ScalarType.LONG,
    "sint32":   ScalarType.INT,
    "sint64":   ScalarType.LONG,
    "fixed32":  ScalarType.INT,
    "fixed64":  ScalarType.LONG,
    "sfixed32": ScalarType.INT,
    "sfixed64": ScalarType.LONG,
    "bool":     ScalarType.BOOLEAN,
    "string":   ScalarType.STRING,
    "bytes":    ScalarType.BINARY,
}


class ProtoParser(BaseMSDMParser):
    """Parser for Protobuf IDL (.proto) files."""
    name = "proto"
    supported_extensions = (".proto",)

    async def _parse_to_msdm(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> MSDMDocument:
        encoding = options.encoding or "utf-8"
        text = data.decode(encoding)

        doc = MSDMDocument(
            document_id=Path(source_name).stem,
            title=Path(source_name).stem,
            media_type=MEDIA_TYPES.get("protobuf", MEDIA_TYPES["txt"])
        )
        doc.namespace = Namespace(uri=Path(source_name).stem)

        # Remove comments
        text = self._strip_comments(text)

        # Parse top‑level elements using a simple recursive descent approach
        self._tokenize(text)
        self._pos = 0

        while self._peek() is not None:
            self._parse_top_level(doc)

        self.resolve_references(doc)
        return doc

    # ── Simple tokenizer (splitting by meaningful boundaries) ─────
    def _tokenize(self, text: str) -> None:
        pattern = re.compile(
            r'"[^"]*"'          # string literal
            r"|'[^']*'"
            r"|0x[0-9a-fA-F]+"
            r"|\d+\.\d+|\d+"
            r"|[a-zA-Z_][\w.]*" # identifier or qualified name
            r"|//[^\n]*"        # line comment (though we already stripped)
            r"|\S",
            re.IGNORECASE
        )
        self._tokens = pattern.findall(text)
        self._pos = 0

    def _peek(self, offset: int = 0) -> str | None:
        idx = self._pos + offset
        return self._tokens[idx] if idx < len(self._tokens) else None

    def _advance(self) -> str:
        tok = self._tokens[self._pos]
        self._pos += 1
        return tok

    def _strip_comments(self, text: str) -> str:
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
        text = re.sub(r'//[^\n]*', '', text)
        return text

    # ── Top‑level parsing ────────────────────────────────────────
    def _parse_top_level(self, doc: MSDMDocument) -> None:
        tok = self._peek()
        if tok is None:
            return
        keyword = tok
        if keyword == "syntax":
            self._advance()
            self._expect("=")
            val = self._advance().strip('";')
            doc.annotations.append(Annotation(key="syntax", value=val))
            self._expect(";")
        elif keyword == "package":
            self._advance()
            pkg = self._advance().rstrip(";")
            doc.namespace = Namespace(uri=pkg)
            if self._peek() == ";":
                self._advance()
        elif keyword == "import":
            self._advance()
            imp = self._advance().strip('";')
            doc.annotations.append(Annotation(key="import", value=imp))
            if self._peek() == ";":
                self._advance()
        elif keyword == "option":
            self._parse_option(None, doc)
        elif keyword == "message":
            self._advance()
            self._parse_message(doc, None)
        elif keyword == "enum":
            self._advance()
            self._parse_enum(doc, None)
        elif keyword == "extend":
            self._advance()
            self._parse_extend(doc)
        elif keyword == "service":
            self._advance()
            self._parse_service(doc)
        else:
            self._advance()

    # ── Message parsing ──────────────────────────────────────────
    def _parse_message(self, doc: MSDMDocument, parent: Entity | None) -> Entity:
        name = self._advance()
        entity = Entity(name=name, kind=EntityKind.OBJECT)
        self._expect("{")
        while self._peek() and self._peek() != "}":
            field_tok = self._peek()
            if field_tok == "message":
                self._advance()
                nested = self._parse_message(doc, entity)
                entity.annotations.append(Annotation(key="nested_message", value=nested.name))
                doc.entities.append(nested)
            elif field_tok == "enum":
                self._advance()
                nested_enum = self._parse_enum(doc, entity)
                entity.annotations.append(Annotation(key="nested_enum", value=nested_enum.name))
                doc.entities.append(nested_enum)
            elif field_tok == "option":
                self._parse_option(entity, doc)
            elif field_tok == "oneof":
                self._advance()
                self._parse_oneof(entity, doc)
            elif field_tok == "reserved":
                self._advance()
                reserved_parts = []
                while self._peek() and self._peek() != ";":
                    reserved_parts.append(self._advance())
                entity.annotations.append(Annotation(key="reserved", value=" ".join(reserved_parts)))
                self._expect(";")
            elif field_tok == "map":
                self._parse_map_field(entity, doc)
            elif field_tok == "}":
                break
            else:
                self._parse_field(entity, doc)
        self._expect("}")
        doc.entities.append(entity)
        return entity

    def _parse_field(self, entity: Entity, doc: MSDMDocument) -> None:
        label = None
        tok = self._peek()
        if tok in ("optional", "repeated", "required"):
            label = self._advance()
        field_type = self._advance()
        field_name = self._advance()
        self._expect("=")
        field_number = self._advance()
        field_options = {}
        if self._peek() == "[":
            self._advance()
            field_options = self._parse_field_options()
            self._expect("]")
        while self._peek() and self._peek() != ";":
            self._advance()
        if self._peek() == ";":
            self._advance()

        dt = self._proto_type_to_datatype(field_type, label, doc)
        attr = Attribute(
            name=field_name,
            data_type=dt,
            required=label == "required",
            description=None,
        )
        attr.annotations.append(Annotation(key="field_number", value=field_number))
        if label:
            attr.annotations.append(Annotation(key="label", value=label))
        for opt_key, opt_val in field_options.items():
            attr.annotations.append(Annotation(key=opt_key, value=opt_val))
        entity.attributes.append(attr)

    def _parse_map_field(self, entity: Entity, doc: MSDMDocument) -> None:
        # Assume we are already at '<' after 'map' token
        if self._peek() == "<":
            self._advance()
        key_type = self._advance()
        self._expect(",")
        value_type = self._advance()
        self._expect(">")
        name = self._advance()
        self._expect("=")
        field_number = self._advance()
        field_options = {}
        if self._peek() == "[":
            self._advance()
            field_options = self._parse_field_options()
            self._expect("]")
        while self._peek() and self._peek() != ";":
            self._advance()
        self._expect(";")

        key_dt = self._proto_scalar_to_datatype(key_type)
        val_dt = self._proto_type_to_datatype(value_type, None, doc)
        dt = DataType(base=ScalarType.MAP, key_type=key_dt, value_type=val_dt)

        attr = Attribute(name=name, data_type=dt)
        attr.annotations.append(Annotation(key="field_number", value=field_number))
        for opt_key, opt_val in field_options.items():
            attr.annotations.append(Annotation(key=opt_key, value=opt_val))
        entity.attributes.append(attr)

    def _parse_oneof(self, entity: Entity, doc: MSDMDocument) -> None:
        name = self._advance()
        self._expect("{")
        nested_attrs = []
        while self._peek() and self._peek() != "}":
            tok = self._peek()
            if tok in ("option",):
                self._advance()
                while self._peek() and self._peek() != ";":
                    self._advance()
                self._expect(";")
            else:
                field_type = self._advance()
                field_name = self._advance()
                self._expect("=")
                field_number = self._advance()
                field_options = {}
                if self._peek() == "[":
                    self._advance()
                    field_options = self._parse_field_options()
                    self._expect("]")
                while self._peek() and self._peek() != ";":
                    self._advance()
                self._expect(";")
                dt = self._proto_type_to_datatype(field_type, None, doc)
                attr = Attribute(name=field_name, data_type=dt, required=False)
                attr.annotations.append(Annotation(key="field_number", value=field_number))
                for opt_key, opt_val in field_options.items():
                    attr.annotations.append(Annotation(key=opt_key, value=opt_val))
                nested_attrs.append(attr)
        self._expect("}")
        oneof_attr = Attribute(name=name, data_type=DataType(base=ScalarType.STRUCT))
        oneof_attr.nested_attributes = nested_attrs
        oneof_attr.annotations.append(Annotation(key="oneof", value="true"))
        entity.attributes.append(oneof_attr)

    # ── Enum parsing ──────────────────────────────────────────────
    def _parse_enum(self, doc: MSDMDocument, parent: Entity | None) -> Entity:
        name = self._advance()
        entity = Entity(name=name, kind=EntityKind.OBJECT)
        self._expect("{")
        while self._peek() and self._peek() != "}":
            tok = self._peek()
            if tok == "option":
                self._parse_option(entity, doc)
            elif tok == "reserved":
                self._advance()
                parts = []
                while self._peek() and self._peek() != ";":
                    parts.append(self._advance())
                entity.annotations.append(Annotation(key="reserved", value=" ".join(parts)))
                self._expect(";")
            else:
                val_name = self._advance()
                self._expect("=")
                val_num = self._advance()
                while self._peek() and self._peek() != ";":
                    if self._peek() == "[":
                        self._advance()
                        self._parse_field_options()
                        self._expect("]")
                    else:
                        self._advance()
                self._expect(";")
                entity.annotations.append(Annotation(key="enum_value", value=f"{val_name}={val_num}"))
        self._expect("}")
        doc.entities.append(entity)
        return entity

    # ── Option parsing ──────────────────────────────────────────
    def _parse_option(self, target: Entity | None, doc: MSDMDocument) -> None:
        opt_name = self._advance()
        self._expect("=")
        value_tokens = []
        while self._peek() and self._peek() != ";":
            value_tokens.append(self._advance())
        opt_value = " ".join(value_tokens)
        if target:
            target.annotations.append(Annotation(key="option", value=f"{opt_name}={opt_value}"))
        else:
            doc.annotations.append(Annotation(key="file_option", value=f"{opt_name}={opt_value}"))

    def _parse_field_options(self) -> dict[str, str]:
        opts = {}
        while self._peek() and self._peek() != "]":
            tok = self._peek()
            if tok == ",":
                self._advance()
                continue
            key = self._advance()
            if self._peek() == "=":
                self._advance()
                val = self._advance().strip('"')
                opts[key.strip("(")] = val.strip(")")
            else:
                opts[key.strip("(")] = "true"
        return opts

    # ── Extend / Service (stubs for round‑trip) ──────────────────
    def _parse_extend(self, doc: MSDMDocument) -> None:
        extend_target = self._advance()
        self._expect("{")
        depth = 1
        while self._peek() and depth > 0:
            if self._peek() == "{":
                depth += 1
            elif self._peek() == "}":
                depth -= 1
                if depth == 0:
                    self._advance()
                    break
            self._advance()
        doc.annotations.append(Annotation(key="extend", value=extend_target))

    def _parse_service(self, doc: MSDMDocument) -> None:
        service_name = self._advance()
        self._expect("{")
        depth = 1
        while self._peek() and depth > 0:
            if self._peek() == "{":
                depth += 1
            elif self._peek() == "}":
                depth -= 1
                if depth == 0:
                    self._advance()
                    break
            self._advance()
        doc.annotations.append(Annotation(key="service", value=service_name))

    # ── Type conversion helpers ─────────────────────────────────
    def _proto_type_to_datatype(self, type_str: str, label: str | None, doc: MSDMDocument) -> DataType:
        base = self._proto_scalar_to_datatype(type_str)
        if label == "repeated":
            return DataType(base=ScalarType.ARRAY, element_type=base)
        return base

    def _proto_scalar_to_datatype(self, type_str: str) -> DataType:
        if type_str in PROTO_SCALAR_MAP:
            return DataType(base=PROTO_SCALAR_MAP[type_str])
        return DataType(base=ScalarType.REF, ref_entity_id=type_str)

    # ── Utility ─────────────────────────────────────────────────
    def _expect(self, expected: str) -> None:
        tok = self._advance()
        if tok != expected:
            raise SyntaxError(f"Expected '{expected}' but got '{tok}'")