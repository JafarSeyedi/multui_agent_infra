# engines/document/parsers/ssdm_parsers/wsdl_parser.py
"""
WSDL 1.1 Parser – converts a .wsdl file into an SSDMDocument.

Mapping rules (WSDL → SSDM):
- <definitions>                       → SSDMDocument (title, targetNamespace)
- <types>/<xsd:schema>                → MSDM entities (type_definitions)
- <message>                           → temporary mapping of message name → part elements
- <portType>/<operation>              → SSDM ServiceOperation (name, soap_action)
  - input / output messages           → parameters (from message parts) and request/response bodies
- <binding>/<operation>/<soap:operation> → soapAction
- <service>/<port>/<soap:address>     → servers list
"""
from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET

from ...models.media_types import MEDIA_TYPES
from ...models.msdm_models import Attribute
from ...models.msdm_models import DataType
from ...models.msdm_models import Entity
from ...models.msdm_models import MSDMDocument
from ...models.msdm_models import ScalarType
from ...models.ssdm_models import ServiceOperation
from ...models.ssdm_models import Parameter
from ...models.ssdm_models import ParameterLocation
from ...models.ssdm_models import RequestBody
from ...models.ssdm_models import Response
from ...models.ssdm_models import Server
from ...models.ssdm_models import SSDMDocument
from ..base import ParseOptions
from .base_ssdm_parser import BaseSSDMParser

WSDL_NS = "http://schemas.xmlsoap.org/wsdl/"
SOAP_NS = "http://schemas.xmlsoap.org/wsdl/soap/"
XSD_NS = "http://www.w3.org/2001/XMLSchema"
NS = {"wsdl": WSDL_NS, "soap": SOAP_NS, "xsd": XSD_NS}


