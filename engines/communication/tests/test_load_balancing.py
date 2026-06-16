# engines/communication/tests/test_load_balancing.py
import pytest
from engines.communication.load_balancing.backends.round_robin.round_robin_lb import RoundRobinLoadBalancer
from engines.communication.models.communication_models import Endpoint


def test_round_robin():
    eps = [
        Endpoint(host="a", port=1, transport="http"),
        Endpoint(host="b", port=2, transport="http"),
    ]
    lb = RoundRobinLoadBalancer()
    assert lb.select(eps).host == "a"
    assert lb.select(eps).host == "b"
    assert lb.select(eps).host == "a"


def test_round_robin_empty():
    lb = RoundRobinLoadBalancer()
    with pytest.raises(ValueError, match="No endpoints"):
        lb.select([])
