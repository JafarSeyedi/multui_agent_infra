# engines/gateway/models/writers/api_writer.py
from __future__ import annotations

from ..gateway_models import ApiResponse


def write_api_response(response: ApiResponse) -> dict:
    return {"status_code": response.status_code, "body": response.body, "headers": response.headers}
