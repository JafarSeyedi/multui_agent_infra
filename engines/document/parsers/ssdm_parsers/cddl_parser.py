"""
cddl_parser.py – CDDL (CBOR Data Definition Language) parser → SSDM_DOCUMENT
"""

from __future__ import annotations

import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from ..base import ParseOptions
from ..ssdm_parsers.base_ssdm_parser import BaseSSDMParser
from ...models.ssdm_models import (
    SSDM_DOCUMENT,
    Operation,
    Parameter,
    ParameterLocation,
)
from ...models.msdm_models import (
    MSDMDocument,
    Entity,
    Attribute,
    CompositionEntity,
)


# --------------------------------------------------------------------------
#  CDDL Lexer
# --------------------------------------------------------------------------
class CDDLTokenType:
    IDENT = "IDENT"
    NUMBER = "NUMBER"
    STRING = "STRING"
    OP = "OP"            # operators like '=', '/=', ':', '=>', ',', ';', '{', '}', '[', ']', '(', ')', '#', '?', '*', '+', '&'
    NEWLINE = "NEWLINE"
    EOF = "EOF"

@dataclass
class CDDLToken:
    type: str
    value: str
    line: int
    col: int

class CDDLLexer:
    """Simple lexer for CDDL text."""
    _SIMPLE_OPS = set("=/:,{}[]()#?*+;&")
    _TWO_CHAR_OPS = {"/=", "=>"}

    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1
        self.col = 1
        self._next = None  # lookahead

    def _skip_spaces_and_comments(self):
        while self.pos < len(self.text):
            ch = self.text[self.pos]
            if ch in ' \t\r':
                self.pos += 1
                self.col += 1
            elif ch == '\n':
                self.pos += 1
                self.line += 1
                self.col = 1
                # return NEWLINE? We treat newline as token separator, not a token unless needed.
                # but we need to emit NEWLINE tokens for statement separation? We'll handle via lexer's peek.
                # We'll not emit newline tokens to simplify; we'll rely on end of statement detection via ';' or end of file? 
                # Actually CDDL uses either newline or ';' as statement separator. So we need to detect statement boundaries.
                # We'll handle it in the parser by checking for newlines and ';' manually.
                # For lexer, we'll skip newlines in _skip_spaces_and_comments? But then we lose ability to detect newline as separator.
                # Better: we'll have a method skip_whitespace that does not skip newlines; we'll handle newline as a token in the lexer.
                # Let's emit NEWLINE tokens so the parser can use them.
                # We'll modify to include newline handling.
                return
            elif ch == ';':
                # comment until end of line
                while self.pos < len(self.text) and self.text[self.pos] != '\n':
                    self.pos += 1
                    self.col += 1
            else:
                break

    def _make_token(self, type, value):
        return CDDLToken(type, value, self.line, self.col)

    def next_token(self) -> CDDLToken:
        self._skip_spaces_and_comments()
        if self.pos >= len(self.text):
            return self._make_token(CDDLTokenType.EOF, "")

        ch = self.text[self.pos]
        start_line, start_col = self.line, self.col

        # Newline – treat as token
        if ch == '\n':
            self.pos += 1
            self.line += 1
            self.col = 1
            return self._make_token(CDDLTokenType.NEWLINE, "\n")

        # Two-character operators
        if self.pos+1 < len(self.text):
            two = self.text[self.pos:self.pos+2]
            if two in self._TWO_CHAR_OPS:
                self.pos += 2
                self.col += 2
                return self._make_token(CDDLTokenType.OP, two)

        # Single-character operators
        if ch in self._SIMPLE_OPS:
            self.pos += 1
            self.col += 1
            return self._make_token(CDDLTokenType.OP, ch)

        # String (double-quoted)
        if ch == '"':
            start = self.pos
            self.pos += 1
            self.col += 1
            while self.pos < len(self.text):
                c = self.text[self.pos]
                if c == '\\' and self.pos+1 < len(self.text):
                    self.pos += 2
                    self.col += 2
                elif c == '"':
                    self.pos += 1
                    self.col += 1
                    return self._make_token(CDDLTokenType.STRING, self.text[start:self.pos])
                else:
                    self.pos += 1
                    self.col += 1
            raise SyntaxError("Unterminated string")

        # Number (integer, float, hex)
        if ch.isdigit() or (ch == '-' and self.pos+1 < len(self.text) and self.text[self.pos+1].isdigit()):
            start = self.pos
            if ch == '-':
                self.pos += 1
                self.col += 1
            while self.pos < len(self.text) and self.text[self.pos].isdigit():
                self.pos += 1
                self.col += 1
            if self.pos < len(self.text) and self.text[self.pos] == '.' and self.pos+1 < len(self.text) and self.text[self.pos+1].isdigit():
                self.pos += 1  # '.'
                self.col += 1
                while self.pos < len(self.text) and self.text[self.pos].isdigit():
                    self.pos += 1
                    self.col += 1
            # hex? skip for now
            return self._make_token(CDDLTokenType.NUMBER, self.text[start:self.pos])

        # Identifier or keyword
        if ch.isalpha() or ch == '_':
            start = self.pos
            while self.pos < len(self.text) and (self.text[self.pos].isalnum() or self.text[self.pos] in ('_', '-')):
                self.pos += 1
                self.col += 1
            ident = self.text[start:self.pos]
            # check for reserved words? CDDL has no reserved words; all are identifiers.
            return self._make_token(CDDLTokenType.IDENT, ident)

        raise SyntaxError(f"Unexpected character '{ch}' at line {self.line}, col {self.col}")


