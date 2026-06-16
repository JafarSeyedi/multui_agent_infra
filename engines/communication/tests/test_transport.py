# engines/communication/tests/test_transport.py
import pytest


@pytest.mark.asyncio
async def test_http_transport_init():
    from engines.communication.transport.backends.http.http_transport import HttpTransport
    transport = HttpTransport()
    assert transport.name == "http"


@pytest.mark.asyncio
async def test_stdio_transport_init():
    from engines.communication.transport.backends.stdio.stdio_transport import StdioTransport
    transport = StdioTransport(command="echo")
    assert transport.name == "stdio"
