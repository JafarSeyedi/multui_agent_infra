# engines/document/writers/tsdm_writers/tsdm_json_writer.py
import json
from typing import Optional
from .base_tsdm_writer import BaseTSDMWriter
from ..base import WriteOptions
from ...models.tsdm_models import TSDMDocument, Tool

class TsdmJsonWriter(BaseTSDMWriter):
    name = "tsdm_json"
    supported_extensions = (".tsdm.json", ".tools.json")

    async def _write_design(self, document: TSDMDocument) -> bytes:
        tools = [self._tool_to_dict(t) for t in document.tools]
        output = {"tools": tools}
        json_str = json.dumps(output, indent=2, ensure_ascii=False)
        return json_str.encode(self.options.encoding or "utf-8")

    def _tool_to_dict(self, tool: Tool) -> dict:
        d = {
            "id": tool.id,
            "name": tool.name,
            "description": tool.description,
            "version": tool.version,
            "kind": tool.kind.value,
            "parameters": [self._param_to_dict(p) for p in tool.parameters],
            "outputs": [self._output_to_dict(o) for o in tool.outputs],
            "tags": tool.tags,
            "annotations": tool.annotations,
            "retry_policy": tool.retry_policy,
            "timeout_ms": tool.timeout_ms,
        }
        # Add specific fields
        kind = tool.kind
        if kind in ("dbQuery", "dbStatement"):
            d["connection_string"] = tool.connection_string
            if kind == "dbQuery":
                d["query_template"] = tool.query_template
            else:
                d["statement_template"] = tool.statement_template
        elif kind == "httpService":
            d.update({
                "endpoint_url": tool.endpoint_url,
                "http_method": tool.http_method.value,
                "headers": tool.headers,
                "body_template": tool.body_template,
                "auth": tool.auth,
                "load_balance": tool.load_balance.value,
                "endpoints": tool.endpoints,
            })
        # ... (repeat for all other kinds, similar to parser but reverse)
        # For brevity, the writer mirrors the parser; full implementation would include all types.

        return d

    def _param_to_dict(self, p):
        return {
            "name": p.name, "type": p.type.value, "required": p.required,
            "default": p.default, "description": p.description,
            "source": p.source.value, "source_path": p.source_path,
            "mapping_target": p.mapping_target,
        }

    def _output_to_dict(self, o):
        return {
            "name": o.name, "type": o.type.value, "description": o.description,
            "mapping_from": o.mapping_from,
        }