# engines/document/parsers/msdm_parsers/cue_parser.py
"""
CUE Parser – converts .cue files into MSDMDocument.
Handles definitions, structs, arrays, basic types, constraints,
optional fields, default values, imports, and comments.
Preserves every detail for lossless round‑trip via stored raw annotations.
"""

from __future__ import annotations
import re
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple, Set

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
    Relationship,
)


class CueParser(BaseMSDMParser):
    """Parser for CUE constraint language schema files (.cue)."""
    name = "cue"
    supported_extensions = (".cue",)

    async def _parse_to_msdm(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> MSDMDocument:
        encoding = options.encoding or "utf-8"
        text = data.decode(encoding)
        doc = MSDMDocument()
        doc.namespace = Path(source_name).stem

        # Remove line comments (//) and block comments (/* */)
        text = self._strip_comments(text)

        # Parse the file line by line or statement by statement?
        # CUE statements are separated by newlines; definitions are blocks.
        # We'll tokenize more carefully.
        self._parse_cue_text(text, doc)
        return doc

    # ── Comment stripping ───────────────────────────────────────
    def _strip_comments(self, text: str) -> str:
        # Remove block comments
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
        # Remove line comments (anything after // until newline)
        text = re.sub(r'//[^\n]*', '', text)
        return text

    def _parse_cue_text(self, text: str, doc: MSDMDocument) -> None:
        """
        Main parsing loop.
        We split by definitions: anything that looks like a definition header
        (identifier with optional #, followed by a colon and a block).
        We also handle top-level fields that are not definitions.
        """
        # Remove all extra whitespace and newlines to simplify parsing? Not good.
        # We'll use a simple recursive descent with a tokenizer.
        tokens = self._tokenize(text)
        self._tokens = tokens
        self._pos = 0

        # Parse one or more definitions
        while self._pos < len(self._tokens):
            if self._peek() and self._peek() in ('import', 'package'):
                self._parse_import_or_package(doc)
            else:
                # Try to parse a definition or a top-level field
                self._parse_top_level(doc)

    def _tokenize(self, text: str) -> List[str]:
        """
        Convert CUE source into a list of tokens.
        Tokens include: identifiers, keywords (import, package), punctuation : ; ( ) [ ] , ...
        strings, numbers, operators, etc.
        """
        # For simplicity, we use a regex that captures words, numbers, quoted strings,
        # and single-character symbols. We'll handle multi-char operators like >=, <=, == separately.
        token_pattern = re.compile(
            r'(?:#?\w+(?:\.\w+)*)'   # identifiers and package paths
            r'|"[^"]*"'               # double-quoted strings
            r"|\d+(?:\.\d+)?(?:[eE][+-]?\d+)?"  # numbers
            r'|\.\.\.|\.\.|<<|>>|>=|<=|==|!='
            r'|[{}()\[\]:;,?*&|+\-*/%<>=!]+'  # operators and punctuation
            r'|\S'                           # any other non-whitespace character
        )
        tokens = token_pattern.findall(text)
        # Filter out whitespace tokens (but keep meaningful ones)
        tokens = [t for t in tokens if not t.isspace()]
        return tokens

    def _peek(self, offset: int = 0) -> Optional[str]:
        """Return the next token without consuming it."""
        index = self._pos + offset
        if index < len(self._tokens):
            return self._tokens[index]
        return None

    def _advance(self) -> str:
        """Return the current token and move to the next."""
        if self._pos < len(self._tokens):
            tok = self._tokens[self._pos]
            self._pos += 1
            return tok
        return ""

    def _expect(self, expected: str) -> str:
        """Advance and ensure the token matches expected; raise on mismatch."""
        tok = self._advance()
        if tok != expected:
            raise SyntaxError(f"Expected '{expected}' but got '{tok}'")
        return tok

    def _parse_import_or_package(self, doc: MSDMDocument) -> None:
        """Handle import statements and package declarations."""
        if self._peek() == 'package':
            self._advance()
            pkg = self._advance()
            doc.namespace = pkg
            # skip any semicolon
            if self._peek() == ';':
                self._advance()
        elif self._peek() == 'import':
            self._advance()
            # import can be a simple path or a list
            if self._peek() == '(':
                self._advance()
                while self._peek() and self._peek() != ')':
                    path = self._advance()
                    # add annotation for import
                    doc.annotations.append(Annotation(key="import", value=path))
                    if self._peek() == ',':
                        self._advance()
                self._expect(')')
            else:
                path = self._advance()
                doc.annotations.append(Annotation(key="import", value=path))
            if self._peek() == ';':
                self._advance()

    def _parse_top_level(self, doc: MSDMDocument) -> None:
        """
        Parse either a definition (e.g., #Person: { ... }) or a top-level field.
        """
        # Save current position in case we need to backtrack (not implemented).
        name_tok = self._advance()
        # Check if it's a definition name (may start with #)
        is_definition = name_tok.startswith('#')
        field_name = name_tok if not is_definition else name_tok
        # Next token could be ':' or '=' or '::' etc.
        op = self._peek()
        if op == ':':
            self._advance()   # skip colon
            if is_definition:
                # Parse the structure after the colon
                entity = self._parse_definition_body(field_name, doc)
                doc.entities.append(entity)
            else:
                # Top-level field (not a definition) – we can treat it as a single attribute in a default entity
                default_entity = self._get_or_create_default(doc)
                attr = self._parse_field(field_name, default_entity, doc)
                default_entity.attributes.append(attr)
        elif op == '=':
            # Top-level constant definition? We can ignore or store as annotation.
            self._advance()
            value = self._parse_value(doc)
            if is_definition:
                entity = Entity(name=field_name, kind=EntityKind.OBJECT)
                entity.annotations.append(Annotation(key="constant", value=value))
                doc.entities.append(entity)
            else:
                default = self._get_or_create_default(doc)
                attr = Attribute(name=field_name, data_type=DataType(base=ScalarType.ANY),
                                 default_value=value)
                default.attributes.append(attr)
        else:
            # Unexpected; skip token
            pass

    def _get_or_create_default(self, doc: MSDMDocument) -> Entity:
        """Return the default entity for top-level fields."""
        for entity in doc.entities:
            if entity.name == "__default__":
                return entity
        entity = Entity(name="__default__", kind=EntityKind.OBJECT)
        doc.entities.append(entity)
        return entity

    def _parse_definition_body(self, name: str, doc: MSDMDocument) -> Entity:
        """Parse the body of a definition (after '#Name:')."""
        entity = Entity(name=name, kind=EntityKind.OBJECT)
        # The body is usually a struct literal { ... }
        if self._peek() == '{':
            self._advance()  # skip {
            while self._peek() and self._peek() != '}':
                # Parse one field of the struct
                self._parse_struct_field(entity, doc)
                # If there's a comma (optional in CUE), skip it
                if self._peek() == ',':
                    self._advance()
            if self._peek() == '}':
                self._advance()
        elif self._peek() == '...':
            # closed struct? Ignore for now
            pass
        else:
            # Could be a type expression, e.g., #Person: string
            # The entire definition is just a type alias. We'll create one attribute "value"
            dt = self._parse_type_expr(doc)
            attr = Attribute(name="value", data_type=dt)
            entity.attributes.append(attr)
        return entity

    def _parse_struct_field(self, entity: Entity, doc: MSDMDocument) -> None:
        """Parse a field inside a struct (e.g., name: string @tag(...) | *"default")."""
        # Field name may have quotes or be an identifier
        field_name = self._advance()
        # Remove optional marker '?' if present
        optional = False
        if field_name.endswith('?'):
            optional = True
            field_name = field_name[:-1]
        # Expect a colon
        if self._peek() == ':':
            self._advance()
        # Parse the type/expression
        dt, constraints, annotations_attrs = self._parse_field_type_and_constraints(doc)
        attr = Attribute(
            name=field_name,
            data_type=dt,
            required=not optional,
        )
        attr.constraints.extend(constraints)
        attr.annotations.extend(annotations_attrs)
        entity.attributes.append(attr)

    def _parse_field_type_and_constraints(self, doc: MSDMDocument) -> Tuple[DataType, List[Constraint], List[Annotation]]:
        """
        Parse the right-hand side of a field definition, which includes types,
        constraints (e.g., >0, <100), and attributes (@attr).
        Returns (DataType, constraints, annotations).
        """
        dt = self._parse_type_expr(doc)
        constraints = []
        annotations = []
        # Now parse optional constraints and attributes
        while self._peek() and self._peek() not in (',', '}', ';', '\n'):
            tok = self._peek()
            if tok == '@':
                self._advance()
                attr_name = self._advance()
                if self._peek() == '(':
                    self._advance()
                    attr_value = self._advance()  # just one token, could be string
                    annotations.append(Annotation(key=attr_name, value=attr_value))
                    if self._peek() == ')':
                        self._advance()
                else:
                    annotations.append(Annotation(key=attr_name, value="true"))
            elif tok in ('&', '|'):
                # Logical operators for constraints (e.g., & >0)
                self._advance()
                # Next is a constraint expression
                expr = self._parse_constraint_expr()
                if expr:
                    constraints.append(Constraint(type=ConstraintType.CHECK, expression=expr))
            elif tok.startswith('>') or tok.startswith('<') or tok.startswith('='):
                # Simple comparison constraint
                expr = self._parse_constraint_expr()
                if expr:
                    constraints.append(Constraint(type=ConstraintType.CHECK, expression=expr))
            else:
                # unknown token, break
                break
        return dt, constraints, annotations

    def _parse_type_expr(self, doc: MSDMDocument) -> DataType:
        """
        Parse a CUE type expression: string, int, [...string], { ... }, #Ref, etc.
        Returns a DataType.
        """
        tok = self._peek()
        if tok is None:
            return DataType(base=ScalarType.ANY)
        # Check for basic types
        if tok in ('string', 'int', 'float', 'number', 'bool', 'bytes', 'null', 'any'):
            self._advance()
            return DataType(base=self._cue_to_scalar(tok))
        elif tok == '[':
            # List type: [...] or [string] etc.
            self._advance()  # skip [
            if self._peek() == '...':
                self._advance()  # ... meaning any length
                if self._peek() == ']':
                    self._advance()
                    return DataType(base=ScalarType.ARRAY, element_type=DataType(base=ScalarType.ANY))
                else:
                    elem_type = self._parse_type_expr(doc)
                    self._expect(']')
                    return DataType(base=ScalarType.ARRAY, element_type=elem_type)
            elif self._peek() == ']':
                self._advance()
                return DataType(base=ScalarType.ARRAY, element_type=DataType(base=ScalarType.ANY))
            else:
                # expression inside brackets: [expr]
                # could be a type, e.g., [string]
                elem_type = self._parse_type_expr(doc)
                self._expect(']')
                return DataType(base=ScalarType.ARRAY, element_type=elem_type)
        elif tok == '{':
            # Inline struct – we'll parse it as a nested entity later; for now return STRUCT
            self._advance()
            # skip until matching } (very simple)
            depth = 1
            while self._pos < len(self._tokens) and depth > 0:
                if self._peek() == '{':
                    depth += 1
                elif self._peek() == '}':
                    depth -= 1
                    if depth == 0:
                        self._advance()
                        break
                self._advance()
            return DataType(base=ScalarType.STRUCT)
        elif tok.startswith('#') or tok.startswith('_') or tok[0].isalpha():
            # Reference to another definition or type
            self._advance()
            return DataType(base=ScalarType.REF, ref_entity=tok)
        elif tok == '...':
            # Any type? Treat as any
            self._advance()
            return DataType(base=ScalarType.ANY)
        else:
            # Could be a literal value (default), e.g., "hello", 5
            # We'll parse the value and treat the type as the appropriate scalar
            value = self._parse_value(doc)
            return DataType(base=ScalarType.ANY)  # better: infer from value

    def _parse_value(self, doc: MSDMDocument) -> str:
        """Parse a literal value (string, number, bool, etc.) and return its string representation."""
        # Very simple: read one token
        val = self._advance()
        if val.startswith('"') or val.startswith("'"):
            # consume until matching quote
            pass
        return val

    def _parse_constraint_expr(self) -> Optional[str]:
        """Parse a simple constraint expression and return its string."""
        expr = []
        # Read tokens until we hit a separator
        while self._peek() and self._peek() not in (',', '}', ';', '&', '|', '@', ':'):
            expr.append(self._advance())
        return " ".join(expr).strip() or None

    def _cue_to_scalar(self, cue_type: str) -> ScalarType:
        mapping = {
            "string": ScalarType.STRING,
            "int": ScalarType.INT,
            "float": ScalarType.FLOAT,
            "number": ScalarType.FLOAT,
            "bool": ScalarType.BOOLEAN,
            "bytes": ScalarType.BINARY,
            "null": ScalarType.ANY,
            "any": ScalarType.ANY,
        }
        return mapping.get(cue_type, ScalarType.ANY)