class WSDLParser(BaseSSDMParser):
    """Parser for WSDL 1.1 files (.wsdl)."""

    name = "wsdl"
    supported_extensions = (".wsdl",)

    async def _parse_to_document(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> SSDMDocument:
        encoding = options.encoding or "utf-8"
        text = data.decode(encoding)
        root = ET.fromstring(text)

        # Placeholder for unresolved parameter type references
        _param_refs: dict[Parameter, str] = {}

        # SSDMDocument requires title, document_id, media_type
        doc = SSDMDocument(
            title=root.get("name", Path(source_name).stem),
            document_id=source_name,           # temporary, will be overwritten by base parser
            media_type=MEDIA_TYPES["wsdl"],
            version="1.0.0",
        )
        root.get("targetNamespace", "")
        doc.description = self._get_child_text(root, "wsdl:documentation")

        # 1. Types – parse XSD into MSDM
        msdm = MSDMDocument(
            title="types",
            document_id="types",
            media_type=MEDIA_TYPES["wsdl"],
        )
        types_elem = root.find("wsdl:types", NS)
        if types_elem is not None:
            for schema in types_elem.findall("xsd:schema", NS):
                self._parse_xsd_schema(schema, msdm)
        if msdm.entities:
            doc.type_definitions = msdm

        # 2. Messages (skip messages without a name)
        messages: dict[str, list[tuple[str, str, str]]] = {}
        for msg in root.findall("wsdl:message", NS):
            msg_name = msg.get("name")
            if msg_name is None:
                continue
            parts = []
            for part in msg.findall("wsdl:part", NS):
                part_name = part.get("name")
                if part_name is None:
                    continue          # parts without a name are invalid in WSDL
                element = part.get("element") or ""
                type_attr = part.get("type") or ""
                if element:
                    parts.append((part_name, element, "element"))
                elif type_attr:
                    parts.append((part_name, type_attr, "type"))
                else:
                    parts.append((part_name, "", "any"))
            messages[msg_name] = parts

        # 3. PortType operations (skip operations without a name)
        operations: list[ServiceOperation] = []
        port_type = root.find("wsdl:portType", NS)
        soap_actions: dict[str, str] = {}  # operation name → soapAction (from binding)
        if port_type is not None:
            for op_elem in port_type.findall("wsdl:operation", NS):
                op_name = op_elem.get("name")
                if op_name is None:
                    continue
                desc = self._get_child_text(op_elem, "wsdl:documentation")
                op = ServiceOperation(name=op_name, description=desc)

                # Input
                input_elem = op_elem.find("wsdl:input", NS)
                if input_elem is not None:
                    in_msg_name = input_elem.get("message", "").split(":")[-1]
                    if in_msg_name in messages:
                        params, refs = self._parts_to_parameters(messages[in_msg_name])
                        op.parameters = params
                        _param_refs.update(refs)
                        body_entity = self._parts_to_body_entity(messages[in_msg_name], msdm)
                        if body_entity:
                            op.request_body = RequestBody(content_entity=body_entity)

                # Output
                output_elem = op_elem.find("wsdl:output", NS)
                if output_elem is not None:
                    out_msg_name = output_elem.get("message", "").split(":")[-1]
                    if out_msg_name in messages:
                        resp_entity = self._parts_to_body_entity(messages[out_msg_name], msdm)
                        if resp_entity:
                            op.responses.append(
                                Response(
                                    status_code="200",
                                    content_entity=resp_entity,
                                )
                            )

                operations.append(op)

        # 4. Binding (soapAction)
        binding = root.find("wsdl:binding", NS)
        if binding is not None:
            for op_elem in binding.findall("wsdl:operation", NS):
                op_name = op_elem.get("name")
                if op_name is None:
                    continue
                soap_op = op_elem.find("soap:operation", NS)
                if soap_op is not None:
                    soap_action = soap_op.get("soapAction", "")
                    soap_actions[op_name] = soap_action
            # Assign soap actions to operations
            for op in operations:
                if op.name in soap_actions:
                    op.soap_action = soap_actions[op.name]

        # 5. Service → servers
        service = root.find("wsdl:service", NS)
        if service is not None:
            for port in service.findall("wsdl:port", NS):
                address = port.find("soap:address", NS)
                if address is not None:
                    location = address.get("location", "")
                    if location:
                        doc.servers.append(Server(url=location))

        doc.operations = operations

        # ---- Second pass: resolve parameter type references to Entities ----
        if doc.type_definitions is not None:
            # Build a lookup map: entity name → Entity
            entity_by_name = {e.name: e for e in doc.type_definitions.entities}
            for param, ref_str in _param_refs.items():
                # ref_str may be something like "tns:MyElement" or "xsd:string"
                # Extract local name after colon
                local_name = ref_str.split(":")[-1]
                # Only resolve if it matches an Entity name (not a built‑in XSD type)
                if local_name in entity_by_name:
                    param.type_entity = entity_by_name[local_name]
                # Otherwise leave param.type_entity as None (built‑in or unresolved)

        return doc

    # ── Helpers ────────────────────────────────────────────────────
    def _parse_xsd_schema(self, schema: ET.Element, msdm: MSDMDocument) -> None:
        """Extract XSD element definitions and convert to MSDM entities."""
        for element in schema.findall("xsd:element", NS):
            name = element.get("name")
            if not name:
                continue
            entity = Entity(name=name)
            complex_type = element.find("xsd:complexType", NS)
            if complex_type is not None:
                sequence = complex_type.find("xsd:sequence", NS)
                if sequence is not None:
                    for child_elem in sequence.findall("xsd:element", NS):
                        attr_name = child_elem.get("name")
                        if attr_name is None:
                            continue
                        attr_type = child_elem.get("type", "xsd:string")
                        dt = self._xsd_type_to_datatype(attr_type)
                        required = child_elem.get("minOccurs") != "0"
                        entity.attributes.append(
                            Attribute(
                                name=attr_name,
                                data_type=dt,
                                required=required,
                            )
                        )
            if entity.attributes:
                msdm.entities.append(entity)

    def _xsd_type_to_datatype(self, qname: str) -> DataType:
        """Convert an XSD type QName (or built-in) to MSDM DataType."""
        local = qname.split(":")[-1]
        mapping = {
            "string": ScalarType.STRING,
            "int": ScalarType.INT,
            "integer": ScalarType.INT,
            "long": ScalarType.LONG,
            "float": ScalarType.FLOAT,
            "double": ScalarType.DOUBLE,
            "boolean": ScalarType.BOOLEAN,
            "date": ScalarType.DATE,
            "time": ScalarType.TIME,
            "dateTime": ScalarType.TIMESTAMP,
            "decimal": ScalarType.DECIMAL,
            "base64Binary": ScalarType.BINARY,
            "anyType": ScalarType.ANY,
        }
        if local in mapping:
            return DataType(base=mapping[local])
        # Otherwise, it's a reference to another XSD type (or tns: type)
        return DataType(base=ScalarType.REF, ref_entity_id=local)

    def _parts_to_parameters(
        self, parts: list[tuple[str, str, str]]
    ) -> tuple[list[Parameter], dict[Parameter, str]]:
        """
        Convert message parts to SSDM Parameter list.
        Returns:
            - list of Parameter objects
            - dict mapping each Parameter to its original type reference string
        """
        params = []
        refs: dict[Parameter, str] = {}
        for part_name, ref, kind in parts:
            # WSDL parts typically belong to the SOAP body.
            param = Parameter(
                name=part_name,
                location=ParameterLocation.BODY,
                required=True,
                type_entity=None,
            )
            params.append(param)
            if kind in ("element", "type") and ref:
                refs[param] = ref
        return params, refs

    def _parts_to_body_entity(
        self, parts: list[tuple[str, str, str]], msdm: MSDMDocument
    ) -> Entity | None:
        """If the message has exactly one part that references an element defined in MSDM, return that entity."""
        for part_name, ref, kind in parts:
            if kind == "element":
                elem_name = ref.split(":")[-1]
                for entity in msdm.entities:
                    if entity.name == elem_name:
                        return entity
        # Fallback: create a temporary entity from parts
        if parts:
            temp_entity = Entity(name="body")
            for part_name, ref, kind in parts:
                dt = DataType(base=ScalarType.ANY)
                if ref and kind == "type":
                    dt = self._xsd_type_to_datatype(ref)
                temp_entity.attributes.append(
                    Attribute(name=part_name, data_type=dt, required=True)
                )
            return temp_entity
        return None

    @staticmethod
    def _get_child_text(elem: ET.Element, tag: str) -> str | None:
        child = elem.find(tag, NS)
        return child.text.strip() if child is not None and child.text else None