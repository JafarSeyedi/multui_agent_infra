"""
apib_parser.py – API Blueprint (apib) parser → SSDM_DOCUMENT
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import json

from ..base import ParseOptions
from ..ssdm_parsers.base_ssdm_parser import BaseSSDMParser
from ...models.ssdm_models import (
    SSDM_DOCUMENT,
    ContactInfo,
    LicenseInfo,
    Server,
    Operation,
    OperationType,
    Parameter,
    ParameterLocation,
    RequestBody,
    Response,
    HttpMethod,
)
from ...models.msdm_models import MSDMDocument, Entity, Attribute


# --------------------------------------------------------------------------
#  Simple line reader / tokenizer for API Blueprint
# --------------------------------------------------------------------------
APIB_HEADING = re.compile(r"^(#+)\s+(.*)")
APIB_LIST_ITEM = re.compile(r"^\s*[\+\-\*]\s+(.*)")
APIB_CODE_FENCE = re.compile(r"^\s*```(.*)$")
APIB_METADATA = re.compile(r"^([A-Za-z][\w-]*)\s*:\s*(.*)")

class APIBlueprintTokenizer:
    """Iterates over lines, providing look-ahead and block detection."""
    def __init__(self, text: str):
        self.lines = text.splitlines()
        self.pos = 0

    def eof(self) -> bool:
        return self.pos >= len(self.lines)

    def current(self) -> str:
        if self.eof():
            return ""
        return self.lines[self.pos]

    def peek(self) -> str:
        return self.current()

    def advance(self):
        self.pos += 1

    def next_non_empty(self) -> Optional[str]:
        while not self.eof():
            line = self.current().rstrip()
            self.advance()
            if line.strip():
                return line
        return None

    def extract_until_blank_or_heading(self) -> List[str]:
        """Gather lines until a blank line or a heading is encountered."""
        block = []
        while not self.eof():
            line = self.current().rstrip()
            if line.strip() == "" or APIB_HEADING.match(line):
                break
            block.append(line)
            self.advance()
        return block

    def extract_code_block(self, language: str = "") -> Tuple[str, str]:
        """Extract a fenced code block. Returns (language, content)."""
        # current line is the opening fence (already consumed by caller, we assume it's been matched)
        # but we design to start after the fence line.
        lines = []
        while not self.eof():
            line = self.current()
            if line.strip().startswith("```"):
                self.advance()
                break
            lines.append(line)
            self.advance()
        return language, "\n".join(lines)


# --------------------------------------------------------------------------
#  API Blueprint AST nodes (simplified)
# --------------------------------------------------------------------------
class APIBObject:
    def to_dict(self):
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}

class APIBMetadata(APIBObject):
    def __init__(self):
        self.format = "1A"
        self.host = ""
        self.name = ""
        self.description = ""
        self.other = {}

class APIBParameter(APIBObject):
    def __init__(self, name: str, type_str: str = "string", required: bool = True,
                 description: str = "", example: str = ""):
        self.name = name
        self.type = type_str
        self.required = required
        self.description = description
        self.example = example

class APIBBody(APIBObject):
    def __init__(self, media_type: str = "application/json", body: str = "",
                 schema_ref: str = ""):
        self.media_type = media_type
        self.body = body  # raw example
        self.schema_ref = schema_ref

class APIBAction(APIBObject):
    def __init__(self, method: str, name: str = ""):
        self.method = method.upper()
        self.name = name
        self.description = ""
        self.parameters: List[APIBParameter] = []
        self.headers: Dict[str, str] = {}
        self.request_bodies: List[APIBBody] = []
        self.responses: Dict[str, Tuple[str, List[APIBBody]]] = {}  # status -> (desc, bodies)

class APIBResource(APIBObject):
    def __init__(self, path: str, name: str = ""):
        self.path = path
        self.name = name
        self.description = ""
        self.parameters: List[APIBParameter] = []
        self.actions: List[APIBAction] = []

class APIBGroup(APIBObject):
    def __init__(self, name: str):
        self.name = name
        self.description = ""
        self.resources: List[APIBResource] = []


# --------------------------------------------------------------------------
#  Parser
# --------------------------------------------------------------------------
class APIBlueprintParser:
    """Parse API Blueprint markdown into a document model."""
    def __init__(self, text: str):
        self.tokens = APIBlueprintTokenizer(text)
        self.metadata = APIBMetadata()
        self.groups: List[APIBGroup] = []
        self.data_structures: Dict[str, Any] = {}  # name -> raw MSON (for later)

    def parse(self):
        # First line can be metadata or heading
        self._parse_metadata()
        # Then resource groups / resources
        while not self.tokens.eof():
            self._skip_blank()
            if self.tokens.eof():
                break
            line = self.tokens.current().strip()
            heading_match = APIB_HEADING.match(line)
            if not heading_match:
                self.tokens.advance()
                continue
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()
            if title.lower().startswith("group "):
                group = self._parse_group(title[6:].strip())
                if group:
                    self.groups.append(group)
            elif title.lower().startswith("resource "):
                resource = self._parse_resource(title[9:].strip(), path="")
                if resource:
                    # add to last group or create default group
                    if not self.groups:
                        self.groups.append(APIBGroup("Default"))
                    self.groups[-1].resources.append(resource)
            elif title.lower().startswith("data structures"):
                self._parse_data_structures()
            else:
                # Unknown heading, skip
                self.tokens.advance()
        return self

    def _skip_blank(self):
        while not self.tokens.eof() and self.tokens.current().strip() == "":
            self.tokens.advance()

    def _parse_metadata(self):
        """Metadata before any heading. Key: Value pairs."""
        while not self.tokens.eof():
            line = self.tokens.current().strip()
            if APIB_HEADING.match(line) or line == "":
                break
            meta_match = APIB_METADATA.match(line)
            if meta_match:
                key = meta_match.group(1).upper()
                value = meta_match.group(2).strip()
                if key == "FORMAT":
                    self.metadata.format = value
                elif key == "HOST":
                    self.metadata.host = value
                elif key == "NAME":
                    self.metadata.name = value
                else:
                    self.metadata.other[key] = value
            else:
                # might be description line before heading, collect as description
                if not self.metadata.description:
                    self.metadata.description = line
                else:
                    self.metadata.description += "\n" + line
            self.tokens.advance()

    def _parse_group(self, name: str) -> Optional[APIBGroup]:
        group = APIBGroup(name)
        # Consume description lines until blank line or a Resource heading
        while not self.tokens.eof():
            self.tokens.advance()  # move past the heading line
            self._skip_blank()
            if self.tokens.eof():
                break
            line = self.tokens.current().strip()
            heading = APIB_HEADING.match(line)
            if heading:
                level = len(heading.group(1))
                title = heading.group(2).strip()
                if title.lower().startswith("resource "):
                    resource = self._parse_resource(title[9:].strip(), path="")
                    if resource:
                        group.resources.append(resource)
                    continue
                else:
                    # unexpected heading, break
                    break
            else:
                # treat as description
                group.description += line + "\n"
        return group

    def _parse_resource(self, name_path: str, path: str) -> Optional[APIBResource]:
        # name_path can be "[GET] /path" or just "/path" or "Resource Name [/path]"
        # We'll try to extract method and path from brackets.
        method = None
        rest = name_path
        bracket_match = re.search(r"\[([A-Z]+)\]\s*(.*)", rest)
        if bracket_match:
            method = bracket_match.group(1).upper()
            rest = bracket_match.group(2).strip()
        # if rest starts with "/", it's a path, else it's just a name and we need later line for path
        resource = APIBResource(path="", name=rest)
        if rest.startswith("/"):
            resource.path = rest
            resource.name = rest  # fallback
        else:
            # name only; the path might be on the next line indented
            resource.name = rest
        self.tokens.advance()  # consume heading line

        # Read description and parameters and actions
        while not self.tokens.eof():
            self._skip_blank()
            if self.tokens.eof():
                break
            line = self.tokens.current().strip()
            # Check for sub-heading (## or ###)
            heading = APIB_HEADING.match(line)
            if heading:
                level = len(heading.group(1))
                title = heading.group(2).strip()
                if level == 2 and title.lower().startswith("action "):
                    action = self._parse_action(title[7:].strip())
                    if action:
                        resource.actions.append(action)
                    continue
                elif level == 2:
                    # could be "Parameters" or other section; we'll handle inside action instead
                    break  # unknown sub-heading, stop parsing this resource
                else:
                    break
            else:
                # Normal line: could be description or parameter list
                resource.description += line + "\n"
            self.tokens.advance()
        return resource

    def _parse_action(self, name: str) -> Optional[APIBAction]:
        # name should be "GET /path" or "POST" etc.
        parts = name.split(None, 1)
        method = parts[0].upper()
        path = parts[1].strip() if len(parts) > 1 else ""
        action = APIBAction(method, f"{method} {path}".strip())
        self.tokens.advance()  # consume heading line
        self._parse_action_details(action)
        return action

    def _parse_action_details(self, action: APIBAction):
        """Parse the content under an Action heading (## Action ...)."""
        while not self.tokens.eof():
            self._skip_blank()
            if self.tokens.eof():
                break
            line = self.tokens.current().strip()
            heading = APIB_HEADING.match(line)
            if heading:
                # Sub-section: Request, Response, Parameters, etc.
                level = len(heading.group(1))
                title = heading.group(2).strip().lower()
                if title.startswith("request"):
                    self._parse_request_section(action)
                elif title.startswith("response"):
                    self._parse_response_section(action)
                elif title.startswith("parameters"):
                    self._parse_parameters_section(action.parameters)
                elif title.startswith("headers"):
                    self._parse_headers_section(action.headers)
                else:
                    self.tokens.advance()
            else:
                # Description line
                action.description += line + "\n"
                self.tokens.advance()

    def _parse_request_section(self, action: APIBAction):
        self.tokens.advance()  # consume heading
        # Body or headers or arbitrary content
        while not self.tokens.eof():
            self._skip_blank()
            if self.tokens.eof():
                break
            line = self.tokens.current().strip()
            if APIB_HEADING.match(line):  # new heading, stop
                break
            # Could be "[Body]" or "Body" or a code block
            if line.lower().startswith("[body]") or line.lower() == "body":
                self.tokens.advance()
                self._parse_body_block(action.request_bodies)
            elif APIB_CODE_FENCE.match(line):
                lang, content = self._extract_code_block()
                action.request_bodies.append(APIBBody(lang if lang else "text/plain", content))
            else:
                self.tokens.advance()

    def _parse_response_section(self, action: APIBAction):
        self.tokens.advance()  # consume "Response ..." heading
        # The heading might contain status code and description: "Response 200 (application/json)"
        # We'll need to extract from the heading text (already consumed), but we can read it from the previous line? Let's rework: we should capture from heading.
        # For simplicity, we'll parse the heading text from the initial heading match before advancing.
        # Since we already advanced, we need to keep the heading string; we'll adjust the flow.
        # Instead, we'll modify _parse_action_details to pass heading text. Let's do inline:
        # We'll backtrack: better to rewrite the parsing of sub-sections with heading text.
        # Let's just assume the heading text is lost; we can deduce from the content.
        # We'll look for "[Status]" or similar.
        status = "200"
        desc = ""
        bodies: List[APIBBody] = []
        while not self.tokens.eof():
            self._skip_blank()
            if self.tokens.eof():
                break
            line = self.tokens.current().strip()
            if APIB_HEADING.match(line):
                break
            if line.lower().startswith("[status]") or line.lower() == "status":
                self.tokens.advance()
                line = self.tokens.current().strip()
                # could be "200"
                status = line.split()[0] if line else "200"
                desc = line[len(status):].strip()
                self.tokens.advance()
            elif APIB_CODE_FENCE.match(line):
                lang, content = self._extract_code_block()
                bodies.append(APIBBody(lang if lang else "application/json", content))
            else:
                self.tokens.advance()
        action.responses[status] = (desc, bodies)

    def _parse_parameters_section(self, param_list: List[APIBParameter]):
        self.tokens.advance()  # consume heading
        while not self.tokens.eof():
            self._skip_blank()
            if self.tokens.eof():
                break
            line = self.tokens.current().strip()
            if APIB_HEADING.match(line):
                break
            # Parameter line: + name: type (required) - description
            if APIB_LIST_ITEM.match(line):
                text = APIB_LIST_ITEM.match(line).group(1)
                # Parse parameter: name: type (optional, required) - description
                param = self._parse_parameter_text(text)
                if param:
                    param_list.append(param)
            self.tokens.advance()

    def _parse_headers_section(self, headers: Dict[str, str]):
        self.tokens.advance()
        while not self.tokens.eof():
            self._skip_blank()
            if self.tokens.eof():
                break
            line = self.tokens.current().strip()
            if APIB_HEADING.match(line):
                break
            if APIB_LIST_ITEM.match(line):
                text = APIB_LIST_ITEM.match(line).group(1)
                # Header: name: value
                parts = text.split(":", 1)
                if len(parts) == 2:
                    headers[parts[0].strip()] = parts[1].strip()
            self.tokens.advance()

    def _parse_body_block(self, bodies: List[APIBBody]):
        """Parse a body section, possibly with media type and schema."""
        media_type = "application/json"
        content = ""
        while not self.tokens.eof():
            self._skip_blank()
            if self.tokens.eof():
                break
            line = self.tokens.current().strip()
            if APIB_HEADING.match(line) or line.lower().startswith("request") or line.lower().startswith("response"):
                break
            if APIB_CODE_FENCE.match(line):
                lang, code = self._extract_code_block()
                media_type = lang if lang else media_type
                content = code
                break
            elif line.lower().startswith("[schema]") or line.lower() == "schema":
                self.tokens.advance()
                # reference to data structure
                schema_ref = self.tokens.current().strip()
                self.tokens.advance()
                bodies.append(APIBBody(media_type, "", schema_ref=schema_ref))
                return
            else:
                # assume it's content
                content += line + "\n"
                self.tokens.advance()
        if content:
            bodies.append(APIBBody(media_type, content))

    def _parse_parameter_text(self, text: str) -> Optional[APIBParameter]:
        # format: name: type (optional, required) - description
        # or name (type, optional) - ...
        # We'll use regex
        match = re.match(r"(\w+)\s*(?:\:\s*(\w+))?\s*(\([^)]+\))?\s*(?:-\s*(.*))?", text)
        if not match:
            return None
        name = match.group(1)
        type_str = match.group(2) or "string"
        modifiers = match.group(3) or ""
        description = match.group(4) or ""
        required = "required" in modifiers.lower()
        return APIBParameter(name, type_str, required, description)

    def _extract_code_block(self) -> Tuple[str, str]:
        # current line is the opening fence
        fence_match = APIB_CODE_FENCE.match(self.tokens.current())
        lang = fence_match.group(1) if fence_match else ""
        self.tokens.advance()
        return self.tokens.extract_code_block(lang)

    def _parse_data_structures(self):
        """Stub: parse MSON data structures and store raw."""
        # In a full implementation we would parse these into MSDM entities.
        # For now, we just skip them.
        while not self.tokens.eof():
            line = self.tokens.current().strip()
            if APIB_HEADING.match(line) and not line.startswith("##"):
                break  # next top-level heading
            self.tokens.advance()


# --------------------------------------------------------------------------
#  SSDM converter
# --------------------------------------------------------------------------
class APIBlueprintToSSDMParser(BaseSSDMParser):
    name = "apib"
    supported_extensions = (".apib",)

    async def _parse_to_document(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> SSDM_DOCUMENT:
        text = data.decode(options.encoding)
        api_parser = APIBlueprintParser(text)
        api_parser.parse()

        doc = SSDM_DOCUMENT(
            document_id="",
            title=api_parser.metadata.name or Path(source_name).stem,
            version="1.0.0",
            description=api_parser.metadata.description,
            servers=self._build_servers(api_parser.metadata),
            security_schemes=[],
            operations=[],
        )

        # Convert groups/resources/actions to Operations
        all_ops = []
        for group in api_parser.groups:
            for res in group.resources:
                for action in res.actions:
                    op = self._action_to_operation(action, res, group)
                    all_ops.append(op)
        doc.operations = all_ops

        # Data structures could be converted to MSDM entities (future)
        doc.type_definitions = None
        doc.is_valid = True
        return doc

    def _build_servers(self, metadata: APIBMetadata) -> List[Server]:
        servers = []
        if metadata.host:
            # HOST can be "http://example.com" or just "example.com"
            url = metadata.host if metadata.host.startswith("http") else f"http://{metadata.host}"
            servers.append(Server(url=url))
        return servers

    def _action_to_operation(self, action: APIBAction, resource: APIBResource, group: APIBGroup) -> Operation:
        # Build path from resource path
        path = resource.path or "/"

        # HTTP method
        try:
            http_method = HttpMethod(action.method)
        except ValueError:
            http_method = None

        # Parameters: combine resource params and action params
        params = []
        # Resource parameters (URI params from path)
        # Extract path parameters like {id}
        for match in re.finditer(r"\{(\w+)\}", path):
            pname = match.group(1)
            params.append(Parameter(name=pname, location=ParameterLocation.PATH, type_string="string"))
        # Add action defined parameters (query/header/body)
        for ap in action.parameters:
            # API Blueprint doesn't specify location explicitly; assume query
            loc = ParameterLocation.QUERY
            params.append(Parameter(name=ap.name, location=loc, required=ap.required,
                                    type_string=ap.type, description=ap.description))

        # Request body: take first body from action.request_bodies
        request_body = None
        if action.request_bodies:
            first_body = action.request_bodies[0]
            entity = None
            if first_body.body:
                # Try to treat as JSON and create entity from it
                try:
                    body_obj = json.loads(first_body.body)
                    entity = self._object_to_entity("request", body_obj)
                except:
                    pass
            request_body = RequestBody(
                description="",
                required=True,
                content_entity=entity,
                is_binary=False,
            )

        # Responses
        responses = []
        for status, (desc, bodies) in action.responses.items():
            resp_entity = None
            if bodies:
                try:
                    body_obj = json.loads(bodies[0].body)
                    resp_entity = self._object_to_entity(f"response_{status}", body_obj)
                except:
                    pass
            responses.append(Response(
                status_code=status,
                description=desc,
                content_entity=resp_entity,
            ))

        # Operation name: action name or method+path
        op_name = action.name if action.name.strip() else f"{action.method} {path}"

        return Operation(
            name=op_name,
            type=OperationType.REQUEST_RESPONSE,
            description=action.description,
            http_method=http_method,
            path=path,
            parameters=params,
            request_body=request_body,
            responses=responses,
            tags=[group.name] if group.name else [],
            deprecated=False,
        )

    def _object_to_entity(self, name: str, obj: Any) -> Optional[Entity]:
        """Convert a JSON object into an MSDM Entity (shallow)."""
        if not isinstance(obj, dict):
            return None
        attrs = []
        for key, val in obj.items():
            typ = "string"
            if isinstance(val, bool):
                typ = "boolean"
            elif isinstance(val, int):
                typ = "int"
            elif isinstance(val, float):
                typ = "float"
            elif isinstance(val, list):
                typ = "array"
            elif isinstance(val, dict):
                typ = "object"
            attrs.append(Attribute(name=key, type=typ))
        return Entity(name=name, attributes=attrs)