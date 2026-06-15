import pytest
from engines.tools.llm_gateway.gateway import LLMGateway, ModelResult


def test_model_result_defaults():
    mr = ModelResult(text="hello", model="gpt-4")
    assert mr.text == "hello"
    assert mr.model == "gpt-4"
    assert mr.cost == 0.0


@pytest.mark.asyncio
async def test_gateway_rejects_no_backend():
    gateway = LLMGateway()
    with pytest.raises(RuntimeError, match="No LLM gateway backend"):
        await gateway.route(model="gpt-4", prompt="test")
