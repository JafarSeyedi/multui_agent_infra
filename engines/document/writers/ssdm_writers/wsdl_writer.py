# engines/document/writers/ssdm_writers/wsdl_writer.py
"""
WSDL 1.1 Writer – serialises an SSDMDocument  into a WSDL 1.1 XML file.

Mapping rules (SSDM → WSDL):
- document.title                                           → wsdl:definitions name
- document.description                                     → wsdl:documentation
- document.servers[0].url                                  → wsdl:service endpoint address
- document.operations                                      → wsdl:portType/wsdl:operation
  - operation.name                                         → operation name
  - operation.soap_action (or name)                        → soapAction
  - operation.input parameters and request body            → wsdl:message (input)
  - operation.output (first 200 response)                  → wsdl:message (output)
- document.type_definitions (MSDM)                         → embedded XSD schema

Every element is derived from typed SSDM/MSDM fields; no annotations are used.
"""
from __future__ import annotations

from xml.etree.ElementTree import Element
from xml.etree.ElementTree import SubElement
from xml.etree.ElementTree import tostring

from ...models.msdm_models import DataType
from ...models.msdm_models import Entity
from ...models.msdm_models import MSDMDocument
from ...models.msdm_models import ScalarType
from ...models.ssdm_models import ServiceOperation
from ...models.ssdm_models import Parameter
from ...models.ssdm_models import Server
from ...models.ssdm_models import SSDMDocument 
from .base_ssdm_writer import BaseSSDMWriter
from .base_ssdm_writer import SSDMWriteOptions

# ── Namespaces ────────────────────────────────────────────────────
WSDL_NS = "http://schemas.xmlsoap.org/wsdl/"
SOAP_NS = "http://schemas.xmlsoap.org/wsdl/soap/"
XSD_NS  = "http://www.w3.org/2001/XMLSchema"


