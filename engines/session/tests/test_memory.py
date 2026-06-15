from __future__ import annotations

import pytest

from engines.session.memory import InMemoryMemoryService, MemoryEntry, SearchMemoryResponse
from engines.session.models import Event, Session


class TestInMemoryMemoryService:

    @pytest.fixture
    def service(self):
        return InMemoryMemoryService()

    def _make_session(self, app_name="app1", user_id="user1", session_id="s1", events=None):
        if events is None:
            events = [
                Event(author="user", content={"text": "hello world"}),
                Event(author="agent", content={"text": "hi there"}),
                Event(author="user", content={"text": "what is the weather?"}),
            ]
        return Session(
            id="sid1", app_name=app_name, user_id=user_id,
            session_id=session_id, events=events,
        )

    async def test_add_session_to_memory(self, service):
        session = self._make_session()
        await service.add_session_to_memory(session)

        result = await service.search_memory("app1", "user1", "")
        assert len(result.memories) == 3

    async def test_search_memory_finds_matching(self, service):
        session = self._make_session()
        await service.add_session_to_memory(session)

        result = await service.search_memory("app1", "user1", "weather")
        assert len(result.memories) == 1
        assert "weather" in result.memories[0].content

    async def test_search_memory_no_match(self, service):
        session = self._make_session()
        await service.add_session_to_memory(session)

        result = await service.search_memory("app1", "user1", "nonexistent")
        assert len(result.memories) == 0

    async def test_search_memory_empty_query_returns_all(self, service):
        session = self._make_session()
        await service.add_session_to_memory(session)

        result = await service.search_memory("app1", "user1", "")
        assert len(result.memories) == 3

    async def test_search_empty_store(self, service):
        result = await service.search_memory("app1", "user1", "hello")
        assert len(result.memories) == 0

    async def test_multiple_sessions_same_user(self, service):
        s1 = self._make_session(session_id="s1", events=[
            Event(author="user", content={"text": "from session 1"}),
        ])
        s2 = self._make_session(session_id="s2", events=[
            Event(author="user", content={"text": "from session 2"}),
        ])
        await service.add_session_to_memory(s1)
        await service.add_session_to_memory(s2)

        result = await service.search_memory("app1", "user1", "")
        assert len(result.memories) == 2

    async def test_different_users_isolated(self, service):
        s1 = self._make_session(user_id="user1", events=[
            Event(author="user", content={"text": "user1 data"}),
        ])
        s2 = self._make_session(user_id="user2", events=[
            Event(author="user", content={"text": "user2 data"}),
        ])
        await service.add_session_to_memory(s1)
        await service.add_session_to_memory(s2)

        result = await service.search_memory("app1", "user1", "")
        assert len(result.memories) == 1
        assert "user1" in result.memories[0].content

    async def test_memory_entry_has_author_and_timestamp(self, service):
        session = self._make_session()
        await service.add_session_to_memory(session)

        result = await service.search_memory("app1", "user1", "")
        entry = result.memories[0]
        assert entry.author == "user"
        assert entry.timestamp != ""

    async def test_case_insensitive_search(self, service):
        session = self._make_session(events=[
            Event(author="user", content={"text": "Hello World"}),
        ])
        await service.add_session_to_memory(session)

        result = await service.search_memory("app1", "user1", "hello")
        assert len(result.memories) == 1
