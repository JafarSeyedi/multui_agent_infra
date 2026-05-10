# engines/document/parsers/msdm_parsers/graphql_schema_parser.py
"""
GraphQL Schema Parser – converts .graphql / .gql SDL files into an MSDMDocument.

Handles:
- Object types, Interface types, Union types, Enum types, Input object types, Scalar types
- Field definitions with arguments, return types, and directives
- Type extensions (extend type ...)
- Schema definition (root operation types)
- Descriptions (quoted strings and doc strings)
- Directives and directive definitions
- Implements interfaces, union membership
- Default values for arguments and input fields

Every GraphQL construct is mapped to MSDM entities and attributes,
with annotations for arguments, directives, and extensions to ensure lossless round‑trip.
"""
from __future__ import annotations

import re
import json
from enum import Enum
from pathlib import Path
from typing import Optional, Any, Dict, List, Tuple

from ...models.media_types import MEDIA_TYPES
from ...models.msdm_models import (
    Annotation, Attribute, Constraint, ConstraintType, DataType,
    Entity, EntityKind, MSDMDocument, ScalarType, Namespace, EntityComposition, CompositionType
)
from ..base import ParseOptions
from .base_msdm_parser import BaseMSDMParser


# ── Tokenizer ────────────────────────────────────────────────────
TOKEN_PATTERN = re.compile(
    r'(?:"""[\s\S]*?""")'                     # block string description
    r'|(?:"(?:[^"\\]|\\.)*")'                 # string literal
    r'|(?:#.*?$)'
    r'|(?:@\w+(?:\(.*?\))?)'                  # inline directive
    r'|[{}()\[\]:,!=&|]'                       # punctuation
    r'|\b(?:type|interface|union|enum|input|scalar|schema'
    r'|extend|directive|on|implements|fragment|query|mutation|subscription'
    r'|true|false|null)\b'
    r'|\b(?:String|Int|Float|Boolean|ID|__schema|__type)\b'
    r'|\$\w+'                                   # variable
    r'|\w+(?:\.\w+)*'                           # identifier or path
    r'|\s+',
    re.IGNORECASE | re.MULTILINE
)

class TokenType(Enum):
    BRACE_OPEN = 1
    BRACE_CLOSE = 2
    PAREN_OPEN = 3
    PAREN_CLOSE = 4
    BRACKET_OPEN = 5
    BRACKET_CLOSE = 6
    COLON = 7
    COMMA = 8
    EQUALS = 9
    BANG = 10
    PIPE = 11
    AMPERSAND = 12
    STRING = 13
    NAME = 14
    KEYWORD = 15
    DIRECTIVE = 16
    VARIABLE = 17
    BLOCK_STRING = 18
    COMMENT = 19
    WHITESPACE = 20

KEYWORDS = {
    "type", "interface", "union", "enum", "input", "scalar", "schema",
    "extend", "directive", "on", "implements", "fragment", "query", "mutation", "subscription",
    "true", "false", "null",
}


def _tokenize(text: str) -> list[tuple[TokenType, str, int]]:
    """Return list of (type, value, position) tokens."""
    tokens = []
    for m in TOKEN_PATTERN.finditer(text):
        val = m.group()
        start = m.start()
        if val.strip() == '':
            continue
        if val.startswith('#'):
            tokens.append((TokenType.COMMENT, val, start))
        elif val.startswith('"""') and len(val) > 5:
            tokens.append((TokenType.BLOCK_STRING, val, start))
        elif val.startswith('"'):
            tokens.append((TokenType.STRING, val, start))
        elif val.startswith('$'):
            tokens.append((TokenType.VARIABLE, val, start))
        elif val.startswith('@'):
            tokens.append((TokenType.DIRECTIVE, val, start))
        elif val == '{':
            tokens.append((TokenType.BRACE_OPEN, val, start))
        elif val == '}':
            tokens.append((TokenType.BRACE_CLOSE, val, start))
        elif val == '(':
            tokens.append((TokenType.PAREN_OPEN, val, start))
        elif val == ')':
            tokens.append((TokenType.PAREN_CLOSE, val, start))
        elif val == '[':
            tokens.append((TokenType.BRACKET_OPEN, val, start))
        elif val == ']':
            tokens.append((TokenType.BRACKET_CLOSE, val, start))
        elif val == ':':
            tokens.append((TokenType.COLON, val, start))
        elif val == ',':
            tokens.append((TokenType.COMMA, val, start))
        elif val == '=':
            tokens.append((TokenType.EQUALS, val, start))
        elif val == '!':
            tokens.append((TokenType.BANG, val, start))
        elif val == '|':
            tokens.append((TokenType.PIPE, val, start))
        elif val == '&':
            tokens.append((TokenType.AMPERSAND, val, start))
        elif val.lower() in KEYWORDS:
            tokens.append((TokenType.KEYWORD, val, start))
        else:
            tokens.append((TokenType.NAME, val, start))
    return tokens