class WSDLWriter(BaseSSDMWriter):
    """Serialises an SSDMDocument  to WSDL 1.1 XML."""

    name = "wsdl"
    supported_extensions = (".wsdl",)

    def __init__(self, options: SSDMWriteOptions | None = None):
        super().__init__(options)
        self._tns = "http://tempuri.org/"  # will be set from document if available

    async def _write_design(self, document: SSDMDocument ) -> bytes:
        self._tns = f"http://{self._safe_name(document.title or 'service')}.local/"
        root = Element(f"{{{WSDL_NS}}}definitions", {
            "xmlns": WSDL_NS,
            "xmlns:soap": SOAP_NS,
            "xmlns:xsd": XSD_NS,
            "xmlns:tns": self._tns,
            "name": document.title or "Service",
            "targetNamespace": self._tns,
        })

        # Documentation
        if document.description:
            doc_elem = SubElement(root, f"{{{WSDL_NS}}}documentation")
            doc_elem.text = document.description

        # Types (XSD schema) from MSDM
        if document.type_definitions:
            self._write_types(root, document.type_definitions)

        # Messages from operations
        messages = self._build_messages(document.operations)
        for name, msg_def in messages.items():
            self._write_message(root, name, msg_def)

        # Port type
        self._write_port_type(root, document.title or "Service", document.operations)

        # Binding
        binding_name = f"{self._safe_name(document.title or 'Service')}Binding"
        self._write_binding(root, binding_name, document.title or "Service", document.operations)

        # Service
        self._write_service(root, document.title or "Service", binding_name, document.servers)

        xml_bytes = tostring(root, encoding="unicode", method="xml")
        encoding = "utf-8"
        if self.options and self.options.encoding:
            encoding = self.options.encoding
        return xml_bytes.encode(encoding)

    def get_supported_media_types(self) -> list[str]:
        return ["application/xml"]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    # ── Types (XSD) from MSDM ─────────────────────────────────────
    def _write_types(self, root: Element, msdm: MSDMDocument) -> None:
        types = SubElement(root, f"{{{WSDL_NS}}}types")
        schema = SubElement(types, f"{{{XSD_NS}}}schema", {
            "targetNamespace": self._tns,
            "xmlns": XSD_NS,
        })
        for entity in msdm.entities:
            self._write_xsd_entity(schema, entity)

    def _write_xsd_entity(self, schema: Element, entity: Entity) -> None:
        elem = SubElement(schema, f"{{{XSD_NS}}}element", {"name": entity.name})
        complex_type = SubElement(elem, f"{{{XSD_NS}}}complexType")
        sequence = SubElement(complex_type, f"{{{XSD_NS}}}sequence")
        for attr in entity.attributes:
            attr_elem = SubElement(sequence, f"{{{XSD_NS}}}element", {
                "name": attr.name,
                "type": self._msdm_to_xsd_type(attr.data_type),
            })
            if not attr.required:
                attr_elem.set("minOccurs", "0")

    def _msdm_to_xsd_type(self, dt: DataType) -> str:
        base = dt.base
        if base == ScalarType.STRING:
            return "xsd:string"
        if base == ScalarType.INT:
            return "xsd:int"
        if base == ScalarType.LONG:
            return "xsd:long"
        if base == ScalarType.FLOAT:
            return "xsd:float"
        if base == ScalarType.DOUBLE:
            return "xsd:double"
        if base == ScalarType.BOOLEAN:
            return "xsd:boolean"
        if base == ScalarType.DATE:
            return "xsd:date"
        if base == ScalarType.TIME:
            return "xsd:time"
        if base == ScalarType.TIMESTAMP:
            return "xsd:dateTime"
        if base == ScalarType.DURATION:
            return "xsd:duration"
        if base == ScalarType.DECIMAL:
            return "xsd:decimal"
        if base == ScalarType.BINARY:
            return "xsd:base64Binary"
        if base == ScalarType.ANY:
            return "xsd:anyType"
        if base == ScalarType.ARRAY and dt.element_type:
            inner = self._msdm_to_xsd_type(dt.element_type)
            return f"{inner}"  # arrays not directly expressed; we'll just use inner type
        if base == ScalarType.REF and dt.ref_entity:
            return f"tns:{dt.ref_entity.name}"
        if base == ScalarType.STRUCT:
            return "xsd:anyType"
        return "xsd:string"

    # ── Messages ──────────────────────────────────────────────────
    def _build_messages(self, operations: list[ServiceOperation]) -> dict[str, list[tuple[str, str]]]:
        messages: dict[str, list[tuple]] = {}
        for op in operations:
            # Input message parts
            input_parts: list[tuple] = []
            for param in op.parameters:
                ptype = self._parameter_to_xsd_type(param)
                input_parts.append((param.name, ptype))
            if op.request_body and op.request_body.content_entity:
                input_parts.append(("body", f"tns:{op.request_body.content_entity.name}"))
            elif op.request_body:
                input_parts.append(("body", "xsd:anyType"))
            if not input_parts:
                input_parts.append(("empty", "xsd:string"))

            messages[f"{op.name}Request"] = input_parts

            # Output message parts (first 200 response)
            output_parts: list[tuple] = []
            for resp in op.responses:
                if resp.status_code in ("200", "201") and resp.content_entity:
                    output_parts.append(("body", f"tns:{resp.content_entity.name}"))
                    break
            if not output_parts:
                output_parts.append(("result", "xsd:boolean"))
            messages[f"{op.name}Response"] = output_parts
        return messages

    def _parameter_to_xsd_type(self, param: Parameter) -> str:
        if param.type_entity:
            return f"tns:{param.type_entity.name}"
        if param.type_entity:
            return f"xsd:{param.type_entity.name}"
        return "xsd:string"

    def _write_message(self, root: Element, name: str, parts: list[tuple]) -> None:
        msg = SubElement(root, f"{{{WSDL_NS}}}message", {"name": name})
        for part_name, part_type in parts:
            SubElement(msg, f"{{{WSDL_NS}}}part", {
                "name": part_name,
                "element" if part_type.startswith("tns:") else "type": part_type,
            })

    # ── Port type ─────────────────────────────────────────────────
    def _write_port_type(self, root: Element, service_name: str, operations: list[ServiceOperation]) -> None:
        pt = SubElement(root, f"{{{WSDL_NS}}}portType", {"name": f"{service_name}PortType"})
        for op in operations:
            operation = SubElement(pt, f"{{{WSDL_NS}}}operation", {"name": op.name})
            if op.description:
                doc = SubElement(operation, f"{{{WSDL_NS}}}documentation")
                doc.text = op.description
            SubElement(operation, f"{{{WSDL_NS}}}input", {
                "message": f"tns:{op.name}Request",
            })
            SubElement(operation, f"{{{WSDL_NS}}}output", {
                "message": f"tns:{op.name}Response",
            })

    # ── Binding ───────────────────────────────────────────────────
    def _write_binding(self, root: Element, binding_name: str, service_name: str, operations: list[ServiceOperation]) -> None:
        bind = SubElement(root, f"{{{WSDL_NS}}}binding", {
            "name": binding_name,
            "type": f"tns:{service_name}PortType",
        })
        soap_bind = SubElement(bind, f"{{{SOAP_NS}}}binding", {
            "transport": "http://schemas.xmlsoap.org/soap/http",
        })
        for op in operations:
            oper = SubElement(bind, f"{{{WSDL_NS}}}operation", {"name": op.name})
            soap_op = SubElement(oper, f"{{{SOAP_NS}}}operation", {
                "soapAction": op.soap_action or f"{self._tns}{op.name}",
                "style": "document",
            })
            SubElement(oper, f"{{{WSDL_NS}}}input")
            SubElement(oper, f"{{{WSDL_NS}}}output")

    # ── Service ───────────────────────────────────────────────────
    def _write_service(self, root: Element, service_name: str, binding_name: str, servers: list[Server]) -> None:
        svc = SubElement(root, f"{{{WSDL_NS}}}service", {"name": service_name})
        for idx, server in enumerate(servers):
            port = SubElement(svc, f"{{{WSDL_NS}}}port", {
                "name": f"{service_name}Port{idx}",
                "binding": f"tns:{binding_name}",
            })
            SubElement(port, f"{{{SOAP_NS}}}address", {
                "location": server.url,
            })

    @staticmethod
    def _safe_name(name: str) -> str:
        return "".join(c if c.isalnum() else "_" for c in (name or "unnamed")).strip("_")
