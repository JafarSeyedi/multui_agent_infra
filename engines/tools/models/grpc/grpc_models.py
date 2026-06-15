from __future__ import annotations

from dataclasses import dataclass, field

from engines.tools.models.core.core_models import Tool
from engines.tools.models.core.core_models import ToolKind


@dataclass
class GrpcServiceTool(Tool):
    kind: ToolKind = ToolKind.GRPC_SERVICE
    host: str = ""
    port: int = 443
    service_name: str = ""
    method_name: str = ""
    proto_file_path: str = ""
    tls_config: dict[str, str] = field(default_factory=dict)
