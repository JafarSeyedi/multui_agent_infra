from __future__ import annotations

import pytest

from engines.session.models import Event, Session
from engines.session.service import BaseSessionService, InMemorySessionService


class TestInMemorySessionService:

    @pytest.fixture
    def service(self):
        return InMemorySessionService()

    async def test_create_and_get_session(self, service: InMemorySessionService):
        session = await service.create_session(
            app_name="test_app", user_id="user1", session_id="sess1"
        )
        assert session.app_name == "test_app"
        assert session.user_id == "user1"
        assert session.session_id == "sess1"
        assert session.state == {}
        assert session.events == []

        loaded = await service.get_session("test_app", "user1", "sess1")
        assert loaded is not None
        assert loaded.id == session.id

    async def test_get_session_not_found(self, service: InMemorySessionService):
        result = await service.get_session("nonexistent", "u", "s")
        assert result is None

    async def test_list_sessions(self, service: InMemorySessionService):
        await service.create_session("app1", "user1", "s1")
        await service.create_session("app1", "user1", "s2")
        await service.create_session("app1", "user2", "s3")

        sessions = await service.list_sessions("app1", "user1")
        assert len(sessions) == 2
        assert {s.session_id for s in sessions} == {"s1", "s2"}

    async def test_list_sessions_empty(self, service: InMemorySessionService):
        sessions = await service.list_sessions("app1", "user1")
        assert sessions == []

    async def test_delete_session(self, service: InMemorySessionService):
        await service.create_session("app1", "user1", "s1")
        await service.delete_session("app1", "user1", "s1")
        result = await service.get_session("app1", "user1", "s1")
        assert result is None

    async def test_delete_session_nonexistent(self, service: InMemorySessionService):
        await service.delete_session("app1", "user1", "nonexistent")

    async def test_append_event(self, service: InMemorySessionService):
        session = await service.create_session("app1", "user1", "s1")
        event = Event(author="user", content={"text": "hello"})
        await service.append_event(session, event)

        loaded = await service.get_session("app1", "user1", "s1")
        assert loaded is not None
        assert len(loaded.events) == 1
        assert loaded.events[0].content == {"text": "hello"}
        assert loaded.updated_at > session.created_at

    async def test_state_persistence(self, service: InMemorySessionService):
        session = await service.create_session("app1", "user1", "s1")
        session.state["counter"] = 1

        loaded = await service.get_session("app1", "user1", "s1")
        assert loaded is not None
        assert loaded.state["counter"] == 1

    async def test_session_idempotent_create(self, service: InMemorySessionService):
        s1 = await service.create_session("app1", "user1", "s1")
        s2 = await service.create_session("app1", "user1", "s1")
        assert s1.id == s2.id

    async def test_default_event_values(self):
        event = Event()
        assert event.author == "user"
        assert event.actions.state_delta == {}
        assert event.timestamp is not None
