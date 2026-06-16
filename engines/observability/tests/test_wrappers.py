import pytest
from engines.observability.core.wrappers import wrap_registry


class FakeRegistry:
    def __init__(self):
        self.calls = []

    async def run(self, name: str, data: dict) -> dict:
        self.calls.append((name, data))
        return {"result": "ok"}


class FakeBackend:
    def __init__(self):
        self.spans = []

    async def start_span(self, name, attributes=None):
        self.spans.append(("start", name, attributes))
        return "span-1"

    async def end_span(self, span, status="ok"):
        self.spans.append(("end", span, status))

    async def record_metric(self, name, value, tags=None):
        pass

    async def record_event(self, name, attributes=None):
        pass


@pytest.mark.asyncio
async def test_wrap_registry_instruments_run():
    registry = FakeRegistry()
    backend = FakeBackend()
    wrapped = wrap_registry(registry, backend, "agent")
    result = await wrapped.run("test-agent", {"key": "val"})
    assert result == {"result": "ok"}
    assert any("start" in s for s in backend.spans)
    assert any("end" in s for s in backend.spans)
