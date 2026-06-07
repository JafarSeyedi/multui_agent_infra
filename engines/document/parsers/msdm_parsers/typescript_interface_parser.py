# engines/document/parsers/msdm_parsers/typescript_interface_parser.py
"""
TypeScript Interface Parser – extracts MSDM entities from .ts files.

Supports:
- export declarations
- interface, type alias, enum, class
- properties with modifiers, optional, type annotation, default value
- complex types: primitives, arrays, generics (Array, Record), references
- union, intersection, tuple types (stored as annotations)
- method signatures (stored as annotations)
- reference resolution after full parse
"""
from __future__ import annotations

import re
import ast
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from ...models.media_types import MEDIA_TYPES
from ...models.msdm_models import (
    Annotation, Attribute, Constraint, ConstraintType, DataType,
    Entity, EntityKind, MSDMDocument, ScalarType, Namespace
)
from ..base import ParseOptions
from .base_msdm_parser import BaseMSDMParser

# TypeScript primitive mapping
TS_PRIMITIVE_MAP = {
    "string": ScalarType.STRING,
    "number": ScalarType.FLOAT,
    "bigint": ScalarType.LONG,
    "boolean": ScalarType.BOOLEAN,
    "symbol": ScalarType.STRING,
    "undefined": ScalarType.ANY,
    "null": ScalarType.ANY,
    "void": ScalarType.ANY,
    "any": ScalarType.ANY,
    "unknown": ScalarType.ANY,
    "never": ScalarType.ANY,
    "object": ScalarType.STRUCT,
    "Date": ScalarType.TIMESTAMP,
    "ArrayBuffer": ScalarType.BINARY,
    "DataView": ScalarType.BINARY,
    "Int8Array": ScalarType.BINARY,
    "Uint8Array": ScalarType.BINARY,
    "Blob": ScalarType.BINARY,
    "File": ScalarType.STRUCT,
    "FormData": ScalarType.STRUCT,
    "URLSearchParams": ScalarType.STRUCT,
    "RegExp": ScalarType.STRING,
    "Error": ScalarType.STRUCT,
}

