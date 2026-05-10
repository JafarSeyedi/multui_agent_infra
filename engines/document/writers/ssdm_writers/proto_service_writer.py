# engines/document/writers/ssdm_writers/proto_service_writer.py
"""
Protobuf Service Writer – serialises an SSDMDocument  into a Protocol Buffers
IDL file (.proto).  Each operation becomes an RPC method in a single service
whose name is derived from the document title.  MSDM type definitions are used
to generate nested message types.
"""
from __future__ import annotations

from ...models.msdm_models import DataType
from ...models.msdm_models import Entity
from ...models.msdm_models import MSDMDocument
from ...models.msdm_models import ScalarType
from ...models.ssdm_models import ServiceOperation
from ...models.ssdm_models import Parameter
from ...models.ssdm_models import SSDMDocument 
from .base_ssdm_writer import BaseSSDMWriter
from .base_ssdm_writer import SSDMWriteOptions

# Mapping from MSDM scalar type to proto type
SCALAR_TO_PROTO = {
    ScalarType.STRING: "string",
    ScalarType.INT: "int32",
    ScalarType.LONG: "int64",
    ScalarType.FLOAT: "float",
    ScalarType.DOUBLE: "double",
    ScalarType.BOOLEAN: "bool",
    ScalarType.BINARY: "bytes",
    ScalarType.DATE: "string",       # no native date
    ScalarType.TIME: "string",
    ScalarType.TIMESTAMP: "google.protobuf.Timestamp",
    ScalarType.DURATION: "google.protobuf.Duration",
    ScalarType.UUID: "string",
    ScalarType.DECIMAL: "string",
    ScalarType.ANY: "google.protobuf.Any",
}


class ProtoServiceWriter(BaseSSDMWriter):
    """Serialises an SSDMDocument  to a Protobuf IDL (.proto) file."""

    name = "proto_service"
    supported_extensions = (".proto",)

    def __init__(self, options: SSDMWriteOptions | None = None):
        super().__init__(options)

    async def _write_design(self, document: SSDMDocument ) -> bytes:
        lines: list[str] = []
        package = self._safe_name(document.title) if document.title else "service"
        lines.append(f'package {package};')
        lines.append("")

        # Imports for well-known types (if used)
        imports: set = set()
        # Extract operations and generate messages
        msdm = document.type_definitions
        op_messages = self._prepare_operation_messages(document.operations, msdm, imports)

        for imp in imports:
            lines.append(f'import "{imp}";')
        if imports:
            lines.append("")

        # Write message definitions from MSDM entities
        if msdm:
            for entity in msdm.entities:
                self._write_message(lines, entity)

        # Write generated request/response messages for operations
        for msg_name, fields in op_messages.items():
            lines.append(f"message {msg_name} {{")
            for idx, (fname, ftype) in enumerate(fields, start=1):
                lines.append(f"  {ftype} {fname} = {idx};")
            lines.append("}")
            lines.append("")

        # Write service
        service_name = self._safe_name(document.title) or "Service"
        lines.append(f"service {service_name} {{")
        for op in document.operations:
            rpc_name = self._safe_name(op.name)
            req_msg = f"{rpc_name}Request"
            res_msg = f"{rpc_name}Response"
            # Ensure the generated messages exist
            if req_msg not in op_messages:
                # Should not happen
                req_msg = "google.protobuf.Empty"
            if res_msg not in op_messages:
                res_msg = "google.protobuf.Empty"
            lines.append(f"  rpc {rpc_name} ({req_msg}) returns ({res_msg});")
        lines.append("}")

        return "\n".join(lines).encode(getattr(self.options, "encoding", "utf-8") or "utf-8")

    def get_supported_media_types(self) -> list[str]:
        return ["text/plain"]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    # ── Build request/response messages from operations ────────────
    def _prepare_operation_messages(self, operations: list[ServiceOperation],
                                    msdm: MSDMDocument | None,
                                    imports: set) -> dict[str, list[tuple[str, str]]]:
        """Returns a dict of message_name → list of (field_name, proto_type)."""
        messages: dict[str, list[tuple]] = {}
        for op in operations:
            rpc_name = self._safe_name(op.name)
            req_msg = f"{rpc_name}Request"
            res_msg = f"{rpc_name}Response"

            req_fields: list[tuple[str, str]] = []
            # Parameters become fields
            for param in op.parameters:
                ptype = self._param_to_proto_type(param, import_list=imports)
                req_fields.append((param.name, ptype))
            # Request body → a field named "body"
            if op.request_body and op.request_body.content_entity:
                body_type = self._safe_name(op.request_body.content_entity.name)
                req_fields.append(("body", body_type))
            elif op.request_body:
                req_fields.append(("body", "bytes"))
            if not req_fields:
                req_fields.append(("placeholder", "bool"))
            messages[req_msg] = req_fields

            res_fields: list[tuple[str, str]] = []
            for resp in op.responses:
                if resp.content_entity:
                    res_type = self._safe_name(resp.content_entity.name)
                    res_fields.append(("body", res_type))
                    break
            if not res_fields:
                res_fields.append(("success", "bool"))
            messages[res_msg] = res_fields

        return messages

    def _param_to_proto_type(self, param: Parameter, import_list: set) -> str:
        if param.type_entity:
            return self._safe_name(param.type_entity.name)
        if param.type_entity:
            return param.type_entity.name
        return "string"

    # ── Write a message from an MSDM Entity ───────────────────────
    def _write_message(self, lines: list[str], entity: Entity) -> None:
        lines.append(f"message {self._safe_name(entity.name)} {{")
        for idx, attr in enumerate(entity.attributes, start=1):
            proto_type = self._datatype_to_proto(attr.data_type)
            lines.append(f"  {proto_type} {attr.name} = {idx};")
        lines.append("}")
        lines.append("")

    def _datatype_to_proto(self, dt: DataType) -> str:
        base = dt.base
        if base == ScalarType.ARRAY and dt.element_type:
            inner = self._datatype_to_proto(dt.element_type)
            return f"repeated {inner}"
        if base == ScalarType.MAP:
            key = "string"
            val = "string"
            if dt.key_type:
                key = self._datatype_to_proto(dt.key_type)
            if dt.value_type:
                val = self._datatype_to_proto(dt.value_type)
            return f"map<{key}, {val}>"
        if base == ScalarType.REF and dt.ref_entity:
            return self._safe_name(dt.ref_entity.name)
        if base == ScalarType.STRUCT:
            # Assume the struct is defined by another message referenced via ref_entity
            if dt.ref_entity:
                return self._safe_name(dt.ref_entity.name)
            return "bytes"  # fallback
        return SCALAR_TO_PROTO.get(base, "string")

    @staticmethod
    def _safe_name(name: str) -> str:
        """Convert a string to a valid proto identifier."""
        return "".join(c if c.isalnum() else "_" for c in (name or "unnamed")).strip("_")
