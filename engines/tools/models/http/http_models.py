from __future__ import annotations

from dataclasses import dataclass, field

from engines.document.models.ssdm_models import HttpMethod
from engines.tools.models.core.core_models import Tool
from engines.tools.models.core.core_models import ToolKind
from engines.tools.models.core.core_models import LoadBalanceStrategy


@dataclass
class HttpServiceTool(Tool):
    kind: ToolKind = ToolKind.HTTP_SERVICE
    endpoint_url: str = ""
    http_method: HttpMethod = HttpMethod.GET
    headers: dict[str, str] = field(default_factory=dict)
    body_template: str | None = None
    auth: str | None = None
    load_balance: LoadBalanceStrategy = LoadBalanceStrategy.ROUND_ROBIN
    endpoints: list[str] = field(default_factory=list)


@dataclass
class GraphQLTool(Tool):
    kind: ToolKind = ToolKind.GRAPHQL
    endpoint_url: str = ""
    query_template: str = ""
    variables: dict[str, str] = field(default_factory=dict)