# Tokenizer
TOKEN_SPEC = [
    ("BLOCK_COMMENT", r"/\*[\s\S]*?\*/"),
    ("LINE_COMMENT", r"//[^\n]*"),
    ("STRING", r"\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*'|`(?:[^`\\]|\\.)*`"),
    ("TEMPLATE_HEAD", r"`(?:[^`\\]|\\.)*\$\{"),
    ("NUMBER", r"\b\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b"),
    ("KEYWORD", r"\b(?:interface|type|enum|class|extends|implements|readonly|public|"
                r"private|protected|static|abstract|export|import|from|as|default|"
                r"true|false|null|undefined|new|typeof|keyof|infer|is|extends|"
                r"module|namespace|declare|abstract|async|await|yield|"
                r"string|number|bigint|boolean|symbol|void|any|unknown|never|object"
                r")\b"),
    ("IDENTIFIER", r"[a-zA-Z_$][\w$]*"),
    ("PUNCTUATION", r"[{}()\[\];,:=|&<>?.]+"),
    ("WHITESPACE", r"\s+"),
    ("UNEXPECTED", r"."),
]
TOKEN_RE = re.compile("|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPEC), re.DOTALL)


class _Token:
    __slots__ = ("kind", "value", "pos")
    def __init__(self, kind: str, value: str, pos: int):
        self.kind = kind
        self.value = value
        self.pos = pos


def _tokenize(text: str) -> list[_Token]:
    tokens = []
    for m in TOKEN_RE.finditer(text):
        kind = m.lastgroup
        if not kind:
            continue
        value = m.group()
        if kind in ("WHITESPACE", "BLOCK_COMMENT", "LINE_COMMENT"):
            continue
        tokens.append(_Token(kind, value, m.start()))
    return tokens


class TypeScriptInterfaceParser(BaseMSDMParser):
    name = "typescript_interface"
    supported_extensions = (".ts",)

    async def _parse_to_msdm(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> MSDMDocument:
        encoding = options.encoding or "utf-8"
        text = data.decode(encoding)

        doc = MSDMDocument(
            title=source_name,
            document_id=source_name,
            media_type=MEDIA_TYPES.get("typescript_interface", MEDIA_TYPES["txt"])
        )
        doc.namespace = Namespace(uri=Path(source_name).stem)
        
        self._tokens = _tokenize(text)
        self._pos = 0
        self._entity_names: set[str] = set()
        self._methods: Dict[str, List[Dict[str, Any]]] = {}

        while self._pos < len(self._tokens):
            self._parse_declaration(doc)

        for entity in doc.entities:
            if entity.name in self._methods:
                for method in self._methods[entity.name]:
                    entity.annotations.append(Annotation(
                        key="method",
                        value=json.dumps(method)
                    ))

        self.resolve_references(doc)
        return doc

    # ------------------------------------------------------------------
    # Helpers with safe peek
    # ------------------------------------------------------------------
    def _peek(self) -> Optional[_Token]:
        if self._pos < len(self._tokens):
            return self._tokens[self._pos]
        return None

    def _peek_value(self) -> str | None:
        t = self._peek()
        return t.value if t else None

    def _peek_kind(self) -> str | None:
        t = self._peek()
        return t.kind if t else None

    def _advance(self) -> _Token:
        tok = self._tokens[self._pos]
        self._pos += 1
        return tok

    def _expect(self, kind: str, value: str | None = None) -> _Token:
        tok = self._advance()
        if tok.kind != kind or (value and tok.value != value):
            raise SyntaxError(f"Expected {kind}('{value}') but got {tok.kind}('{tok.value}')")
        return tok

    # ------------------------------------------------------------------
    # Top‑level declarations
    # ------------------------------------------------------------------
    def _parse_declaration(self, doc: MSDMDocument) -> None:
        modifiers = []
        while self._peek() and self._peek_value() in ("export", "declare", "abstract", "default"):
            modifiers.append(self._advance().value)

        tok = self._peek()
        if not tok:
            return
        if tok.value == "interface":
            self._advance()
            self._parse_interface(doc, modifiers)
        elif tok.value == "type":
            self._advance()
            self._parse_type_alias(doc, modifiers)
        elif tok.value == "enum":
            self._advance()
            self._parse_enum(doc, modifiers)
        elif tok.value == "class":
            self._advance()
            self._parse_class(doc, modifiers)
        else:
            self._advance()

    # ------------------------------------------------------------------
    # Interface
    # ------------------------------------------------------------------
    def _parse_interface(self, doc: MSDMDocument, modifiers: list[str]) -> Entity:
        name = self._expect("IDENTIFIER").value
        # Skip generic parameters
        if self._peek_value() == "<":
            self._advance()
            depth = 1
            while depth > 0 and self._pos < len(self._tokens):
                t = self._advance()
                if t.value == "<":
                    depth += 1
                elif t.value == ">":
                    depth -= 1

        entity = Entity(name=name, kind=EntityKind.OBJECT)
        entity.annotations.append(Annotation(key="ts_type", value="interface"))
        if "export" in modifiers:
            entity.annotations.append(Annotation(key="exported", value="true"))

        # extends
        if self._peek_value() == "extends":
            self._advance()
            base_names: list[str] = []
            while True:
                base = self._parse_type_reference()
                if base and base.ref_entity_id:
                    base_names.append(base.ref_entity_id)
                if self._peek_value() == ",":
                    self._advance()
                else:
                    break
            # entity.implements.extend(base_names)
            # Store string references in temporary dict; do NOT assign to entity.implements yet
            entity.implements_ref_ids.extend(base_names)

        self._expect("PUNCTUATION", "{")
        while self._peek() and self._peek_value() != "}":
            self._parse_interface_member(entity, name)
        self._expect("PUNCTUATION", "}")

        doc.entities.append(entity)
        self._entity_names.add(name)
        return entity

    def _parse_interface_member(self, entity: Entity, entity_name: str) -> None:
        tok = self._peek()
        if not tok:
            return

        # Skip index signatures and store raw
        if tok.value in ("[", "("):
            raw = ""
            while self._peek() and self._peek_value() not in (";", "}"):
                raw += self._advance().value + " "
            entity.annotations.append(Annotation(key="raw_member", value=raw.strip()))
            if self._peek() and self._peek_value() == ";":
                self._advance()
            return

        # Modifiers
        modifiers = []
        while self._peek() and self._peek_value() in ("readonly", "public", "private", "protected", "static", "abstract"):
            modifiers.append(self._advance().value)

        # Property name
        prop_name: str | None = None
        peek = self._peek()
        if peek and peek.kind == "IDENTIFIER":
            prop_name = self._advance().value
        elif peek and peek.kind == "STRING":
            prop_name = ast.literal_eval(self._advance().value)
        if not prop_name:
            if self._peek():
                self._advance()
            return

        # Optional
        optional = False
        if self._peek_value() == "?":
            self._advance()
            optional = True

        # Type annotation or method
        if self._peek_value() == ":":
            self._advance()
            attr_type = self._parse_type_expression()
            attr = Attribute(name=prop_name, data_type=attr_type, required=not optional)
            for mod in modifiers:
                attr.annotations.append(Annotation(key="modifier", value=mod))
            # Default value
            if self._peek_value() == "=":
                self._advance()
                default_val = self._parse_expression()
                attr.default_value = default_val
                attr.constraints.append(Constraint(type=ConstraintType.DEFAULT, expression=default_val))
            entity.attributes.append(attr)
            if self._peek_value() in (";", ","):
                self._advance()
        elif self._peek_value() == "(":
            # Method signature
            self._parse_method_signature(entity_name, prop_name, modifiers, optional)
            if self._peek_value() == ";":
                self._advance()
        else:
            # Unknown – skip
            if self._peek():
                self._advance()

    # ------------------------------------------------------------------
    # Type alias
    # ------------------------------------------------------------------
    def _parse_type_alias(self, doc: MSDMDocument, modifiers: list[str]) -> Entity:
        name = self._expect("IDENTIFIER").value
        # Skip generics
        if self._peek_value() == "<":
            self._advance()
            depth = 1
            while depth > 0 and self._pos < len(self._tokens):
                t = self._advance()
                if t.value == "<":
                    depth += 1
                elif t.value == ">":
                    depth -= 1
        self._expect("PUNCTUATION", "=")

        entity = Entity(name=name, kind=EntityKind.OBJECT)
        entity.annotations.append(Annotation(key="ts_type", value="type"))
        if "export" in modifiers:
            entity.annotations.append(Annotation(key="exported", value="true"))

        if self._peek_value() == "{":
            self._advance()
            while self._peek() and self._peek_value() != "}":
                self._parse_interface_member(entity, name)
            self._expect("PUNCTUATION", "}")
        else:
            type_expr = self._parse_type_expression()
            entity.annotations.append(Annotation(key="type_alias", value=repr(type_expr)))
            attr = Attribute(name="value", data_type=DataType(base=ScalarType.ANY))
            attr.annotations.append(Annotation(key="type_alias_detail", value=json.dumps(self._type_to_dict(type_expr))))
            entity.attributes.append(attr)

        doc.entities.append(entity)
        self._entity_names.add(name)
        return entity

    # ------------------------------------------------------------------
    # Enum
    # ------------------------------------------------------------------
    def _parse_enum(self, doc: MSDMDocument, modifiers: list[str]) -> Entity:
        name = self._expect("IDENTIFIER").value
        entity = Entity(name=name, kind=EntityKind.OBJECT)
        entity.annotations.append(Annotation(key="ts_type", value="enum"))
        if "export" in modifiers:
            entity.annotations.append(Annotation(key="exported", value="true"))

        self._expect("PUNCTUATION", "{")
        values = []
        while self._peek() and self._peek_value() != "}":
            member_name = self._expect("IDENTIFIER").value
            member_value = member_name
            if self._peek_value() == "=":
                self._advance()
                member_value = self._parse_expression()
            entity.annotations.append(Annotation(key="enum_member", value=f"{member_name}={member_value}"))
            values.append(member_name)
            if self._peek_value() == ",":
                self._advance()
        self._expect("PUNCTUATION", "}")

        if values:
            attr = Attribute(name="value", data_type=DataType(base=ScalarType.STRING), required=True)
            quoted = ", ".join(repr(v) for v in values)
            attr.constraints.append(Constraint(type=ConstraintType.CHECK, expression=f"IN ({quoted})"))
            entity.attributes.append(attr)

        doc.entities.append(entity)
        self._entity_names.add(name)
        return entity

    # ------------------------------------------------------------------
    # Class
    # ------------------------------------------------------------------
    def _parse_class(self, doc: MSDMDocument, modifiers: list[str]) -> Entity:
        name = self._expect("IDENTIFIER").value
        entity = Entity(name=name, kind=EntityKind.OBJECT)
        entity.annotations.append(Annotation(key="ts_type", value="class"))
        if "export" in modifiers:
            entity.annotations.append(Annotation(key="exported", value="true"))

        # extends
        if self._peek_value() == "extends":
            self._advance()
            base = self._parse_type_reference()
            if base and base.ref_entity_id:
                # entity.extends = base.ref_entity
                # Store string reference; do not assign to entity.extends yet
                self.extends_ref_id = base.ref_entity_id
        # implements
        if self._peek_value() == "implements":
            self._advance()
            impl_names: list[str] = []
            while True:
                iface = self._parse_type_reference()
                if iface and iface.ref_entity_id:
                    impl_names.append(iface.ref_entity_id)
                if self._peek_value() == ",":
                    self._advance()
                else:
                    break
            # entity.implements.extend(impl_names)
            entity.implements_ref_ids.extend(impl_names)

        self._expect("PUNCTUATION", "{")
        while self._peek() and self._peek_value() != "}":
            self._parse_class_member(entity, name)
        self._expect("PUNCTUATION", "}")

        doc.entities.append(entity)
        self._entity_names.add(name)
        return entity

    def _parse_class_member(self, entity: Entity, entity_name: str) -> None:
        tok = self._peek()
        if not tok:
            return
        # Skip modifiers
        while self._peek() and self._peek_value() in ("public", "private", "protected", "static", "readonly", "abstract"):
            self._advance()
        if self._peek() and self._peek_kind() == "IDENTIFIER":
            prop_name = self._advance().value
            optional = False
            if self._peek_value() == "?":
                self._advance()
                optional = True
            if self._peek_value() == ":":
                self._advance()
                dt = self._parse_type_expression()
                attr = Attribute(name=prop_name, data_type=dt, required=not optional)
                entity.attributes.append(attr)
                if self._peek_value() == "=":
                    self._advance()
                    default_val = self._parse_expression()
                    attr.default_value = default_val
                    attr.constraints.append(Constraint(type=ConstraintType.DEFAULT, expression=default_val))
                if self._peek_value() in (";", ","):
                    self._advance()
            elif self._peek_value() == "(":
                self._parse_method_signature(entity_name, prop_name, [], optional)
                if self._peek_value() == ";":
                    self._advance()
            else:
                if self._peek():
                    self._advance()
        else:
            self._advance()

    # ------------------------------------------------------------------
    # Method signature parsing (stored as annotation)
    # ------------------------------------------------------------------
    def _parse_method_signature(self, entity_name: str, method_name: str, modifiers: list[str], optional: bool) -> None:
        self._expect("PUNCTUATION", "(")
        params = []
        while self._peek() and self._peek_value() != ")":
            param_name = None
            if self._peek_kind() == "IDENTIFIER":
                param_name = self._advance().value
            else:
                break
            param_optional = False
            if self._peek_value() == "?":
                self._advance()
                param_optional = True
            param_type = None
            if self._peek_value() == ":":
                self._advance()
                param_type = self._parse_type_expression()
            params.append({
                "name": param_name,
                "optional": param_optional,
                "type": self._type_to_dict(param_type) if param_type else None
            })
            if self._peek_value() == ",":
                self._advance()
        self._expect("PUNCTUATION", ")")
        return_type = None
        if self._peek_value() == ":":
            self._advance()
            return_type = self._parse_type_expression()
        method_info = {
            "name": method_name,
            "modifiers": modifiers,
            "optional": optional,
            "parameters": params,
            "return_type": self._type_to_dict(return_type) if return_type else None
        }
        self._methods.setdefault(entity_name, []).append(method_info)

    # ------------------------------------------------------------------
    # Type expression parsing (supports union, intersection, tuple)
    # ------------------------------------------------------------------
    def _parse_type_expression(self) -> DataType:
        left = self._parse_intersection()
        while self._peek_value() == "|":
            self._advance()
            right = self._parse_intersection()
            dt = DataType(base=ScalarType.ANY)
            _dt_union = {"union": [self._type_to_dict(left), self._type_to_dict(right)]}
            # dt.annotations.append(Annotation(key="union_type", value=json.dumps(_dt_union)))
            left = dt
        return left

    def _parse_intersection(self) -> DataType:
        left = self._parse_array_or_primary()
        while self._peek_value() == "&":
            self._advance()
            right = self._parse_array_or_primary()
            dt = DataType(base=ScalarType.ANY)
            _dt_intersection = {"intersection": [self._type_to_dict(left), self._type_to_dict(right)]}
            # dt.annotations.append(Annotation(key="intersection_type", value=json.dumps(_dt_intersection)))
            left = dt
        return left

    def _parse_array_or_primary(self) -> DataType:
        dt = self._parse_primary_type()
        while self._peek_value() == "[":
            self._advance()
            if self._peek_value() == "]":
                self._advance()
                dt = DataType(base=ScalarType.ARRAY, element_type=dt)
            else:
                tuple_types = []
                while self._peek() and self._peek_value() != "]":
                    tuple_types.append(self._parse_type_expression())
                    if self._peek_value() == ",":
                        self._advance()
                self._expect("PUNCTUATION", "]")
                dt = DataType(base=ScalarType.ANY)
                _dt_tuple = {"tuple": [self._type_to_dict(tt) for tt in tuple_types]}
                # dt.annotations.append(Annotation(key="tuple_type", value=json.dumps(_dt_tuple)))
        return dt

    def _parse_primary_type(self) -> DataType:
        tok = self._peek()
        if not tok:
            return DataType(base=ScalarType.ANY)

        if tok.value == "(":
            self._advance()
            dt = self._parse_type_expression()
            self._expect("PUNCTUATION", ")")
            return dt

        if tok.kind in ("STRING", "NUMBER"):
            self._advance()
            if tok.kind == "STRING":
                return DataType(base=ScalarType.STRING)
            else:
                return DataType(base=ScalarType.FLOAT)

        if tok.kind in ("IDENTIFIER", "KEYWORD"):
            name = self._advance().value
            # Generic
            if self._peek_value() == "<":
                self._advance()
                inner_tokens: list[_Token] = []
                depth = 1
                while depth > 0 and self._pos < len(self._tokens):
                    t = self._peek()
                    if not t:
                        break
                    if t.value == "<":
                        depth += 1
                    elif t.value == ">":
                        depth -= 1
                    if depth > 0:
                        inner_tokens.append(self._advance())
                    else:
                        self._advance()
                        break
                if name == "Array" and len(inner_tokens) == 1:
                    elem_dt = self._parse_single_type_token(inner_tokens[0])
                    return DataType(base=ScalarType.ARRAY, element_type=elem_dt)
                if name == "Record" and len(inner_tokens) == 2:
                    key_dt = self._parse_single_type_token(inner_tokens[0])
                    val_dt = self._parse_single_type_token(inner_tokens[1])
                    return DataType(base=ScalarType.MAP, key_type=key_dt, value_type=val_dt)
                dt = DataType(base=ScalarType.ANY)
                # dt.annotations.append(Annotation(key="generic", value=json.dumps({"name": name, "args": [self._type_to_dict(self._parse_single_type_token(it)) for it in inner_tokens]})))
                return dt

            if name.lower() in TS_PRIMITIVE_MAP:
                return DataType(base=TS_PRIMITIVE_MAP[name.lower()])
            return DataType(base=ScalarType.REF, ref_entity_id=name)

        if tok.value == "{":
            self._advance()
            depth = 1
            while self._peek() and depth > 0:
                t = self._advance()
                if t.value == "{":
                    depth += 1
                elif t.value == "}":
                    depth -= 1
            return DataType(base=ScalarType.STRUCT)

        return DataType(base=ScalarType.ANY)

    def _parse_single_type_token(self, token: _Token) -> DataType:
        name = token.value
        if name.lower() in TS_PRIMITIVE_MAP:
            return DataType(base=TS_PRIMITIVE_MAP[name.lower()])
        return DataType(base=ScalarType.REF, ref_entity_id=name)

    def _parse_type_reference(self) -> DataType | None:
        tok = self._peek()
        if tok and tok.kind == "IDENTIFIER":
            self._advance()
            return DataType(base=ScalarType.REF, ref_entity_id=tok.value)
        return None

    def _parse_expression(self) -> str:
        parts = []
        depth = 0
        while self._peek():
            tok = self._peek()
            if not tok:
                break
            if tok.value in (",", ";", "}") and depth == 0:
                break
            if tok.value in ("{", "(", "["):
                depth += 1
            elif tok.value in ("}", ")", "]"):
                depth -= 1
            parts.append(self._advance().value)
        return " ".join(parts).strip()

    def _type_to_dict(self, dt: DataType) -> Dict[str, Any]:
        result: Dict[str, Any] = {"base": dt.base.value}
        if dt.element_type:
            result["element_type"] = self._type_to_dict(dt.element_type)
        if dt.key_type:
            result["key_type"] = self._type_to_dict(dt.key_type)
        if dt.value_type:
            result["value_type"] = self._type_to_dict(dt.value_type)
        if dt.ref_entity_id:
            # dt.ref_entity may be an Entity or a string; convert to name for JSON
            result["ref_entity_id"] = dt.ref_entity_id
        return result
    
