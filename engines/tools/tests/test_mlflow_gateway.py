import pytest
from engines.tools.llm_gateway.backends.mlflow import MLflowGatewayBackend


def test_mlflow_backend_identity():
    backend = MLflowGatewayBackend(gateway_uri="http://localhost:5000")
    assert backend.gateway_uri == "http://localhost:5000"
