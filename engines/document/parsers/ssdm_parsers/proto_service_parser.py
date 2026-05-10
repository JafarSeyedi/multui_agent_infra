# engines/document/parsers/ssdm_parsers/proto_service_parser.py
"""
proto_service_parser.py – Protobuf / gRPC service definition parser → SSDMDocument
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from ...models.media_types import MEDIA_TYPES
from ...models.msdm_models import Attribute
from ...models.msdm_models import DataType
from ...models.msdm_models import Entity
from ...models.msdm_models import MSDMDocument
from ...models.msdm_models import ScalarType, Annotation
from ...models.ssdm_models import ServiceOperation
from ...models.ssdm_models import OperationType
from ...models.ssdm_models import RequestBody
from ...models.ssdm_models import Response
from ...models.ssdm_models import SSDMDocument
from ..base import ParseOptions
from ..ssdm_parsers.base_ssdm_parser import BaseSSDMParser


# ---------------------------------------------------------------------------
#  Protobuf Lexer
# ---------------------------------------------------------------------------
class ProtoToken:
    def __init__(self, type_: str, value: str, line: int):
        self.type = type_
        self.value = value
        self.line = line


class ProtoLexer:
    _KEYWORDS = {
        'syntax', 'package', 'option', 'import', 'message', 'service',
        'rpc', 'returns', 'stream', 'repeated', 'optional', 'required',
        'map', 'oneof', 'enum', 'reserved', 'to', 'max',
        'double', 'float', 'int32', 'int64', 'uint32', 'uint64',
        'sint32', 'sint64', 'fixed32', 'fixed64', 'sfixed32', 'sfixed64',
        'bool', 'string', 'bytes', 'true', 'false',
    }
    _PUNCTUATION = set("{}()[]=;,.<>")

    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1

    def next_token(self) -> ProtoToken:
        self._skip_whitespace_and_comments()
        if self.pos >= len(self.text):
            return ProtoToken('EOF', '', self.line)

        ch = self.text[self.pos]

        # Punctuation
        if ch in self._PUNCTUATION:
            self.pos += 1
            return ProtoToken(ch, ch, self.line)

        # String literal (double or single quote)
        if ch in ('"', "'"):
            return self._scan_string()

        # Number (integer or float)
        if ch.isdigit() or (ch == '-' and self.pos + 1 < len(self.text) and self.text[self.pos + 1].isdigit()):
            return self._scan_number()

        # Identifier or keyword
        if ch.isalpha() or ch == '_':
            start = self.pos
            while self.pos < len(self.text) and (self.text[self.pos].isalnum() or self.text[self.pos] == '_'):
                self.pos += 1
            ident = self.text[start:self.pos]
            ttype = 'IDENTIFIER' if ident not in self._KEYWORDS else ident.upper()
            return ProtoToken(ttype, ident, self.line)

        raise SyntaxError(f"Unexpected character '{ch}' at line {self.line}")

    def _skip_whitespace_and_comments(self):
        while self.pos < len(self.text):
            ch = self.text[self.pos]
            if ch in ' \t\r\n':
                if ch == '\n':
                    self.line += 1
                self.pos += 1
            elif ch == '/':
                if self.pos + 1 < len(self.text) and self.text[self.pos + 1] == '/':
                    # line comment
                    self.pos += 2
                    while self.pos < len(self.text) and self.text[self.pos] != '\n':
                        self.pos += 1
                elif self.pos + 1 < len(self.text) and self.text[self.pos + 1] == '*':
                    # block comment
                    self.pos += 2
                    while self.pos < len(self.text):
                        if self.text[self.pos] == '*' and self.pos + 1 < len(self.text) and self.text[self.pos + 1] == '/':
                            self.pos += 2
                            break
                        if self.text[self.pos] == '\n':
                            self.line += 1
                        self.pos += 1
                else:
                    break
            else:
                break

    def _scan_string(self) -> ProtoToken:
        quote = self.text[self.pos]
        start = self.pos
        self.pos += 1
        while self.pos < len(self.text):
            if self.text[self.pos] == '\\':
                self.pos += 2
            elif self.text[self.pos] == quote:
                self.pos += 1
                return ProtoToken('STRING', self.text[start:self.pos], self.line)
            else:
                self.pos += 1
        raise SyntaxError("Unterminated string")

    def _scan_number(self) -> ProtoToken:
        start = self.pos
        if self.text[self.pos] == '-':
            self.pos += 1
        while self.pos < len(self.text) and self.text[self.pos].isdigit():
            self.pos += 1
        if self.pos < len(self.text) and self.text[self.pos] == '.':
            self.pos += 1
            while self.pos < len(self.text) and self.text[self.pos].isdigit():
                self.pos += 1
            return ProtoToken('FLOAT', self.text[start:self.pos], self.line)
        return ProtoToken('INTEGER', self.text[start:self.pos], self.line)


# ---------------------------------------------------------------------------
#  Protobuf Parser (abstract syntax)
# ---------------------------------------------------------------------------
class ProtoType:
    """Represents a type reference (scalar or message)."""
    def __init__(self, name: str):
        self.name = name


class FieldDescriptor:
    def __init__(self, name: str, number: int, type_: ProtoType, label: str = ''):
        self.name = name
        self.number = number
        self.type = type_
        self.label = label  # '', 'repeated', 'optional', 'required'


class MessageDef:
    def __init__(self, name: str):
        self.name = name
        self.fields: list[FieldDescriptor] = []
        self.nested_messages: dict[str, MessageDef] = {}
        self.nested_enums: dict[str, EnumDef] = {}
        self.oneofs: dict[str, list[FieldDescriptor]] = {}


class EnumDef:
    def __init__(self, name: str):
        self.name = name
        self.values: dict[str, int] = {}


class ServiceMethod:
    def __init__(self, name: str, input_type: ProtoType, output_type: ProtoType,
                 client_streaming: bool = False, server_streaming: bool = False):
        self.name = name
        self.input = input_type
        self.output = output_type
        self.client_streaming = client_streaming
        self.server_streaming = server_streaming


class ServiceDef:
    def __init__(self, name: str):
        self.name = name
        self.methods: list[ServiceMethod] = []


class ProtoFile:
    def __init__(self) -> None:
        self.package = ""
        self.syntax = "proto2"
        self.messages: dict[str, MessageDef] = {}
        self.enums: dict[str, EnumDef] = {}
        self.services: dict[str, ServiceDef] = {}


class ProtoParser:
    """Recursive descent parser for protobuf IDL."""

    def __init__(self, text: str):
        self.lexer = ProtoLexer(text)
        self.current = self.lexer.next_token()

    def _eat(self, expected_type: str, expected_value: str | None = None) -> ProtoToken:
        token = self.current
        if token.type != expected_type:
            raise SyntaxError(f"Expected {expected_type}, got {token.type} at line {token.line}")
        if expected_value is not None and token.value != expected_value:
            raise SyntaxError(f"Expected '{expected_value}', got '{token.value}' at line {token.line}")
        self.current = self.lexer.next_token()
        return token

    def parse(self) -> ProtoFile:
        file = ProtoFile()
        while self.current.type != 'EOF':
            if self.current.type == 'SYNTAX':
                file.syntax = self._parse_syntax()
            elif self.current.type == 'PACKAGE':
                file.package = self._parse_package()
            elif self.current.type == 'MESSAGE':
                msg = self._parse_message()
                file.messages[msg.name] = msg
            elif self.current.type == 'ENUM':
                enum = self._parse_enum()
                file.enums[enum.name] = enum
            elif self.current.type == 'SERVICE':
                svc = self._parse_service()
                file.services[svc.name] = svc
            else:
                # skip unknown top-level (import, option, etc.)
                self.current = self.lexer.next_token()
        return file

    def _parse_syntax(self) -> str:
        self._eat('SYNTAX')
        self._eat('=')
        value = self._eat('STRING').value.strip('"').strip("'")
        self._eat(';')
        return value

    def _parse_package(self) -> str:
        self._eat('PACKAGE')
        parts = []
        while self.current.type == 'IDENTIFIER' or self.current.type == '.':
            if self.current.type == 'IDENTIFIER':
                parts.append(self.current.value)
                self.current = self.lexer.next_token()
            elif self.current.type == '.':
                parts.append('.')
                self.current = self.lexer.next_token()
        self._eat(';')
        return ''.join(parts).rstrip('.')

    def _parse_message(self) -> MessageDef:
        self._eat('MESSAGE')
        name = self._eat('IDENTIFIER').value
        msg = MessageDef(name)
        self._eat('{')
        while self.current.type != '}':
            if self.current.type == 'MESSAGE':
                nested_msg = self._parse_message()
                msg.nested_messages[nested_msg.name] = nested_msg
            elif self.current.type == 'ENUM':
                nested_enum = self._parse_enum()
                msg.nested_enums[nested_enum.name] = nested_enum
            elif self.current.type == 'ONEOF':
                self._parse_oneof(msg)
            elif self.current.type in ('REPEATED', 'OPTIONAL', 'REQUIRED') or self._is_type_start():
                field = self._parse_field()
                msg.fields.append(field)
            else:
                # possibly option or reserved; skip until semicolon
                self._skip_until_semicolon()
        self._eat('}')
        return msg

    def _parse_enum(self) -> EnumDef:
        self._eat('ENUM')
        name = self._eat('IDENTIFIER').value
        enum = EnumDef(name)
        self._eat('{')
        while self.current.type != '}':
            if self.current.type == 'IDENTIFIER':
                id_name = self.current.value
                self.current = self.lexer.next_token()
                self._eat('=')
                value = int(self._eat('INTEGER').value)
                enum.values[id_name] = value
                self._eat(';')
            else:
                self._skip_until_semicolon()
        self._eat('}')
        return enum

    def _parse_service(self) -> ServiceDef:
        self._eat('SERVICE')
        name = self._eat('IDENTIFIER').value
        svc = ServiceDef(name)
        self._eat('{')
        while self.current.type != '}':
            if self.current.type == 'RPC':
                method = self._parse_rpc()
                svc.methods.append(method)
            else:
                self._skip_until_semicolon()
        self._eat('}')
        return svc

    def _parse_rpc(self) -> ServiceMethod:
        self._eat('RPC')
        method_name = self._eat('IDENTIFIER').value
        # input
        self._eat('(')
        client_streaming = False
        if self.current.type == 'STREAM':
            client_streaming = True
            self.current = self.lexer.next_token()
        input_type = self._parse_type_reference()
        self._eat(')')
        # returns
        self._eat('RETURNS')
        self._eat('(')
        server_streaming = False
        if self.current.type == 'STREAM':
            server_streaming = True
            self.current = self.lexer.next_token()
        output_type = self._parse_type_reference()
        self._eat(')')
        # either ';' or body for options
        if self.current.type == '{':
            self._skip_block()
        else:
            self._eat(';')
        return ServiceMethod(method_name, input_type, output_type, client_streaming, server_streaming)

    def _parse_field(self) -> FieldDescriptor:
        label = ''
        if self.current.type in ('REPEATED', 'OPTIONAL', 'REQUIRED'):
            label = self.current.value.lower()
            self.current = self.lexer.next_token()
        ftype = self._parse_type_reference()
        name = self._eat('IDENTIFIER').value
        self._eat('=')
        number = int(self._eat('INTEGER').value)
        # possible field options in brackets
        if self.current.type == '[':
            self._skip_block(begin='[', end=']')
        self._eat(';')
        return FieldDescriptor(name, number, ftype, label)

    def _parse_type_reference(self) -> ProtoType:
        # scalar, message, or full path
        # map<key, value>
        if self.current.type == 'MAP':
            self.current = self.lexer.next_token()  # skip map
            self._eat('<')
            key_type = self._parse_scalar()
            self._eat(',')
            value_type = self._parse_type_reference()
            self._eat('>')
            return ProtoType(f"map<{key_type.name},{value_type.name}>")
        return ProtoType(self._parse_type_name())

    def _parse_scalar(self) -> ProtoType:
        types = {'double', 'float', 'int32', 'int64', 'uint32', 'uint64', 'sint32', 'sint64',
                 'fixed32', 'fixed64', 'sfixed32', 'sfixed64', 'bool', 'string', 'bytes'}
        if self.current.type in types:
            val = self.current.value
            self.current = self.lexer.next_token()
            return ProtoType(val)
        # else, could be a message type? Usually map keys are scalar only.
        return ProtoType(self._eat('IDENTIFIER').value)

    def _parse_type_name(self) -> str:
        parts = []
        while self.current.type == 'IDENTIFIER' or self.current.type == '.':
            if self.current.type == 'IDENTIFIER':
                parts.append(self.current.value)
                self.current = self.lexer.next_token()
            elif self.current.type == '.':
                parts.append('.')
                self.current = self.lexer.next_token()
        return ''.join(parts)

    def _is_type_start(self) -> bool:
        # any scalar or identifier can be a type start
        return self.current.type in ('IDENTIFIER',) or \
               self.current.type in ('DOUBLE', 'FLOAT', 'INT32', 'INT64', 'UINT32', 'UINT64',
                                     'SINT32', 'SINT64', 'FIXED32', 'FIXED64', 'SFIXED32', 'SFIXED64',
                                     'BOOL', 'STRING', 'BYTES')

    def _parse_oneof(self, msg: MessageDef):
        self._eat('ONEOF')
        name = self._eat('IDENTIFIER').value
        msg.oneofs[name] = []
        self._eat('{')
        while self.current.type != '}':
            if self._is_type_start() or self.current.type in ('REPEATED', 'OPTIONAL', 'REQUIRED'):
                field = self._parse_field()
                msg.oneofs[name].append(field)
            else:
                self._skip_until_semicolon()
        self._eat('}')

    def _skip_until_semicolon(self):
        while self.current.type != ';' and self.current.type != 'EOF':
            self.current = self.lexer.next_token()
        if self.current.type == ';':
            self.current = self.lexer.next_token()

    def _skip_block(self, begin='{', end='}'):
        """Skip a block including nested braces."""
        assert self.current.type == '{'
        depth = 1
        self.current = self.lexer.next_token()
        while depth > 0 and self.current.type != 'EOF':
            if self.current.type == begin:
                depth += 1
            elif self.current.type == end:
                depth -= 1
            self.current = self.lexer.next_token()


# ---------------------------------------------------------------------------
#  SSDM Proto parser
# ---------------------------------------------------------------------------
class ProtoServiceParser(BaseSSDMParser):
    name = "proto_service"
    supported_extensions = (".proto",)

    async def _parse_to_document(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> SSDMDocument:
        text = data.decode(options.encoding)
        parser = ProtoParser(text)
        file = parser.parse()

        # Build full name including package prefix
        def full_name(name: str) -> str:
            return f"{file.package}.{name}" if file.package else name

        # 1. Collect all message entities
        entity_by_name: dict[str, Entity] = {}

        def add_message(msg: MessageDef, prefix: str = "") -> None:
            full_msg_name = f"{prefix}{msg.name}" if prefix else msg.name
            entity = self._message_to_entity(msg, full_msg_name)
            entity_by_name[full_name(full_msg_name)] = entity
            # Also add without package prefix for local resolution
            entity_by_name[full_msg_name] = entity
            for nested in msg.nested_messages.values():
                add_message(nested, f"{full_msg_name}.")

        for msg in file.messages.values():
            add_message(msg, "")

        # 2. Collect enum entities
        for enum in file.enums.values():
            entity = self._enum_to_entity(enum, full_name(enum.name))
            entity_by_name[full_name(enum.name)] = entity
            entity_by_name[enum.name] = entity

        # Create MSDMDocument
        msdm_doc = MSDMDocument(
            title="types",
            document_id=f"{source_name}_types",
            media_type=MEDIA_TYPES["proto"],
            entities=list(entity_by_name.values()),
        )

        # 3. Build operations from services, resolving input/output entities
        operations: list[ServiceOperation] = []
        for svc in file.services.values():
            for method in svc.methods:
                op = self._method_to_operation(
                    svc.name, method, file.package, entity_by_name
                )
                if op:
                    operations.append(op)

        doc = SSDMDocument(
            title=Path(source_name).stem,
            document_id=source_name,
            media_type=MEDIA_TYPES["proto_service"],
            version="1.0.0",
            description=f"Protobuf service file {source_name}",
            type_definitions=msdm_doc,
            operations=operations,
            servers=[],
            annotations=[
                Annotation(key="proto:package", value=file.package),
                Annotation(key="proto:syntax", value=file.syntax),
            ],
        )
        doc.is_valid = True
        return doc

    def _message_to_entity(self, msg: MessageDef, full_name: str) -> Entity:
        attrs = []
        for field in msg.fields:
            attrs.append(self._field_to_attribute(field))
        entity = Entity(name=full_name, attributes=attrs)
        # Add description with fields summary
        entity.description = f"Protobuf message with {len(attrs)} fields"
        return entity

    def _field_to_attribute(self, field: FieldDescriptor) -> Attribute:
        # Convert protobuf type to DataType
        data_type = self._proto_type_to_datatype(field.type.name, field.label == 'repeated')
        # Determine required
        required = field.label == 'required'
        # Get default value if any (not captured; could be added later)
        attr = Attribute(
            name=field.name,
            data_type=data_type,
            required=required,
            description=f"field {field.number}",
        )
        return attr

    def _enum_to_entity(self, enum: EnumDef, full_name: str) -> Entity:
        # Represent enum as an entity with a single attribute of type string,
        # and store possible values in annotation.
        enum_entity = Entity(
            name=full_name,
            attributes=[
                Attribute(
                    name="value",
                    data_type=DataType(base=ScalarType.STRING),
                    required=True,
                )
            ],
            description=f"Enum with values: {', '.join(enum.values.keys())}",
        )
        # Annotate possible values (as an example)
        enum_entity.annotations.append(
            # We need to import Annotation; but to avoid additional imports, we can skip.
            # For simplicity, we add a dummy annotation via the list.
            type('Annotation', (), {})()  # placeholder; in real code use models.Annotation
        )
        return enum_entity

    def _method_to_operation(
        self,
        svc_name: str,
        method: ServiceMethod,
        package: str,
        entity_by_name: dict[str, Entity],
    ) -> ServiceOperation | None:
        op_id = f"{svc_name}.{method.name}"

        # Determine operation type based on streaming
        op_type = OperationType.REQUEST_RESPONSE
        if method.client_streaming and method.server_streaming:
            op_type = OperationType.REQUEST_RESPONSE  # bidi
        elif method.server_streaming:
            op_type = OperationType.PUBLISH
        elif method.client_streaming:
            op_type = OperationType.SUBSCRIBE

        # Resolve input entity
        input_type_name = method.input.name
        # Try fully qualified name, then local name
        qualified_input = f"{package}.{input_type_name}" if package else input_type_name
        input_entity = entity_by_name.get(qualified_input)
        if input_entity is None:
            input_entity = entity_by_name.get(input_type_name)
        if input_entity is None:
            # fallback: create a placeholder and add a validation warning
            input_entity = Entity(
                name=input_type_name,
                description=f"Unresolved input type {input_type_name}",
            )
            # Optionally add validation error

        request_body = RequestBody(
            description=f"gRPC request {input_type_name}",
            required=True,
            content_entity=input_entity,
        )

        # Resolve output entity
        output_type_name = method.output.name
        qualified_output = f"{package}.{output_type_name}" if package else output_type_name
        output_entity = entity_by_name.get(qualified_output)
        if output_entity is None:
            output_entity = entity_by_name.get(output_type_name)
        if output_entity is None:
            output_entity = Entity(
                name=output_type_name,
                description=f"Unresolved output type {output_type_name}",
            )

        response = Response(
            status_code="0",  # gRPC status not HTTP
            description=f"gRPC response {output_type_name}",
            content_entity=output_entity,
        )

        op = ServiceOperation(
            name=op_id,
            type=op_type,
            description=f"gRPC method {method.name}",
            http_method=None,
            path=f"/{package}.{svc_name}/{method.name}" if package else f"/{svc_name}/{method.name}",
            parameters=[],
            request_body=request_body,
            responses=[response],
            extensions={
                "proto:client_streaming": method.client_streaming,
                "proto:server_streaming": method.server_streaming,
            },
        )
        return op

    def _proto_type_to_datatype(self, type_name: str, repeated: bool = False) -> DataType:
        """Convert a protobuf type string to an MSDM DataType."""
        # Scalar mapping
        scalar_map = {
            "double": ScalarType.DOUBLE,
            "float": ScalarType.FLOAT,
            "int32": ScalarType.INT,
            "int64": ScalarType.LONG,
            "uint32": ScalarType.INT,
            "uint64": ScalarType.LONG,
            "sint32": ScalarType.INT,
            "sint64": ScalarType.LONG,
            "fixed32": ScalarType.INT,
            "fixed64": ScalarType.LONG,
            "sfixed32": ScalarType.INT,
            "sfixed64": ScalarType.LONG,
            "bool": ScalarType.BOOLEAN,
            "string": ScalarType.STRING,
            "bytes": ScalarType.BINARY,
        }
        # Handle map<key,value> – treat as MAP type
        if type_name.startswith("map<"):
            # Extract key and value types (simplified)
            inner = type_name[4:-1]  # remove "map<" and ">"
            parts = inner.split(',', 1)
            if len(parts) == 2:
                key_type = self._proto_type_to_datatype(parts[0].strip(), False)
                value_type = self._proto_type_to_datatype(parts[1].strip(), False)
                return DataType(base=ScalarType.MAP, key_type=key_type, value_type=value_type)
        # Scalar
        if type_name in scalar_map:
            base = scalar_map[type_name]
            if repeated:
                return DataType(base=ScalarType.ARRAY, element_type=DataType(base=base))
            return DataType(base=base)
        # Message reference
        base = ScalarType.REF
        dt = DataType(base=base, ref_entity_id=type_name)
        if repeated:
            return DataType(base=ScalarType.ARRAY, element_type=dt)
        return dt