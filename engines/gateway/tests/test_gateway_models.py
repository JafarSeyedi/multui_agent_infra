# engines/gateway/tests/test_gateway_models.py
from engines.gateway.models.gateway_models import ApiRequest, ApiResponse, RateLimitState
from engines.gateway.models.parsers.api_parser import parse_api_request
from engines.gateway.models.writers.api_writer import write_api_response


def test_api_request():
    req = ApiRequest(method="POST", path="/users")
    assert req.method == "POST"


def test_api_request_parse():
    data = {"method": "GET", "path": "/health", "headers": {"auth": "bearer"}}
    parsed = parse_api_request(data)
    assert parsed.path == "/health"


def test_api_response_write():
    resp = ApiResponse(status_code=201, body={"id": "1"})
    data = write_api_response(resp)
    assert data["status_code"] == 201
