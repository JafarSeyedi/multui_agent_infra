"""
graphql_service_parser.py – GraphQL SDL parser → SSDM_DOCUMENT
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field

from ..base import ParseOptions
from ..ssdm_parsers.base_ssdm_parser import BaseSSDMParser
from ...models.ssdm_models import (
    SSDM_DOCUMENT,
    Operation,
    OperationType,
    Parameter,
    ParameterLocation,
    RequestBody,
    Response,
    GraphQLService,
)
from ...models.msdm_models import (
    MSDMDocument,
    Entity,
    Attribute,
    CompositionEntity,
)


# =============================================================================
#  GraphQL SDL Lexer & AST
# =============================================================================

# Token types
class TokenType:
    NAME = "NAME"
    STRING = "STRING"
    INT = "INT"
    FLOAT = "FLOAT"
    PUNCTUATION = "PUNCTUATION"
    COMMENT = "COMMENT"
    EOF = "EOF"

@dataclass
class Token:
    type: str
    value: str
    line: int = 0
    col: int = 0

class GraphQLScanner:
    """Simple scanner for GraphQL SDL."""
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1
        self.col = 1

    def peek(self) -> Token:
        return self._next_token(skip=False)

    def next(self) -> Token:
        return self._next_token(skip=True)

    def _next_token(self, skip: bool) -> Token:
        self._skip_whitespace_and_comments()
        if self.pos >= len(self.text):
            return Token(TokenType.EOF, "", self.line, self.col)

        ch = self.text[self.pos]

        # Names
        if ch.isalpha() or ch == '_':
            start = self.pos
            while self.pos < len(self.text) and (self.text[self.pos].isalnum() or self.text[self.pos] == '_'):
                self.pos += 1
            value = self.text[start:self.pos]
            return Token(TokenType.NAME, value, self.line, self.col)

        # Numbers
        if ch.isdigit() or (ch == '-' and self.pos + 1 < len(self.text) and self.text[self.pos+1].isdigit()):
            return self._scan_number()

        # Strings (single or double quoted)
        if ch in ('"', "'"):
            return self._scan_string()

        # Punctuation
        puncts = ['!', '$', '(', ')', '{', '}', '[', ']', ':', ',', '=', '@', '|', '&']
        if ch in puncts:
            self.pos += 1
            return Token(TokenType.PUNCTUATION, ch, self.line, self.col)

        # Unexpected
        raise SyntaxError(f"Unexpected character '{ch}' at line {self.line}, col {self.col}")

    def _skip_whitespace_and_comments(self):
        while self.pos < len(self.text):
            ch = self.text[self.pos]
            if ch in ' \t\n\r':
                if ch == '\n':
                    self.line += 1
                    self.col = 1
                self.pos += 1
            elif ch == '#':
                # comment until end of line
                while self.pos < len(self.text) and self.text[self.pos] != '\n':
                    self.pos += 1
            else:
                break

    def _scan_number(self) -> Token:
        start = self.pos
        if self.text[self.pos] == '-':
            self.pos += 1
        while self.pos < len(self.text) and self.text[self.pos].isdigit():
            self.pos += 1
        if self.pos < len(self.text) and self.text[self.pos] == '.':
            self.pos += 1
            while self.pos < len(self.text) and self.text[self.pos].isdigit():
                self.pos += 1
            return Token(TokenType.FLOAT, self.text[start:self.pos], self.line, self.col)
        return Token(TokenType.INT, self.text[start:self.pos], self.line, self.col)

    def _scan_string(self) -> Token:
        quote = self.text[self.pos]
        start = self.pos
        self.pos += 1  # opening quote
        while self.pos < len(self.text):
            ch = self.text[self.pos]
            if ch == quote and self.text[self.pos-1] != '\\':
                self.pos += 1
                return Token(TokenType.STRING, self.text[start:self.pos], self.line, self.col)
            self.pos += 1
        raise SyntaxError("Unterminated string")


# =============================================================================
#  Parser – builds an internal schema representation
# =============================================================================

class GraphQLField:
    def __init__(self, name: str):
        self.name = name
        self.type_ref: str = ""      # e.g., "String!", "[Todo!]!"
        self.arguments: List[Tuple[str, str, Optional[str]]] = []  # (name, type, default)
        self.description: Optional[str] = None
        self.directives: Dict[str, Dict[str, str]] = {}

class GraphQLType:
    KIND_OBJECT = "OBJECT"
    KIND_INPUT_OBJECT = "INPUT_OBJECT"
    KIND_ENUM = "ENUM"
    KIND_UNION = "UNION"
    KIND_INTERFACE = "INTERFACE"
    KIND_SCALAR = "SCALAR"

    def __init__(self, name: str, kind: str):
        self.name = name
        self.kind = kind
        self.description: Optional[str] = None
        self.fields: List[GraphQLField] = []
        self.interfaces: List[str] = []  # for objects/interfaces
        self.union_members: List[str] = []  # for unions
        self.enum_values: List[str] = []  # for enums
        self.directives: Dict[str, Dict[str, str]] = {}

class GraphQLSchema:
    def __init__(self):
        self.types: Dict[str, GraphQLType] = {}
        self.query_type: Optional[str] = None
        self.mutation_type: Optional[str] = None
        self.subscription_type: Optional[str] = None
        self.directives: List[Dict] = []  # custom directive definitions

class GraphQLParser:
    """Recursive descendant parser for GraphQL SDL."""

    def __init__(self, text: str):
        self.scanner = GraphQLScanner(text)
        self.schema = GraphQLSchema()
        self._current_description: Optional[str] = None  # description preceding a definition

    def parse(self) -> GraphQLSchema:
        self._lookahead = self.scanner.next()
        while self._lookahead.type != TokenType.EOF:
            self._parse_schema_definition()
        return self.schema

    def _match(self, expected_type: str, expected_value: Optional[str] = None) -> Token:
        if self._lookahead.type != expected_type:
            raise SyntaxError(f"Expected {expected_type} but got {self._lookahead.type}")
        if expected_value is not None and self._lookahead.value != expected_value:
            raise SyntaxError(f"Expected '{expected_value}' but got '{self._lookahead.value}'")
        token = self._lookahead
        self._advance()
        return token

    def _advance(self):
        self._lookahead = self.scanner.next()

    def _peek(self) -> Token:
        return self._lookahead

    # ------------------------------------------------------------------
    #  Top-level definitions
    # ------------------------------------------------------------------
    def _parse_schema_definition(self):
        # Collect description strings (multiple possible)
        while self._peek().type == TokenType.STRING:
            desc_token = self._peek()
            self._advance()
            self._current_description = desc_token.value.strip('"').strip("'")
            # multi-line descriptions are concatenated; in reality GraphQL supports triple quotes,
            # but here we assume single strings.

        token = self._peek()
        if token.type == TokenType.NAME:
            name_val = token.value
            if name_val == 'type':
                self._parse_object_type()
            elif name_val == 'input':
                self._parse_input_object_type()
            elif name_val == 'enum':
                self._parse_enum_type()
            elif name_val == 'union':
                self._parse_union_type()
            elif name_val == 'interface':
                self._parse_interface_type()
            elif name_val == 'scalar':
                self._parse_scalar_type()
            elif name_val == 'schema':
                self._parse_schema_block()
            elif name_val == 'directive':
                self._parse_directive_definition()
            elif name_val == 'extend':
                # Extensions not yet supported; skip
                self._advance()
                self._skip_block()
            else:
                # Unknown; skip
                self._advance()
        elif token.type == TokenType.PUNCTUATION and token.value == '{':
            # schema definition block without 'schema' keyword
            self._parse_schema_block()
        else:
            # skip unexpected token
            self._advance()

    def _skip_block(self):
        """Skip over a block delimited by { }."""
        depth = 0
        while self._peek().type != TokenType.EOF:
            if self._peek().value == '{':
                depth += 1
                self._advance()
            elif self._peek().value == '}':
                depth -= 1
                if depth == 0:
                    break
                self._advance()
            else:
                self._advance()

    # ------------------------------------------------------------------
    #  Object type: type Name implements IFace1 & IFace2 { fields }
    # ------------------------------------------------------------------
    def _parse_object_type(self):
        self._advance()  # consume 'type'
        name = self._match(TokenType.NAME).value
        type_def = GraphQLType(name, GraphQLType.KIND_OBJECT)
        if self._current_description:
            type_def.description = self._current_description
            self._current_description = None

        # Interfaces
        if self._peek().value == 'implements':
            self._advance()
            interfaces = []
            while self._peek().value != '{':
                if self._peek().value == '&':
                    self._advance()
                    continue
                interfaces.append(self._match(TokenType.NAME).value)
            type_def.interfaces = interfaces

        # Directives on type
        type_def.directives = self._parse_directives()

        # Fields
        self._match(TokenType.PUNCTUATION, '{')
        while self._peek().value != '}':
            type_def.fields.append(self._parse_field())
        self._match(TokenType.PUNCTUATION, '}')
        self.schema.types[name] = type_def

    # ------------------------------------------------------------------
    #  Input object type
    # ------------------------------------------------------------------
    def _parse_input_object_type(self):
        self._advance()  # consume 'input'
        name = self._match(TokenType.NAME).value
        type_def = GraphQLType(name, GraphQLType.KIND_INPUT_OBJECT)
        if self._current_description:
            type_def.description = self._current_description
            self._current_description = None
        type_def.directives = self._parse_directives()
        self._match(TokenType.PUNCTUATION, '{')
        while self._peek().value != '}':
            # input fields only have name, type, optional default
            field = GraphQLField(name=self._match(TokenType.NAME).value)
            self._match(TokenType.PUNCTUATION, ':')
            field.type_ref = self._parse_type_reference()
            if self._peek().value == '=':
                self._advance()
                field.arguments.append(('default', 'String', self._parse_value()))
            field.directives = self._parse_directives()
            type_def.fields.append(field)
        self._match(TokenType.PUNCTUATION, '}')
        self.schema.types[name] = type_def

    # ------------------------------------------------------------------
    #  Enum type
    # ------------------------------------------------------------------
    def _parse_enum_type(self):
        self._advance()  # consume 'enum'
        name = self._match(TokenType.NAME).value
        type_def = GraphQLType(name, GraphQLType.KIND_ENUM)
        if self._current_description:
            type_def.description = self._current_description
            self._current_description = None
        type_def.directives = self._parse_directives()
        self._match(TokenType.PUNCTUATION, '{')
        while self._peek().value != '}':
            val = self._match(TokenType.NAME).value
            type_def.enum_values.append(val)
            # Possible directives on enum values? We skip.
        self._match(TokenType.PUNCTUATION, '}')
        self.schema.types[name] = type_def

    # ------------------------------------------------------------------
    #  Union type: union Name = Member1 | Member2
    # ------------------------------------------------------------------
    def _parse_union_type(self):
        self._advance()  # consume 'union'
        name = self._match(TokenType.NAME).value
        type_def = GraphQLType(name, GraphQLType.KIND_UNION)
        if self._current_description:
            type_def.description = self._current_description
            self._current_description = None
        self._match(TokenType.PUNCTUATION, '=')
        while True:
            member = self._match(TokenType.NAME).value
            type_def.union_members.append(member)
            if self._peek().value != '|':
                break
            self._advance()
        type_def.directives = self._parse_directives()
        self.schema.types[name] = type_def

    # ------------------------------------------------------------------
    #  Interface type
    # ------------------------------------------------------------------
    def _parse_interface_type(self):
        self._advance()  # consume 'interface'
        name = self._match(TokenType.NAME).value
        type_def = GraphQLType(name, GraphQLType.KIND_INTERFACE)
        if self._current_description:
            type_def.description = self._current_description
            self._current_description = None
        type_def.directives = self._parse_directives()
        self._match(TokenType.PUNCTUATION, '{')
        while self._peek().value != '}':
            type_def.fields.append(self._parse_field())
        self._match(TokenType.PUNCTUATION, '}')
        self.schema.types[name] = type_def

    # ------------------------------------------------------------------
    #  Scalar type
    # ------------------------------------------------------------------
    def _parse_scalar_type(self):
        self._advance()  # consume 'scalar'
        name = self._match(TokenType.NAME).value
        type_def = GraphQLType(name, GraphQLType.KIND_SCALAR)
        if self._current_description:
            type_def.description = self._current_description
            self._current_description = None
        type_def.directives = self._parse_directives()
        self.schema.types[name] = type_def

    # ------------------------------------------------------------------
    #  Schema block: schema { query: Query, mutation: Mutation, subscription: Subscription }
    # ------------------------------------------------------------------
    def _parse_schema_block(self):
        if self._peek().value == 'schema':
            self._advance()
        self._match(TokenType.PUNCTUATION, '{')
        while self._peek().value != '}':
            kw = self._match(TokenType.NAME).value
            self._match(TokenType.PUNCTUATION, ':')
            type_name = self._match(TokenType.NAME).value
            if kw == 'query':
                self.schema.query_type = type_name
            elif kw == 'mutation':
                self.schema.mutation_type = type_name
            elif kw == 'subscription':
                self.schema.subscription_type = type_name
        self._match(TokenType.PUNCTUATION, '}')

    # ------------------------------------------------------------------
    #  Directive definition (skip, not essential for SSDM)
    # ------------------------------------------------------------------
    def _parse_directive_definition(self):
        self._advance()  # consume 'directive'
        # skip the whole definition
        while self._peek().value != '{':
            self._advance()
        self._skip_block()

    # ------------------------------------------------------------------
    #  Field parsing (for object/interface)
    # ------------------------------------------------------------------
    def _parse_field(self) -> GraphQLField:
        # optional description
        if self._peek().type == TokenType.STRING:
            desc = self._peek().value.strip('"')
            self._advance()
        else:
            desc = None
        field_name = self._match(TokenType.NAME).value
        field = GraphQLField(field_name)
        if desc:
            field.description = desc
        # Arguments
        if self._peek().value == '(':
            self._advance()
            while self._peek().value != ')':
                arg_name = self._match(TokenType.NAME).value
                self._match(TokenType.PUNCTUATION, ':')
                arg_type = self._parse_type_reference()
                default = None
                if self._peek().value == '=':
                    self._advance()
                    default = self._parse_value()
                field.arguments.append((arg_name, arg_type, default))
                if self._peek().value == ',':
                    self._advance()
            self._match(TokenType.PUNCTUATION, ')')
        # Return type
        self._match(TokenType.PUNCTUATION, ':')
        field.type_ref = self._parse_type_reference()
        # Directives on field
        field.directives = self._parse_directives()
        return field

    def _parse_type_reference(self) -> str:
        """Parse a type reference possibly with list and non-null modifiers."""
        type_str = ""
        if self._peek().value == '[':
            self._advance()
            inner = self._parse_type_reference()
            self._match(TokenType.PUNCTUATION, ']')
            type_str = f"[{inner}]"
        else:
            type_str = self._match(TokenType.NAME).value
        if self._peek().value == '!':
            self._advance()
            type_str += "!"
        return type_str

    def _parse_value(self) -> str:
        """Parse a literal value (null, boolean, number, string, enum, list, object)."""
        token = self._peek()
        if token.type == TokenType.NAME and token.value in ('true','false','null'):
            self._advance()
            return token.value
        elif token.type in (TokenType.INT, TokenType.FLOAT, TokenType.STRING):
            self._advance()
            return token.value
        elif token.value == '[':
            self._advance()
            values = []
            while self._peek().value != ']':
                values.append(self._parse_value())
                if self._peek().value == ',':
                    self._advance()
            self._match(TokenType.PUNCTUATION, ']')
            return f"[{','.join(values)}]"
        elif token.value == '{':
            self._advance()
            pairs = []
            while self._peek().value != '}':
                key = self._match(TokenType.NAME).value
                self._match(TokenType.PUNCTUATION, ':')
                val = self._parse_value()
                pairs.append(f"{key}:{val}")
                if self._peek().value == ',':
                    self._advance()
            self._match(TokenType.PUNCTUATION, '}')
            return f"{{{','.join(pairs)}}}"
        raise SyntaxError(f"Unexpected value token: {token}")

    def _parse_directives(self) -> Dict[str, Dict[str, str]]:
        """Collect directives like @deprecated(reason: "...") until no more '@'. """
        dirs = {}
        while self._peek().value == '@':
            self._advance()
            dir_name = self._match(TokenType.NAME).value
            args = {}
            if self._peek().value == '(':
                self._advance()
                while self._peek().value != ')':
                    arg_name = self._match(TokenType.NAME).value
                    self._match(TokenType.PUNCTUATION, ':')
                    arg_val = self._parse_value()
                    args[arg_name] = arg_val
                    if self._peek().value == ',':
                        self._advance()
                self._match(TokenType.PUNCTUATION, ')')
            dirs[dir_name] = args
        return dirs


# =============================================================================
#  SSDM converter – maps parsed schema to SSDM_DOCUMENT
# =============================================================================
class GraphQLServiceParser(BaseSSDMParser):
    name = "graphql_service"
    supported_extensions = (".graphql", ".gql", ".graphqls")

    async def _parse_to_document(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> SSDM_DOCUMENT:
        text = data.decode(options.encoding)
        parser = GraphQLParser(text)
        schema = parser.parse()

        # Build MSDM entities for all types
        entities = []
        for type_name, gql_type in schema.types.items():
            entity = self._convert_type_to_entity(gql_type, schema.types)
            if entity:
                entities.append(entity)
        msdm_doc = MSDMDocument(entities=entities) if entities else None

        # Generate operations for queries, mutations, subscriptions
        operations = []
        operations.extend(self._fields_to_operations(schema, schema.query_type, "query"))
        operations.extend(self._fields_to_operations(schema, schema.mutation_type, "mutation"))
        operations.extend(self._fields_to_operations(schema, schema.subscription_type, "subscription"))

        # GraphQLService object
        graphql_service = GraphQLService(
            schema_entity=Entity(  # placeholder for the root schema
                name="Root",
                attributes=[],
                description="GraphQL root schema"
            )
        )

        doc = SSDM_DOCUMENT(
            document_id="",
            title=source_name,
            version="1.0.0",
            description=f"GraphQL schema from {source_name}",
            type_definitions=msdm_doc,
            operations=operations,
            graphql_service=graphql_service,
            servers=[],
            security_schemes=[],
            metadata={
                "graphql:directives": schema.directives,
            }
        )
        doc.is_valid = True
        return doc

    def _convert_type_to_entity(self, gql_type: GraphQLType, all_types: Dict[str, GraphQLType]) -> Optional[Entity]:
        """Convert a GraphQLType to an MSDM Entity."""
        if gql_type.kind == GraphQLType.KIND_SCALAR:
            # Scalars are represented as simple entities with a single value attribute
            return Entity(name=gql_type.name, attributes=[Attribute(name="value", type="string")])

        if gql_type.kind == GraphQLType.KIND_ENUM:
            # Enum can be represented as a string, or an Entity with one string attribute
            desc = f"Enum values: {', '.join(gql_type.enum_values)}"
            return Entity(name=gql_type.name, attributes=[Attribute(name="value", type="string")], description=desc)

        if gql_type.kind in (GraphQLType.KIND_OBJECT, GraphQLType.KIND_INTERFACE):
            attrs = []
            for field in gql_type.fields:
                attr_type = self._map_gql_type_to_string(field.type_ref)
                attr = Attribute(
                    name=field.name,
                    type=attr_type,
                    description=field.description,
                    deprecated=("deprecated" in field.directives),
                )
                # Store arguments metadata
                if field.arguments:
                    attr.metadata["arguments"] = field.arguments
                # Store directives
                if field.directives:
                    attr.metadata["directives"] = field.directives
                attrs.append(attr)

            entity = Entity(
                name=gql_type.name,
                attributes=attrs,
                description=gql_type.description,
                deprecated=("deprecated" in gql_type.directives),
            )
            # Interfaces are stored as composition? We can mark them with metadata.
            if gql_type.interfaces:
                entity.metadata["implements"] = gql_type.interfaces
            # Union members are handled differently (union is not an object)
            return entity

        if gql_type.kind == GraphQLType.KIND_INPUT_OBJECT:
            attrs = []
            for field in gql_type.fields:
                attr_type = self._map_gql_type_to_string(field.type_ref)
                attr = Attribute(name=field.name, type=attr_type, description=field.description)
                if field.directives:
                    attr.metadata["directives"] = field.directives
                attrs.append(attr)
            return Entity(name=gql_type.name, attributes=attrs, description=gql_type.description)

        if gql_type.kind == GraphQLType.KIND_UNION:
            # Union as composition entity
            members = []
            for member_name in gql_type.union_members:
                # Create placeholder Entity for member (could reference real entity if exists)
                member_entity = Entity(name=member_name, attributes=[])
                members.append(member_entity)
            composition = CompositionEntity(
                composition_type="oneOf",
                members=members,
                description=f"Union of {', '.join(gql_type.union_members)}"
            )
            return Entity(
                name=gql_type.name,
                attributes=[],
                composition=composition,
                description=gql_type.description,
            )

        return None

    def _map_gql_type_to_string(self, type_ref: str) -> str:
        """Convert a GraphQL type reference string to an MSDM type string."""
        # Handle lists and non-null
        non_null = type_ref.endswith('!')
        name = type_ref.rstrip('!')
        if name.startswith('[') and name.endswith(']'):
            inner = name[1:-1]
            inner_type = self._map_gql_type_to_string(inner)
            return f"array<{inner_type}>"
        # Map standard scalars
        scalars = {
            'String': 'string',
            'Int': 'int',
            'Float': 'float',
            'Boolean': 'boolean',
            'ID': 'string',
        }
        return scalars.get(name, name)  # custom type

    def _fields_to_operations(self, schema: GraphQLSchema, root_type: Optional[str], operation_kind: str) -> List[Operation]:
        if not root_type:
            return []
        root = schema.types.get(root_type)
        if not root:
            return []
        ops = []
        for field in root.fields:
            # Build parameters from arguments
            params = []
            for arg_name, arg_type, default in field.arguments:
                param_type = self._map_gql_type_to_string(arg_type)
                params.append(Parameter(
                    name=arg_name,
                    location=ParameterLocation.BODY,  # GraphQL arguments are typically in the body
                    type_string=param_type,
                    required=(not arg_type.endswith('!') and default is None)  # if non-null and no default -> required
                ))
            # The return type is stored in response
            return_type = self._map_gql_type_to_string(field.type_ref)
            # Create a placeholder response with an entity representing the return type
            resp_entity = Entity(
                name=f"{root_type}_{field.name}_response",
                attributes=[Attribute(name="data", type=return_type)],
            )
            response = Response(
                status_code="200",  # not HTTP, but we use a fixed code
                description=f"Return type: {field.type_ref}",
                content_entity=resp_entity,
            )
            operation = Operation(
                name=field.name,
                type=OperationType.REQUEST_RESPONSE,
                description=field.description or f"{operation_kind} {field.name}",
                http_method=None,
                path=f"graphql:{operation_kind}:{field.name}",
                parameters=params,
                responses=[response],
                tags=[operation_kind.capitalize()],
                deprecated=("deprecated" in field.directives),
            )
            ops.append(operation)
        return ops