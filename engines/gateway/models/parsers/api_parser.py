# engines/gateway/models/parsers/api_parser.py
from __future__ import annotations

from ..gateway_models import ApiRequest


def parse_api_request(data: dict) -> ApiRequest:
    return ApiRequest(
        method=data.get("method", "GET"),
        path=data.get("path", "/"),
        headers=data.get("headers", {}),
        body=data.get("body"),
    )
