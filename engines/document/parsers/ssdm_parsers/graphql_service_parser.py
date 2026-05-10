# engines/document/parsers/ssdm_parsers/graphql_service_parser.py
"""
GraphQL SDL parser → SSDMDocument
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ...models.media_types import MEDIA_TYPES
from ...models.msdm_models import (
    Annotation, Attribute, CompositionType, DataType, Entity,
    EntityComposition, EntityKind, MSDMDocument, ScalarType, VersionStatus
)
from ...models.ssdm_models import (
    ServiceOperation, OperationType, Parameter, ParameterLocation, Response, SSDMDocument
)
from ..base import ParseOptions
from .base_ssdm_parser import BaseSSDMParser


# =============================================================================
#  GraphQL SDL Lexer & AST
# =============================================================================

# _Token types
class _TokenType:
    NAME = "NAME"
    STRING = "STRING"
    INT = "INT"
    FLOAT = "FLOAT"
    PUNCTUATION = "PUNCTUATION"
    COMMENT = "COMMENT"
    EOF = "EOF"


@dataclass
class _Token:
    type: str
    value: str
    line: int = 0
    col: int = 0


class _GraphQLScanner:
    """Simple scanner for GraphQL SDL."""
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1
        self.col = 1

    def peek(self) -> _Token:
        return self._next_token(skip=False)

    def next(self) -> _Token:
        return self._next_token(skip=True)

    def _next_token(self, skip: bool) -> _Token:
        self._skip_whitespace_and_comments()
        if self.pos >= len(self.text):
            return _Token(_TokenType.EOF, "", self.line, self.col)

        ch = self.text[self.pos]

        # Names
        if ch.isalpha() or ch == '_':
            start = self.pos
            while self.pos < len(self.text) and (self.text[self.pos].isalnum() or self.text[self.pos] == '_'):
                self.pos += 1
            value = self.text[start:self.pos]
            return _Token(_TokenType.NAME, value, self.line, self.col)

        # Numbers
        if ch.isdigit() or (ch == '-' and self.pos + 1 < len(self.text) and self.text[self.pos + 1].isdigit()):
            return self._scan_number()

        # Strings (single or double quoted)
        if ch in ('"', "'"):
            return self._scan_string()

        # Punctuation
        puncts = ['!', '$', '(', ')', '{', '}', '[', ']', ':', ',', '=', '@', '|', '&']
        if ch in puncts:
            self.pos += 1
            return _Token(_TokenType.PUNCTUATION, ch, self.line, self.col)

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

    def _scan_number(self) -> _Token:
        start = self.pos
        if self.text[self.pos] == '-':
            self.pos += 1
        while self.pos < len(self.text) and self.text[self.pos].isdigit():
            self.pos += 1
        if self.pos < len(self.text) and self.text[self.pos] == '.':
            self.pos += 1
            while self.pos < len(self.text) and self.text[self.pos].isdigit():
                self.pos += 1
            return _Token(_TokenType.FLOAT, self.text[start:self.pos], self.line, self.col)
        return _Token(_TokenType.INT, self.text[start:self.pos], self.line, self.col)

    def _scan_string(self) -> _Token:
        quote = self.text[self.pos]
        start = self.pos
        self.pos += 1  # opening quote
        while self.pos < len(self.text):
            ch = self.text[self.pos]
            if ch == quote and self.text[self.pos - 1] != '\\':
                self.pos += 1
                return _Token(_TokenType.STRING, self.text[start:self.pos], self.line, self.col)
            self.pos += 1
        raise SyntaxError("Unterminated string")


# =============================================================================
#  Parser – builds an internal schema representation
# =============================================================================

class _GraphQLField:
    def __init__(self, name: str):
        self.name = name
        self.type_ref: str = ""      # e.g., "String!", "[Todo!]!"
        self.arguments: list[tuple[str, str, str | None]] = []  # (name, type, default)
        self.description: str | None = None
        self.directives: dict[str, dict[str, str]] = {}


class _GraphQLType:
    KIND_OBJECT = "OBJECT"
    KIND_INPUT_OBJECT = "INPUT_OBJECT"
    KIND_ENUM = "ENUM"
    KIND_UNION = "UNION"
    KIND_INTERFACE = "INTERFACE"
    KIND_SCALAR = "SCALAR"

    def __init__(self, name: str, kind: str):
        self.name = name
        self.kind = kind
        self.description: str | None = None
        self.fields: list[_GraphQLField] = []
        self.interfaces: list[str] = []  # for objects/interfaces
        self.union_members: list[str] = []  # for unions
        self.enum_values: list[str] = []  # for enums
        self.directives: dict[str, dict[str, str]] = {}


class _GraphQLSchema:
    def __init__(self) -> None:
        self.types: dict[str, _GraphQLType] = {}
        self.query_type: str | None = None
        self.mutation_type: str | None = None
        self.subscription_type: str | None = None
        self.directives: list[dict] = []  # custom directive definitions


class _GraphQLParser:
    """Recursive descendant parser for GraphQL SDL."""

    def __init__(self, text: str):
        self.scanner = _GraphQLScanner(text)
        self.schema = _GraphQLSchema()
        self._current_description: str | None = None
        # Initialize lookahead; it will never be None after this
        self._lookahead = self.scanner.next()

    def parse(self) -> _GraphQLSchema:
        while self._lookahead.type != _TokenType.EOF:
            self._parse_schema_definition()
        return self.schema

    def _match(self, expected_type: str, expected_value: str | None = None) -> _Token:
        if self._lookahead.type != expected_type:
            raise SyntaxError(f"Expected {expected_type} but got {self._lookahead.type}")
        if expected_value is not None and self._lookahead.value != expected_value:
            raise SyntaxError(f"Expected '{expected_value}' but got '{self._lookahead.value}'")
        token = self._lookahead
        self._advance()
        return token

    def _advance(self):
        self._lookahead = self.scanner.next()

    def _peek(self) -> _Token:
        return self._lookahead

    # ------------------------------------------------------------------
    #  Top-level definitions
    # ------------------------------------------------------------------
    def _parse_schema_definition(self):
        # Collect description strings (multiple possible)
        while self._peek().type == _TokenType.STRING:
            desc_token = self._peek()
            self._advance()
            self._current_description = desc_token.value.strip('"').strip("'")

        token = self._peek()
        if token.type == _TokenType.NAME:
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
                self._advance()
                self._skip_block()
            else:
                self._advance()
        elif token.type == _TokenType.PUNCTUATION and token.value == '{':
            self._parse_schema_block()
        else:
            self._advance()

    def _skip_block(self):
        depth = 0
        while self._peek().type != _TokenType.EOF:
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
    #  Object type
    # ------------------------------------------------------------------
    def _parse_object_type(self):
        self._advance()  # 'type'
        name = self._match(_TokenType.NAME).value
        type_def = _GraphQLType(name, _GraphQLType.KIND_OBJECT)
        if self._current_description:
            type_def.description = self._current_description
            self._current_description = None

        if self._peek().value == 'implements':
            self._advance()
            interfaces = []
            while self._peek().value != '{':
                if self._peek().value == '&':
                    self._advance()
                    continue
                interfaces.append(self._match(_TokenType.NAME).value)
            type_def.interfaces = interfaces

        type_def.directives = self._parse_directives()
        self._match(_TokenType.PUNCTUATION, '{')
        while self._peek().value != '}':
            type_def.fields.append(self._parse_field())
        self._match(_TokenType.PUNCTUATION, '}')
        self.schema.types[name] = type_def

    # ------------------------------------------------------------------
    #  Input object type
    # ------------------------------------------------------------------
    def _parse_input_object_type(self):
        self._advance()
        name = self._match(_TokenType.NAME).value
        type_def = _GraphQLType(name, _GraphQLType.KIND_INPUT_OBJECT)
        if self._current_description:
            type_def.description = self._current_description
            self._current_description = None
        type_def.directives = self._parse_directives()
        self._match(_TokenType.PUNCTUATION, '{')
        while self._peek().value != '}':
            field = _GraphQLField(name=self._match(_TokenType.NAME).value)
            self._match(_TokenType.PUNCTUATION, ':')
            field.type_ref = self._parse_type_reference()
            if self._peek().value == '=':
                self._advance()
                field.arguments.append(('default', 'String', self._parse_value()))
            field.directives = self._parse_directives()
            type_def.fields.append(field)
        self._match(_TokenType.PUNCTUATION, '}')
        self.schema.types[name] = type_def

    # ------------------------------------------------------------------
    #  Enum type
    # ------------------------------------------------------------------
    def _parse_enum_type(self):
        self._advance()
        name = self._match(_TokenType.NAME).value
        type_def = _GraphQLType(name, _GraphQLType.KIND_ENUM)
        if self._current_description:
            type_def.description = self._current_description
            self._current_description = None
        type_def.directives = self._parse_directives()
        self._match(_TokenType.PUNCTUATION, '{')
        while self._peek().value != '}':
            val = self._match(_TokenType.NAME).value
            type_def.enum_values.append(val)
        self._match(_TokenType.PUNCTUATION, '}')
        self.schema.types[name] = type_def

    # ------------------------------------------------------------------
    #  Union type
    # ------------------------------------------------------------------
    def _parse_union_type(self):
        self._advance()
        name = self._match(_TokenType.NAME).value
        type_def = _GraphQLType(name, _GraphQLType.KIND_UNION)
        if self._current_description:
            type_def.description = self._current_description
            self._current_description = None
        self._match(_TokenType.PUNCTUATION, '=')
        while True:
            member = self._match(_TokenType.NAME).value
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
        self._advance()
        name = self._match(_TokenType.NAME).value
        type_def = _GraphQLType(name, _GraphQLType.KIND_INTERFACE)
        if self._current_description:
            type_def.description = self._current_description
            self._current_description = None
        type_def.directives = self._parse_directives()
        self._match(_TokenType.PUNCTUATION, '{')
        while self._peek().value != '}':
            type_def.fields.append(self._parse_field())
        self._match(_TokenType.PUNCTUATION, '}')
        self.schema.types[name] = type_def

    # ------------------------------------------------------------------
    #  Scalar type
    # ------------------------------------------------------------------
    def _parse_scalar_type(self):
        self._advance()
        name = self._match(_TokenType.NAME).value
        type_def = _GraphQLType(name, _GraphQLType.KIND_SCALAR)
        if self._current_description:
            type_def.description = self._current_description
            self._current_description = None
        type_def.directives = self._parse_directives()
        self.schema.types[name] = type_def

    # ------------------------------------------------------------------
    #  Schema block
    # ------------------------------------------------------------------
    def _parse_schema_block(self):
        if self._peek().value == 'schema':
            self._advance()
        self._match(_TokenType.PUNCTUATION, '{')
        while self._peek().value != '}':
            kw = self._match(_TokenType.NAME).value
            self._match(_TokenType.PUNCTUATION, ':')
            type_name = self._match(_TokenType.NAME).value
            if kw == 'query':
                self.schema.query_type = type_name
            elif kw == 'mutation':
                self.schema.mutation_type = type_name
            elif kw == 'subscription':
                self.schema.subscription_type = type_name
        self._match(_TokenType.PUNCTUATION, '}')

    # ------------------------------------------------------------------
    #  Directive definition (skip)
    # ------------------------------------------------------------------
    def _parse_directive_definition(self):
        self._advance()
        while self._peek().value != '{':
            self._advance()
        self._skip_block()

    # ------------------------------------------------------------------
    #  Field parsing
    # ------------------------------------------------------------------
    def _parse_field(self) -> _GraphQLField:
        if self._peek().type == _TokenType.STRING:
            desc = self._peek().value.strip('"')
            self._advance()
        else:
            desc = None
        field_name = self._match(_TokenType.NAME).value
        field = _GraphQLField(field_name)
        if desc:
            field.description = desc
        if self._peek().value == '(':
            self._advance()
            while self._peek().value != ')':
                arg_name = self._match(_TokenType.NAME).value
                self._match(_TokenType.PUNCTUATION, ':')
                arg_type = self._parse_type_reference()
                default = None
                if self._peek().value == '=':
                    self._advance()
                    default = self._parse_value()
                field.arguments.append((arg_name, arg_type, default))
                if self._peek().value == ',':
                    self._advance()
            self._match(_TokenType.PUNCTUATION, ')')
        self._match(_TokenType.PUNCTUATION, ':')
        field.type_ref = self._parse_type_reference()
        field.directives = self._parse_directives()
        return field

    def _parse_type_reference(self) -> str:
        type_str = ""
        if self._peek().value == '[':
            self._advance()
            inner = self._parse_type_reference()
            self._match(_TokenType.PUNCTUATION, ']')
            type_str = f"[{inner}]"
        else:
            type_str = self._match(_TokenType.NAME).value
        if self._peek().value == '!':
            self._advance()
            type_str += "!"
        return type_str

    def _parse_value(self) -> str:
        token = self._peek()
        if token.type == _TokenType.NAME and token.value in ('true', 'false', 'null'):
            self._advance()
            return token.value
        elif token.type in (_TokenType.INT, _TokenType.FLOAT, _TokenType.STRING):
            self._advance()
            return token.value
        elif token.value == '[':
            self._advance()
            values = []
            while self._peek().value != ']':
                values.append(self._parse_value())
                if self._peek().value == ',':
                    self._advance()
            self._match(_TokenType.PUNCTUATION, ']')
            return f"[{','.join(values)}]"
        elif token.value == '{':
            self._advance()
            pairs = []
            while self._peek().value != '}':
                key = self._match(_TokenType.NAME).value
                self._match(_TokenType.PUNCTUATION, ':')
                val = self._parse_value()
                pairs.append(f"{key}:{val}")
                if self._peek().value == ',':
                    self._advance()
            self._match(_TokenType.PUNCTUATION, '}')
            return f"{{{','.join(pairs)}}}"
        raise SyntaxError(f"Unexpected value token: {token}")

    def _parse_directives(self) -> dict[str, dict[str, str]]:
        dirs = {}
        while self._peek().value == '@':
            self._advance()
            dir_name = self._match(_TokenType.NAME).value
            args = {}
            if self._peek().value == '(':
                self._advance()
                while self._peek().value != ')':
                    arg_name = self._match(_TokenType.NAME).value
                    self._match(_TokenType.PUNCTUATION, ':')
                    arg_val = self._parse_value()
                    args[arg_name] = arg_val
                    if self._peek().value == ',':
                        self._advance()
                self._match(_TokenType.PUNCTUATION, ')')
            dirs[dir_name] = args
        return dirs


# =============================================================================
#  SSDM converter – maps parsed schema to SSDMDocument
# =============================================================================
class GraphQLServiceParser(BaseSSDMParser):
    name = "graphql_service"
    supported_extensions = (".graphql", ".gql", ".graphqls")

    async def _parse_to_document(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> SSDMDocument:
        text = data.decode(options.encoding)
        parser = _GraphQLParser(text)
        schema = parser.parse()

        # Build MSDM entities for all types
        entities: list[Entity] = []
        for type_name, gql_type in schema.types.items():
            entity = self._convert_type_to_entity(gql_type, schema.types)
            if entity:
                entities.append(entity)
        msdm_doc = None
        if entities:
            msdm_doc = MSDMDocument(
                title="graphql_types",
                document_id=f"{source_name}_types",
                media_type=MEDIA_TYPES["msdm"],  # MediaType object
                entities=entities
            )

        # Generate operations
        operations: list[ServiceOperation] = []
        operations.extend(self._fields_to_operations(schema, schema.query_type, "query", msdm_doc))
        operations.extend(self._fields_to_operations(schema, schema.mutation_type, "mutation", msdm_doc))
        operations.extend(self._fields_to_operations(schema, schema.subscription_type, "subscription", msdm_doc))

        metadata: dict[str, Any] = {
            "graphql:directives": schema.directives,
            "graphql:query_type": schema.query_type,
            "graphql:mutation_type": schema.mutation_type,
            "graphql:subscription_type": schema.subscription_type,
        }

        doc = SSDMDocument(
            document_id=source_name,
            title=source_name,
            version="1.0.0",
            media_type=MEDIA_TYPES.get("graphql", MEDIA_TYPES["txt"]),
            description=f"GraphQL schema from {source_name}",
            type_definitions=msdm_doc,
            operations=operations,
            metadata=metadata,
        )
        doc.is_valid = True
        return doc

    # ------------------------------------------------------------------
    #  Type conversion helpers
    # ------------------------------------------------------------------
    def _convert_type_to_entity(self, gql_type: _GraphQLType, all_types: dict[str, _GraphQLType]) -> Entity | None:
        if gql_type.kind == _GraphQLType.KIND_SCALAR:
            attr = Attribute(name="value", data_type=DataType(base=ScalarType.STRING))
            return Entity(
                name=gql_type.name,
                kind=EntityKind.OBJECT,
                attributes=[attr],
                description=gql_type.description
            )

        if gql_type.kind == _GraphQLType.KIND_ENUM:
            attr = Attribute(name="value", data_type=DataType(base=ScalarType.STRING))
            entity = Entity(
                name=gql_type.name,
                kind=EntityKind.OBJECT,
                attributes=[attr],
                description=gql_type.description
            )
            entity.annotations.append(Annotation(key="enum_values", value=",".join(gql_type.enum_values)))
            return entity

        if gql_type.kind in (_GraphQLType.KIND_OBJECT, _GraphQLType.KIND_INTERFACE):
            attrs = []
            for field in gql_type.fields:
                data_type = self._map_gql_type_to_datatype(field.type_ref, all_types)
                attr = Attribute(
                    name=field.name,
                    data_type=data_type,
                    description=field.description or "",
                )
                if "deprecated" in field.directives:
                    attr.version_status = VersionStatus.DEPRECATED
                if field.arguments:
                    attr.annotations.append(Annotation(key="arguments", value=str(field.arguments)))
                if field.directives:
                    attr.annotations.append(Annotation(key="directives", value=str(field.directives)))
                attrs.append(attr)

            entity = Entity(
                name=gql_type.name,
                kind=EntityKind.OBJECT,
                attributes=attrs,
                description=gql_type.description,
            )
            if "deprecated" in gql_type.directives:
                entity.version_status = VersionStatus.DEPRECATED
            if gql_type.interfaces:
                entity.annotations.append(Annotation(key="implements", value=",".join(gql_type.interfaces)))
            return entity

        if gql_type.kind == _GraphQLType.KIND_INPUT_OBJECT:
            attrs = []
            for field in gql_type.fields:
                data_type = self._map_gql_type_to_datatype(field.type_ref, all_types)
                attr = Attribute(
                    name=field.name,
                    data_type=data_type,
                    description=field.description or ""
                )
                if field.directives:
                    attr.annotations.append(Annotation(key="directives", value=str(field.directives)))
                attrs.append(attr)
            return Entity(
                name=gql_type.name,
                kind=EntityKind.OBJECT,
                attributes=attrs,
                description=gql_type.description
            )

        if gql_type.kind == _GraphQLType.KIND_UNION:
            member_names = gql_type.union_members
            composition = EntityComposition(
                composition_type=CompositionType.ONE_OF,
                member_ids=member_names,
                description=f"Union of {', '.join(member_names)}"
            )
            return Entity(
                name=gql_type.name,
                kind=EntityKind.OBJECT,
                attributes=[],
                composition=composition,
                description=gql_type.description,
            )

        return None

    def _map_gql_type_to_datatype(self, type_ref: str, all_types: dict[str, _GraphQLType]) -> DataType:
        base_ref = type_ref.rstrip('!')
        if base_ref.startswith('[') and base_ref.endswith(']'):
            inner = base_ref[1:-1]
            element_dt = self._map_gql_type_to_datatype(inner, all_types)
            return DataType(base=ScalarType.ARRAY, element_type=element_dt)
        scalar_map = {
            'String': ScalarType.STRING,
            'Int': ScalarType.INT,
            'Float': ScalarType.FLOAT,
            'Boolean': ScalarType.BOOLEAN,
            'ID': ScalarType.STRING,
        }
        if base_ref in scalar_map:
            return DataType(base=scalar_map[base_ref])
        else:
            return DataType(base=ScalarType.REF, ref_entity_id=base_ref)

    # ------------------------------------------------------------------
    #  ServiceOperation generation
    # ------------------------------------------------------------------
    def _fields_to_operations(
        self,
        schema: _GraphQLSchema,
        root_type: str | None,
        operation_kind: str,
        msdm_doc: MSDMDocument | None
    ) -> list[ServiceOperation]:
        if not root_type:
            return []
        root = schema.types.get(root_type)
        if not root:
            return []
        ops = []
        for field in root.fields:
            params = []
            for arg_name, arg_type, default in field.arguments:
                param = Parameter(
                    name=arg_name,
                    location=ParameterLocation.BODY,
                    description=f"Argument of type {arg_type}",
                    type_entity=None,
                )
                param.annotations.append(Annotation(key="graphql_type", value=arg_type))
                if default is not None:
                    param.annotations.append(Annotation(key="default", value=str(default)))
                param.required = arg_type.endswith('!') and default is None
                params.append(param)

            return_type_ref = field.type_ref
            return_entity_name = f"{root_type}_{field.name}_response"
            return_dt = self._map_gql_type_to_datatype(return_type_ref, schema.types)
            resp_attr = Attribute(name="data", data_type=return_dt)
            resp_entity = Entity(
                name=return_entity_name,
                kind=EntityKind.OBJECT,
                attributes=[resp_attr],
                description=f"Response type for {field.name}"
            )
            if msdm_doc:
                msdm_doc.entities.append(resp_entity)
            response = Response(
                status_code="200",
                description=f"Return type: {return_type_ref}",
                content_entity=resp_entity,
            )

            operation = ServiceOperation(
                name=field.name,
                type=OperationType.REQUEST_RESPONSE,
                description=field.description or f"{operation_kind} {field.name}",
                http_method=None,
                path=f"graphql:{operation_kind}:{field.name}",
                parameters=params,
                responses=[response],
            )
            if "deprecated" in field.directives:
                operation.version_status = VersionStatus.DEPRECATED
            ops.append(operation)
        return ops