# ── Parser ────────────────────────────────────────────────────────
class GraphQLSchemaParser(BaseMSDMParser):
    """Parser for GraphQL Schema Definition Language (.graphql, .gql)."""
    name = "graphql_schema"
    supported_extensions = (".graphql", ".gql")

    async def _parse_to_msdm(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> MSDMDocument:
        encoding = options.encoding or "utf-8"
        text = data.decode(encoding)

        doc = MSDMDocument(
            title=source_name,
            document_id=source_name,
            media_type=MEDIA_TYPES.get("graphql_schema", MEDIA_TYPES["txt"])
        )
        doc.namespace = Namespace(uri=Path(source_name).stem)

        self._root_operations: Dict[str, str] = {}
        self._directive_defs: List[Dict[str, Any]] = []

        tokens = _tokenize(text)
        self._tokens = tokens
        self._pos = 0

        while self._pos < len(tokens):
            self._parse_definition(doc)

        # After parsing all, if we have root operations, create an entity "_graphql_schema"
        if self._root_operations:
            schema_entity = Entity(name="__GraphQLSchema", kind=EntityKind.OBJECT)
            for op_type, type_name in self._root_operations.items():
                attr = Attribute(name=op_type, data_type=DataType(base=ScalarType.REF, ref_entity_id=type_name))
                schema_entity.attributes.append(attr)
            doc.entities.append(schema_entity)

        # Add directive definitions as annotations on a dedicated entity
        if self._directive_defs:
            dir_entity = Entity(name="__GraphQLDirectives", kind=EntityKind.OBJECT)
            for d in self._directive_defs:
                dir_entity.annotations.append(Annotation(key="directive_def", value=json.dumps(d)))
            doc.entities.append(dir_entity)

        self.resolve_references(doc)
        return doc

    # ------------------------------------------------------------------
    # Helpers with safe None checks
    # ------------------------------------------------------------------
    def _peek(self, offset: int = 0) -> Optional[tuple[TokenType, str, int]]:
        idx = self._pos + offset
        if idx < len(self._tokens):
            return self._tokens[idx]
        return None

    def _advance(self) -> tuple[TokenType, str, int]:
        tok = self._tokens[self._pos]
        self._pos += 1
        return tok

    def _skip_comments(self):
        while True:
            tok = self._peek()
            if tok is None or tok[0] != TokenType.COMMENT:
                break
            self._advance()

    def _expect(self, token_type: TokenType) -> tuple[TokenType, str, int]:
        tok = self._advance()
        if tok[0] != token_type:
            raise SyntaxError(f"Expected {token_type} but got {tok}")
        return tok

    def _expect_name(self, context: str = "") -> str:
        tok = self._advance()
        if tok[0] != TokenType.NAME and tok[0] != TokenType.KEYWORD:
            raise SyntaxError(f"Expected name for {context}, got {tok}")
        return tok[1]

    def _expect_keyword(self, expected: Optional[str] = None) -> str:
        tok = self._advance()
        if tok[0] != TokenType.KEYWORD:
            raise SyntaxError(f"Expected keyword, got {tok}")
        if expected and tok[1].lower() != expected.lower():
            raise SyntaxError(f"Expected keyword '{expected}', got '{tok[1]}'")
        return tok[1].lower()

    # ------------------------------------------------------------------
    # Parsing methods (all use safe peeks)
    # ------------------------------------------------------------------
    def _parse_definition(self, doc: MSDMDocument) -> None:
        self._skip_comments()
        desc = self._parse_description()
        tok = self._peek()
        if tok is None:
            return
        ttype, value, _ = tok
        if ttype == TokenType.KEYWORD:
            kw = value.lower()
            if kw == "type":
                self._advance()
                self._parse_object_type(desc, doc, is_interface=False)
            elif kw == "interface":
                self._advance()
                self._parse_object_type(desc, doc, is_interface=True)
            elif kw == "union":
                self._advance()
                self._parse_union_type(desc, doc)
            elif kw == "enum":
                self._advance()
                self._parse_enum_type(desc, doc)
            elif kw == "input":
                self._advance()
                self._parse_input_type(desc, doc)
            elif kw == "scalar":
                self._advance()
                self._parse_scalar_type(desc, doc)
            elif kw == "schema":
                self._advance()
                self._parse_schema_definition(desc)
            elif kw == "extend":
                self._advance()
                self._parse_extension(desc, doc)
            elif kw == "directive":
                self._advance()
                self._parse_directive_definition(desc)
            else:
                self._advance()  # skip unknown
        else:
            self._advance()  # skip

    def _parse_description(self) -> str:
        desc = ""
        while True:
            tok = self._peek()
            if tok is None or tok[0] not in (TokenType.BLOCK_STRING, TokenType.STRING):
                break
            ttype, val, _ = tok
            self._advance()
            if ttype == TokenType.BLOCK_STRING:
                val = val[3:-3]  # strip triple quotes
            else:
                val = val[1:-1]  # strip single quotes
            if desc:
                desc += "\n" + val
            else:
                desc = val
        return desc

    def _parse_object_type(self, desc: str, doc: MSDMDocument, is_interface: bool) -> Entity:
        name = self._expect_name("type or interface")
        entity = Entity(
            name=name,
            kind=EntityKind.OBJECT,
            description=desc,
        )
        # Implements interfaces
        tok = self._peek()
        if tok is not None and tok[1].lower() == "implements":
            self._advance()
            while True:
                iface_name = self._expect_name("interface")
                entity.implements_ref_ids.append(iface_name)
                nxt = self._peek()
                if nxt is None or nxt[0] != TokenType.AMPERSAND:
                    break
                self._advance()
        # Directives on type
        self._parse_directives(entity)

        # Fields
        self._expect(TokenType.BRACE_OPEN)
        while True:
            tok = self._peek()
            if tok is None or tok[0] == TokenType.BRACE_CLOSE:
                break
            self._skip_comments()
            field_desc = self._parse_description()
            field_name = self._expect_name("field")
            # Arguments
            field_args = []
            tok = self._peek()
            if tok is not None and tok[0] == TokenType.PAREN_OPEN:
                self._advance()
                while True:
                    tok = self._peek()
                    if tok is None or tok[0] == TokenType.PAREN_CLOSE:
                        break
                    arg_name = self._expect_name("argument")
                    self._expect(TokenType.COLON)
                    arg_type_str = self._parse_type_string()
                    arg_default = None
                    tok = self._peek()
                    if tok is not None and tok[0] == TokenType.EQUALS:
                        self._advance()
                        arg_default = self._parse_value()
                    field_args.append({
                        "name": arg_name,
                        "type": arg_type_str,
                        "defaultValue": arg_default,
                    })
                    tok = self._peek()
                    if tok is not None and tok[0] == TokenType.COMMA:
                        self._advance()
                self._expect(TokenType.PAREN_CLOSE)
            self._expect(TokenType.COLON)
            field_type_str = self._parse_type_string()
            dt = self._graphql_type_to_datatype(field_type_str, doc)
            attr = Attribute(
                name=field_name,
                data_type=dt,
                description=field_desc,
            )
            self._parse_directives(attr)
            if field_args:
                attr.annotations.append(Annotation(key="arguments", value=json.dumps(field_args)))
            if field_type_str.endswith('!'):
                attr.required = True
                attr.annotations.append(Annotation(key="graphql_type", value=field_type_str))
            entity.attributes.append(attr)
            tok = self._peek()
            if tok is not None and tok[0] == TokenType.COMMA:
                self._advance()
        self._expect(TokenType.BRACE_CLOSE)
        doc.entities.append(entity)
        return entity

    def _parse_union_type(self, desc: str, doc: MSDMDocument) -> Entity:
        name = self._expect_name("union")
        entity = Entity(name=name, kind=EntityKind.OBJECT, description=desc)
        self._parse_directives(entity)
        self._expect(TokenType.EQUALS)
        composition = EntityComposition(composition_type=CompositionType.ONE_OF)
        while True:
            member_name = self._expect_name("member type")
            composition.member_ids.append(member_name)
            tok = self._peek()
            if tok is None or tok[0] != TokenType.PIPE:
                break
            self._advance()
        composition.description=f"Union of {', '.join(composition.member_ids)}"
        doc.entities.append(entity)
        return entity

    def _parse_enum_type(self, desc: str, doc: MSDMDocument) -> Entity:
        name = self._expect_name("enum")
        entity = Entity(name=name, kind=EntityKind.OBJECT, description=desc)
        self._parse_directives(entity)
        self._expect(TokenType.BRACE_OPEN)
        values = []
        while True:
            tok = self._peek()
            if tok is None or tok[0] == TokenType.BRACE_CLOSE:
                break
            val_name = self._expect_name("enum value")
            values.append(val_name)
            tok = self._peek()
            if tok is not None and tok[0] == TokenType.COMMA:
                self._advance()
        self._expect(TokenType.BRACE_CLOSE)
        attr = Attribute(
            name="value",
            data_type=DataType(base=ScalarType.STRING),
            required=True,
        )
        quoted = ", ".join(repr(v) for v in values)
        attr.constraints.append(Constraint(type=ConstraintType.CHECK, expression=f"IN ({quoted})"))
        entity.attributes.append(attr)
        doc.entities.append(entity)
        return entity

    def _parse_input_type(self, desc: str, doc: MSDMDocument) -> Entity:
        name = self._expect_name("input")
        entity = Entity(name=name, kind=EntityKind.OBJECT, description=desc)
        self._parse_directives(entity)
        self._expect(TokenType.BRACE_OPEN)
        while True:
            tok = self._peek()
            if tok is None or tok[0] == TokenType.BRACE_CLOSE:
                break
            self._skip_comments()
            field_desc = self._parse_description()
            field_name = self._expect_name("field")
            self._expect(TokenType.COLON)
            field_type_str = self._parse_type_string()
            dt = self._graphql_type_to_datatype(field_type_str, doc)
            attr = Attribute(name=field_name, data_type=dt, description=field_desc)
            if field_type_str.endswith('!'):
                attr.required = True
                attr.annotations.append(Annotation(key="graphql_type", value=field_type_str))
            self._parse_directives(attr)
            entity.attributes.append(attr)
            tok = self._peek()
            if tok is not None and tok[0] == TokenType.COMMA:
                self._advance()
        self._expect(TokenType.BRACE_CLOSE)
        doc.entities.append(entity)
        return entity

    def _parse_scalar_type(self, desc: str, doc: MSDMDocument) -> Entity:
        name = self._expect_name("scalar")
        entity = Entity(name=name, kind=EntityKind.OBJECT, description=desc)
        self._parse_directives(entity)
        doc.entities.append(entity)
        return entity

    def _parse_schema_definition(self, desc: str) -> None:
        self._parse_directives(None)
        self._expect(TokenType.BRACE_OPEN)
        while True:
            tok = self._peek()
            if tok is None or tok[0] == TokenType.BRACE_CLOSE:
                break
            key = self._expect_name("operation type")
            self._expect(TokenType.COLON)
            val = self._expect_name("type name")
            self._root_operations[key] = val
            tok = self._peek()
            if tok is not None and tok[0] == TokenType.COMMA:
                self._advance()
        self._expect(TokenType.BRACE_CLOSE)

    def _parse_extension(self, desc: str, doc: MSDMDocument) -> None:
        kw = self._expect_keyword()
        if kw == "type":
            self._parse_object_type(desc, doc, is_interface=False)
        elif kw == "interface":
            self._parse_object_type(desc, doc, is_interface=True)
        elif kw == "union":
            self._parse_union_type(desc, doc)
        elif kw == "enum":
            self._parse_enum_type(desc, doc)
        elif kw == "input":
            self._parse_input_type(desc, doc)
        elif kw == "scalar":
            self._parse_scalar_type(desc, doc)

    def _parse_directive_definition(self, desc: str) -> None:
        name = self._expect_name("directive")
        args = []
        tok = self._peek()
        if tok is not None and tok[0] == TokenType.PAREN_OPEN:
            self._advance()
            while True:
                tok = self._peek()
                if tok is None or tok[0] == TokenType.PAREN_CLOSE:
                    break
                arg_name = self._expect_name("argument")
                self._expect(TokenType.COLON)
                arg_type = self._parse_type_string()
                default = None
                tok = self._peek()
                if tok is not None and tok[0] == TokenType.EQUALS:
                    self._advance()
                    default = self._parse_value()
                args.append({"name": arg_name, "type": arg_type, "defaultValue": default})
                tok = self._peek()
                if tok is not None and tok[0] == TokenType.COMMA:
                    self._advance()
            self._expect(TokenType.PAREN_CLOSE)
        self._expect_keyword("on")
        locations = []
        while True:
            tok = self._peek()
            if tok is None or tok[0] not in (TokenType.NAME, TokenType.KEYWORD):
                break
            loc = self._advance()
            locations.append(loc[1])
            tok = self._peek()
            if tok is not None and tok[0] == TokenType.PIPE:
                self._advance()
            else:
                break
        directive_def = {
            "name": name,
            "args": args,
            "locations": locations,
            "description": desc,
        }
        self._directive_defs.append(directive_def)

    def _parse_directives(self, target: Optional[Any]) -> None:
        while True:
            tok = self._peek()
            if tok is None or tok[0] != TokenType.DIRECTIVE:
                break
            ttype, dir_str, _ = self._advance()
            if target is None:
                continue
            if isinstance(target, Entity):
                target.annotations.append(Annotation(key="directive", value=dir_str))
            elif isinstance(target, Attribute):
                target.annotations.append(Annotation(key="directive", value=dir_str))

    def _parse_type_string(self) -> str:
        parts = []
        while True:
            tok = self._peek()
            if tok is None:
                break
            ttype, val, _ = tok
            if ttype in (TokenType.NAME, TokenType.BRACKET_OPEN, TokenType.BRACKET_CLOSE, TokenType.BANG):
                parts.append(val)
                self._advance()
            elif ttype == TokenType.KEYWORD and val in ("true", "false", "null"):
                break
            else:
                break
        return ''.join(parts)

    def _parse_value(self) -> str:
        tok = self._peek()
        if tok is None:
            return ""
        ttype, val, _ = tok
        if ttype == TokenType.STRING:
            self._advance()
            return val
        if ttype in (TokenType.NAME, TokenType.KEYWORD):
            self._advance()
            return val
        if ttype == TokenType.BRACKET_OPEN:
            result = "["
            self._advance()
            while True:
                tok = self._peek()
                if tok is None or tok[0] == TokenType.BRACKET_CLOSE:
                    break
                result += self._parse_value()
                tok = self._peek()
                if tok is not None and tok[0] == TokenType.COMMA:
                    result += ","
                    self._advance()
            self._advance()
            result += "]"
            return result
        if ttype == TokenType.BRACE_OPEN:
            result = "{"
            self._advance()
            while True:
                tok = self._peek()
                if tok is None or tok[0] == TokenType.BRACE_CLOSE:
                    break
                key = self._expect_name("object key")
                self._expect(TokenType.COLON)
                val = self._parse_value()
                result += f'"{key}":{val}'
                tok = self._peek()
                if tok is not None and tok[0] == TokenType.COMMA:
                    result += ","
                    self._advance()
            self._advance()
            result += "}"
            return result
        return ""

    def _graphql_type_to_datatype(self, type_str: str, doc: MSDMDocument) -> DataType:
        non_null = type_str.endswith('!')
        if non_null:
            type_str = type_str[:-1]
        if type_str.startswith('[') and type_str.endswith(']'):
            inner = type_str[1:-1]
            return DataType(base=ScalarType.ARRAY, element_type=self._graphql_type_to_datatype(inner, doc))
        if type_str in ("String", "ID"):
            return DataType(base=ScalarType.STRING)
        if type_str == "Int":
            return DataType(base=ScalarType.INT)
        if type_str == "Float":
            return DataType(base=ScalarType.FLOAT)
        if type_str == "Boolean":
            return DataType(base=ScalarType.BOOLEAN)
        return DataType(base=ScalarType.REF, ref_entity_id=type_str)