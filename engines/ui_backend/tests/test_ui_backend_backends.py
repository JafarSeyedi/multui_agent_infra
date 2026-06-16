# engines/ui_backend/tests/test_ui_backend_backends.py
import pytest
from engines.ui_backend.backends.in_memory.in_memory_ui_backend import (
    InMemoryUIAdapter,
    InMemorySessionManager,
)


@pytest.mark.asyncio
async def test_ui_render():
    ui = InMemoryUIAdapter()
    result = await ui.render("Dialog", {"title": "Hello"})
    assert result["component"] == "Dialog"
    assert "<Dialog" in result["html"]


@pytest.mark.asyncio
async def test_ui_handle_action():
    ui = InMemoryUIAdapter()
    result = await ui.handle_action("click", {"button": "submit"})
    assert result["status"] == "handled"
    assert len(ui._actions) == 1


@pytest.mark.asyncio
async def test_session_create_get():
    mgr = InMemorySessionManager()
    sid = await mgr.create_session("alice")
    session = await mgr.get_session(sid)
    assert session is not None
    assert session["user_id"] == "alice"


@pytest.mark.asyncio
async def test_session_get_missing():
    mgr = InMemorySessionManager()
    session = await mgr.get_session("nonexistent")
    assert session is None


@pytest.mark.asyncio
async def test_session_destroy():
    mgr = InMemorySessionManager()
    sid = await mgr.create_session("bob")
    await mgr.destroy_session(sid)
    assert await mgr.get_session(sid) is None