# --------------------------------------------------------------------------
#  CDDL Parser
# --------------------------------------------------------------------------
class CDDLType:
    """Intermediate representation of a CDDL type."""
    PRIMITIVE = "primitive"
    MAP = "map"
    ARRAY = "array"
    GROUP = "group"
    CHOICE = "choice"
    REF = "ref"
    TAGGED = "tagged"
    CONTROL = "control"
    REPETITION = "repetition"

    def __init__(self, kind: str):
        self.kind = kind
        self.primitive_name: Optional[str] = None
        self.ref_name: Optional[str] = None
        self.members: List[CDDLType] = []          # for choices, groups, arrays
        self.map_members: List[Tuple[CDDLType, CDDLType]] = []  # (key, value)
        self.tag: Optional[int] = None
        self.tag_type: Optional[CDDLType] = None
        self.control_operator: Optional[str] = None
        self.control_value: Optional[str] = None
        self.repetition: Optional[str] = None  # '?' , '*', '+'
        self.repetition_type: Optional[CDDLType] = None
        self.is_group = False
        self.group_name: Optional[str] = None

    def __repr__(self):
        return f"CDDLType({self.kind}, {self.primitive_name or self.ref_name or ''})"


class CDDLParser:
    """Recursive descent parser for CDDL."""

    def __init__(self, lexer: CDDLLexer):
        self.lexer = lexer
        self._token = self.lexer.next_token()  # current token

    def _eat(self, expected_type: str, expected_value: Optional[str] = None) -> CDDLToken:
        token = self._token
        if token.type != expected_type:
            raise SyntaxError(f"Expected {expected_type}, got {token.type} ({token.value})")
        if expected_value is not None and token.value != expected_value:
            raise SyntaxError(f"Expected '{expected_value}', got '{token.value}'")
        self._token = self.lexer.next_token()
        return token

    def _skip_newlines(self):
        while self._token.type == CDDLTokenType.NEWLINE:
            self._token = self.lexer.next_token()

    def parse(self) -> Dict[str, CDDLType]:
        """Parse all rules. Returns dict from rule name to CDDLType."""
        rules = {}
        self._skip_newlines()
        while self._token.type != CDDLTokenType.EOF:
            name_token = self._eat(CDDLTokenType.IDENT)
            rule_name = name_token.value
            # optional generic parameters ( < ... > ) – skip for now
            if self._token.value == '<':
                # skip until '>'
                while self._token.value != '>':
                    self._token = self.lexer.next_token()
                self._token = self.lexer.next_token()  # skip '>'
            # operator: = or /=
            if self._token.value not in ('=', '/='):
                raise SyntaxError(f"Expected '=' or '/=' after rule name, got {self._token.value}")
            is_extend = (self._token.value == '/=')
            self._token = self.lexer.next_token()
            # parse type expression
            type_expr = self._parse_type()
            # if extend, we would merge with existing (not implemented fully)
            rules[rule_name] = type_expr
            # after rule, expect newline or ';'
            if self._token.type == CDDLTokenType.OP and self._token.value == ';':
                self._token = self.lexer.next_token()
            elif self._token.type == CDDLTokenType.NEWLINE:
                self._skip_newlines()
            else:
                # allow end of file
                pass
        return rules

    # ---------- Type parsing ----------
    def _parse_type(self) -> CDDLType:
        """type = choice / group / ..."""
        return self._parse_choice()

    def _parse_choice(self) -> CDDLType:
        """choice = group ('/' group)*"""
        left = self._parse_group()
        while self._token.value == '/':
            self._token = self.lexer.next_token()
            right = self._parse_group()
            choices = [left, right]
            # combine into a single choice node
            while self._token.value == '/':
                self._token = self.lexer.next_token()
                choices.append(self._parse_group())
            left = CDDLType(CDDLType.CHOICE)
            left.members = choices
        return left

    def _parse_group(self) -> CDDLType:
        """group = ( ( map | array | primitive | '(' type ')' ) ( '*' | '?' | '+' )? ) ... group entry? """
        # repeat markers apply to the preceding atom, e.g., ? type, * type
        atom = self._parse_atom()
        # check for repetition marker
        if self._token.value in ('?', '*', '+'):
            marker = self._token.value
            self._token = self.lexer.next_token()
            rep = CDDLType(CDDLType.REPETITION)
            rep.repetition = marker
            rep.repetition_type = atom
            return rep
        return atom

    def _parse_atom(self) -> CDDLType:
        """atom = primitive | ref | map | array | '(' type ')' | '#tag' type"""
        token = self._token
        if token.type == CDDLTokenType.IDENT:
            # check for primitive names
            primitive_set = {
                'any', 'uint', 'int', 'float', 'float32', 'float64',
                'bytes', 'bstr', 'text', 'tstr', 'nil', 'bool', 'true', 'false',
                'any', 'null', 'number', 'integer', 'unsigned'
            }
            if token.value in primitive_set:
                self._token = self.lexer.next_token()
                prim = CDDLType(CDDLType.PRIMITIVE)
                prim.primitive_name = token.value
                return prim
            else:
                # it's a reference to another rule
                self._token = self.lexer.next_token()
                ref = CDDLType(CDDLType.REF)
                ref.ref_name = token.value
                # optionally followed by generic arguments? skip
                if self._token.value == '<':
                    # skip
                    while self._token.value != '>':
                        self._token = self.lexer.next_token()
                    self._token = self.lexer.next_token()
                return ref
        elif token.value == '{':
            return self._parse_map()
        elif token.value == '[':
            return self._parse_array()
        elif token.value == '(':
            self._token = self.lexer.next_token()
            inner = self._parse_type()
            self._eat(CDDLTokenType.OP, ')')
            return inner
        elif token.value == '#':
            # tag
            self._token = self.lexer.next_token()
            # could be a number or a ref? assume number
            tag_val = int(self._eat(CDDLTokenType.NUMBER).value)
            self._eat(CDDLTokenType.OP, '(')
            tagged_type = self._parse_type()
            self._eat(CDDLTokenType.OP, ')')
            tagged = CDDLType(CDDLType.TAGGED)
            tagged.tag = tag_val
            tagged.tag_type = tagged_type
            return tagged
        elif token.value in ('?', '*', '+'):
            # stray marker not preceded by atom – error
            raise SyntaxError(f"Unexpected repetition marker '{token.value}'")
        else:
            raise SyntaxError(f"Unexpected token '{token.value}'")

    def _parse_map(self) -> CDDLType:
        """map = { ( member ',' )* member? }"""
        self._eat(CDDLTokenType.OP, '{')
        map_type = CDDLType(CDDLType.MAP)
        while self._token.value != '}':
            key = self._parse_type()
            # key => value or key : value (CDDL uses '=>')
            if self._token.value == '=>' or self._token.value == ':':
                self._token = self.lexer.next_token()
                value = self._parse_type()
                map_type.map_members.append((key, value))
            else:
                # just a group entry without explicit arrow? treat as key only? error
                raise SyntaxError("Expected '=>' in map entry")
            if self._token.value == ',':
                self._token = self.lexer.next_token()
            else:
                break
        self._eat(CDDLTokenType.OP, '}')
        return map_type

    def _parse_array(self) -> CDDLType:
        """array = [ type ]"""
        self._eat(CDDLTokenType.OP, '[')
        arr_type = CDDLType(CDDLType.ARRAY)
        # can be empty? produce "[]" but we assume at least one type
        if self._token.value != ']':
            element = self._parse_type()
            arr_type.members = [element]  # only one member for array
        self._eat(CDDLTokenType.OP, ']')
        return arr_type


# --------------------------------------------------------------------------
#  SSDM conversion
# --------------------------------------------------------------------------
class CDDLServiceParser(BaseSSDMParser):
    name = "cddl"
    supported_extensions = (".cddl",)

    async def _parse_to_document(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> SSDM_DOCUMENT:
        text = data.decode(options.encoding)
        lexer = CDDLLexer(text)
        parser = CDDLParser(lexer)
        rules = parser.parse()

        entities = []
        for rule_name, cddl_type in rules.items():
            entity = self._cddl_to_entity(rule_name, cddl_type, rules)
            if entity:
                entities.append(entity)

        msdm_doc = MSDMDocument(entities=entities) if entities else None

        doc = SSDM_DOCUMENT(
            document_id="",
            title=Path(source_name).stem,
            version="1.0.0",
            description=f"CDDL schema from {source_name}",
            type_definitions=msdm_doc,
            operations=[],  # CDDL defines no operations
            servers=[],
            security_schemes=[],
            metadata={},
        )
        doc.is_valid = True
        return doc

    def _cddl_to_entity(self, name: str, cddl_type: CDDLType, rules: Dict[str, CDDLType]) -> Entity:
        """Convert a CDDL type tree to an MSDM Entity."""
        if cddl_type.kind == CDDLType.PRIMITIVE:
            # map to simple type string
            type_str = self._primitive_to_type_string(cddl_type.primitive_name)
            return Entity(
                name=name,
                attributes=[Attribute(name="value", type=type_str)],
            )
        elif cddl_type.kind == CDDLType.REF:
            # reference to another rule; produce entity with a single attribute of that referenced type
            ref_name = cddl_type.ref_name
            # if ref is another entity, we can create a placeholder; but for now just treat as type string
            return Entity(
                name=name,
                attributes=[Attribute(name="value", type=ref_name)],
                # we could add a link later
            )
        elif cddl_type.kind == CDDLType.MAP:
            attrs = []
            for key_type, value_type in cddl_type.map_members:
                # if key is a string literal, use as attribute name
                if key_type.kind == CDDLType.PRIMITIVE and key_type.primitive_name in ('text', 'tstr') and hasattr(key_type, 'literal_value'):
                    # but our lexer doesn't extract literal value from strings; we'd need to modify.
                    # For simplicity, we'll use "key" and store the key expression in metadata.
                    key_name = "key"
                elif key_type.kind == CDDLType.REF and key_type.ref_name in ('int', 'uint'):
                    key_name = "key"
                else:
                    key_name = "key"  # generic
                attr_type = self._type_to_string(value_type, rules)
                attr = Attribute(name=key_name, type=attr_type)
                # store the original key and value type for completeness
                attr.metadata["cddl_key"] = key_type
                attr.metadata["cddl_value"] = value_type
                attrs.append(attr)
            return Entity(name=name, attributes=attrs)
        elif cddl_type.kind == CDDLType.ARRAY:
            if cddl_type.members:
                items_type = self._type_to_string(cddl_type.members[0], rules)
            else:
                items_type = "any"
            return Entity(
                name=name,
                attributes=[Attribute(name="items", type=f"array<{items_type}>")],
            )
        elif cddl_type.kind == CDDLType.GROUP:
            # group is like a struct; already handled through maps, but could be bare group.
            # For simplicity, we treat as a generic entity with empty attributes.
            return Entity(name=name, attributes=[])
        elif cddl_type.kind == CDDLType.CHOICE:
            # create composition entity
            members = []
            for i, sub in enumerate(cddl_type.members):
                sub_entity = self._cddl_to_entity(f"{name}_choice{i}", sub, rules)
                members.append(sub_entity)
            composition = CompositionEntity(composition_type="oneOf", members=members)
            return Entity(name=name, attributes=[], composition=composition)
        elif cddl_type.kind == CDDLType.TAGGED:
            # tagged type – wrap inner type with metadata
            inner_entity = self._cddl_to_entity(name, cddl_type.tag_type, rules)
            inner_entity.metadata["tag"] = cddl_type.tag
            return inner_entity
        elif cddl_type.kind == CDDLType.REPETITION:
            # ? type, * type, + type
            inner_entity = self._cddl_to_entity(name, cddl_type.repetition_type, rules)
            inner_entity.metadata["repetition"] = cddl_type.repetition
            return inner_entity
        else:
            return Entity(name=name, attributes=[])

    def _type_to_string(self, cddl_type: CDDLType, rules: Dict[str, CDDLType]) -> str:
        """Produce a type string from a CDDL type."""
        if cddl_type.kind == CDDLType.PRIMITIVE:
            return self._primitive_to_type_string(cddl_type.primitive_name)
        elif cddl_type.kind == CDDLType.REF:
            return cddl_type.ref_name
        elif cddl_type.kind == CDDLType.ARRAY:
            items = self._type_to_string(cddl_type.members[0], rules) if cddl_type.members else "any"
            return f"array<{items}>"
        elif cddl_type.kind == CDDLType.MAP:
            return "object"
        elif cddl_type.kind == CDDLType.GROUP:
            return "object"
        elif cddl_type.kind == CDDLType.CHOICE:
            # choices become composition entity, not a simple type string
            return "choice"
        elif cddl_type.kind == CDDLType.TAGGED:
            return self._type_to_string(cddl_type.tag_type, rules)
        elif cddl_type.kind == CDDLType.REPETITION:
            return self._type_to_string(cddl_type.repetition_type, rules)
        return "any"

    def _primitive_to_type_string(self, prim: str) -> str:
        mapping = {
            'text': 'string', 'tstr': 'string',
            'bytes': 'binary', 'bstr': 'binary',
            'uint': 'int', 'int': 'int',
            'float': 'float', 'float32': 'float', 'float64': 'float',
            'bool': 'boolean', 'nil': 'null', 'any': 'any',
            'true': 'boolean', 'false': 'boolean',
        }
        return mapping.get(prim, prim)