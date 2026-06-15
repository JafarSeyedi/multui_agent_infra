# Phase 1: Session & Runtime — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Session & Runtime layer — session lifecycle management, event tracking, and a Runner that wraps agent execution with session awareness.

**Architecture:** Plugin-based `BaseSessionService` ABC with `InMemorySessionService` default. `Runner` wraps any agent (or MultiAgentEngine) and manages session create/load/append lifecycle, yielding events as an async iterator.

**Tech Stack:** Python 3.11+, Pydantic v2, pytest with asyncio

---

## File Structure

| File | Responsibility |
|---|---|
| `engines/session/__init__.py` | Package exports |
| `engines/session/models.py` | Session, Event, EventActions models |
| `engines/session/service.py` | BaseSessionService ABC, InMemorySessionService |
| `engines/session/tests/__init__.py` | Test package |
| `engines/session/tests/test_session_service.py` | Session & service tests |
| `engines/orchestration/multi_agent/runner.py` | Runner class |
| `engines/orchestration/tests/test_multi_agent/__init__.py` | Already exists |
| `engines/orchestration/tests/test_multi_agent/test_runner.py` | Runner tests |

---

### Task 1: Session and Event models

**Files:**
- Create: `engines/session/__init__.py`
- Create: `engines/session/models.py`

- [ ] **Step 1: Create `engines/session/models.py`**

```python
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EventAuthor(str, Enum):
    USER = "user"
    AGENT = "agent"
    TOOL = "tool"


class EventActions(BaseModel):
    state_delta: dict[str, Any] = Field(default_factory=dict)
    artifact_delta: dict[str, Any] = Field(default_factory=dict)
    skip_summarization: bool = False


class Event(BaseModel):
    id: str = ""
    invocation_id: str = ""
    author: str = EventAuthor.USER
    content: dict[str, Any] | None = None
    actions: EventActions = Field(default_factory=EventActions)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Session(BaseModel):
    id: str
    app_name: str
    user_id: str
    session_id: str
    state: dict[str, Any] = Field(default_factory=dict)
    events: list[Event] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

- [ ] **Step 2: Create `engines/session/__init__.py`**

```python
from .models import Event, EventActions, Session
from .service import BaseSessionService, InMemorySessionService

__all__ = [
    "BaseSessionService",
    "Event",
    "EventActions",
    "InMemorySessionService",
    "Session",
]
```

- [ ] **Step 3: Commit**

```bash
git add engines/session/
git commit -m "feat(session): add Session and Event models"
```

---

### Task 2: SessionService ABC and InMemorySessionService

**Files:**
- Create: `engines/session/service.py`
- Create: `engines/session/tests/__init__.py`

- [ ] **Step 1: Write the failing test for InMemorySessionService**

Create `engines/session/tests/test_session_service.py`:

```python
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

    async def test_append_event_state_persistence(self, service: InMemorySessionService):
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest engines/session/tests/test_session_service.py -v`
Expected: ImportError — `BaseSessionService`, `InMemorySessionService` not defined

- [ ] **Step 3: Implement `engines/session/service.py`**

```python
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from .models import Event, Session


class BaseSessionService(ABC):
    @abstractmethod
    async def create_session(
        self, app_name: str, user_id: str, session_id: str,
    ) -> Session:
        ...

    @abstractmethod
    async def get_session(
        self, app_name: str, user_id: str, session_id: str,
    ) -> Session | None:
        ...

    @abstractmethod
    async def list_sessions(
        self, app_name: str, user_id: str,
    ) -> list[Session]:
        ...

    @abstractmethod
    async def delete_session(
        self, app_name: str, user_id: str, session_id: str,
    ) -> None:
        ...

    @abstractmethod
    async def append_event(
        self, session: Session, event: Event,
    ) -> None:
        ...


class InMemorySessionService(BaseSessionService):
    def __init__(self) -> None:
        self._sessions: dict[tuple[str, str, str], Session] = {}

    def _key(self, app_name: str, user_id: str, session_id: str) -> tuple[str, str, str]:
        return (app_name, user_id, session_id)

    async def create_session(
        self, app_name: str, user_id: str, session_id: str,
    ) -> Session:
        key = self._key(app_name, user_id, session_id)
        existing = self._sessions.get(key)
        if existing is not None:
            return existing
        session = Session(
            id=str(uuid.uuid4()),
            app_name=app_name,
            user_id=user_id,
            session_id=session_id,
        )
        self._sessions[key] = session
        return session

    async def get_session(
        self, app_name: str, user_id: str, session_id: str,
    ) -> Session | None:
        return self._sessions.get(self._key(app_name, user_id, session_id))

    async def list_sessions(
        self, app_name: str, user_id: str,
    ) -> list[Session]:
        prefix = (app_name, user_id)
        return [
            s for k, s in self._sessions.items()
            if k[:2] == prefix
        ]

    async def delete_session(
        self, app_name: str, user_id: str, session_id: str,
    ) -> None:
        self._sessions.pop(self._key(app_name, user_id, session_id), None)

    async def append_event(
        self, session: Session, event: Event,
    ) -> None:
        if not event.id:
            event.id = str(uuid.uuid4())
        session.events.append(event)
        session.updated_at = datetime.utcnow()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest engines/session/tests/test_session_service.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add engines/session/
git commit -m "feat(session): add BaseSessionService and InMemorySessionService"
```

---

### Task 3: Runner

**Files:**
- Create: `engines/orchestration/multi_agent/runner.py`
- Create: `engines/orchestration/tests/test_multi_agent/test_runner.py`

- [ ] **Step 1: Write the failing test for Runner**

Create `engines/orchestration/tests/test_multi_agent/test_runner.py`:

```python
from __future__ import annotations

import pytest

from engines.agent.models import AgentInput, AgentOutput
from engines.session.models import Event, EventAuthor
from engines.session.service import InMemorySessionService
from engines.orchestration.multi_agent.runner import Runner


class FakeAgent:
    def __init__(self):
        self.last_input: AgentInput | None = None

    async def run(self, input_data: AgentInput) -> AgentOutput:
        self.last_input = input_data
        return AgentOutput(
            agent_name="fake_agent",
            message=f"echo: {input_data.message}",
            payload={"echo": input_data.message},
        )


class TestRunner:

    @pytest.fixture
    def runner(self):
        agent = FakeAgent()
        session_service = InMemorySessionService()
        return Runner(
            agent=agent,
            app_name="test_app",
            session_service=session_service,
        )

    async def test_run_creates_session(self, runner: Runner):
        events = []
        async for event in runner.run_async(
            user_id="user1",
            session_id="sess1",
            new_message="hello",
        ):
            events.append(event)

        assert len(events) > 0
        session = await runner.session_service.get_session(
            "test_app", "user1", "sess1",
        )
        assert session is not None
        assert len(session.events) > 0

    async def test_run_yields_user_event_first(self, runner: Runner):
        events = []
        async for event in runner.run_async(
            user_id="user1", session_id="sess1", new_message="hello",
        ):
            events.append(event)

        assert events[0].author == "user"
        assert events[0].content == {"text": "hello"}

    async def test_run_yields_agent_event(self, runner: Runner):
        events = []
        async for event in runner.run_async(
            user_id="user1", session_id="sess1", new_message="hello",
        ):
            events.append(event)

        agent_events = [e for e in events if e.author == "agent"]
        assert len(agent_events) >= 1

    async def test_run_multiple_turns_same_session(self, runner: Runner):
        events_1 = []
        async for e in runner.run_async("user1", "sess1", "turn1"):
            events_1.append(e)

        events_2 = []
        async for e in runner.run_async("user1", "sess1", "turn2"):
            events_2.append(e)

        session = await runner.session_service.get_session(
            "test_app", "user1", "sess1",
        )
        assert session is not None
        assert len(session.events) >= 4

    async def test_run_different_sessions_isolated(self, runner: Runner):
        async for _ in runner.run_async("user1", "sess_a", "msg"):
            pass
        async for _ in runner.run_async("user1", "sess_b", "msg"):
            pass

        sess_a = await runner.session_service.get_session(
            "test_app", "user1", "sess_a",
        )
        sess_b = await runner.session_service.get_session(
            "test_app", "user1", "sess_b",
        )
        assert sess_a is not None
        assert sess_b is not None
        assert sess_a.id != sess_b.id

    async def test_run_state_persists_across_turns(self, runner: Runner):
        async for e in runner.run_async("user1", "sess1", "set count=1"):
            pass

        async for e in runner.run_async("user1", "sess1", "get count"):
            pass

        session = await runner.session_service.get_session(
            "test_app", "user1", "sess1",
        )
        assert session is not None
        assert len(session.events) == 2

    async def test_run_with_new_session_flag(self, runner: Runner):
        async for _ in runner.run_async("user1", "sess1", "first"):
            pass
        async for _ in runner.run_async("user1", "sess1", "second"):
            pass

        session = await runner.session_service.get_session(
            "test_app", "user1", "sess1",
        )
        assert session is not None
        assert len(session.events) == 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest engines/orchestration/tests/test_multi_agent/test_runner.py -v`
Expected: ImportError — `Runner` not defined

- [ ] **Step 3: Implement `engines/orchestration/multi_agent/runner.py`**

```python
from __future__ import annotations

import uuid
from typing import Any, AsyncIterator

from engines.agent.models import AgentInput, AgentOutput
from engines.session.models import Event, Session
from engines.session.service import BaseSessionService


class Runner:
    def __init__(
        self,
        agent: Any,
        app_name: str,
        session_service: BaseSessionService,
    ) -> None:
        self._agent = agent
        self._app_name = app_name
        self.session_service = session_service

    async def run_async(
        self,
        user_id: str,
        session_id: str,
        new_message: str,
    ) -> AsyncIterator[Event]:
        session = await self.session_service.create_session(
            self._app_name, user_id, session_id,
        )

        invocation_id = str(uuid.uuid4())

        user_event = Event(
            id=str(uuid.uuid4()),
            invocation_id=invocation_id,
            author="user",
            content={"text": new_message},
        )
        await self.session_service.append_event(session, user_event)
        yield user_event

        input_data = AgentInput(
            agent_name="runner",
            message=new_message,
            context={"session_id": session_id, "app_name": self._app_name},
            metadata={"invocation_id": invocation_id},
        )

        output: AgentOutput = await self._agent.run(input_data)

        agent_event = Event(
            id=str(uuid.uuid4()),
            invocation_id=invocation_id,
            author="agent",
            content={
                "text": output.message or "",
                "payload": output.payload,
            },
            actions=EventActions(
                state_delta={},
            ),
        )
        await self.session_service.append_event(session, agent_event)
        yield agent_event
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest engines/orchestration/tests/test_multi_agent/test_runner.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add engines/orchestration/multi_agent/runner.py engines/orchestration/tests/test_multi_agent/test_runner.py
git commit -m "feat(runner): add Runner with session lifecycle management"
```

---

### Task 4: Integration — Runner wraps MultiAgentEngine

**Files:**
- Modify: `engines/orchestration/multi_agent/runner.py`
- Create: No new files — update existing Runner

- [ ] **Step 1: Write integration test for Runner + MultiAgentEngine**

Add to `engines/orchestration/tests/test_multi_agent/test_runner.py`:

```python
async def test_runner_with_multi_agent_engine(
    runner_with_engine, sample_plan,
):
    events = []
    async for event in runner_with_engine.run_async(
        user_id="user1",
        session_id="sess1",
        new_message="execute plan",
    ):
        events.append(event)
    assert len(events) >= 1
```

- [ ] **Step 2: Update Runner to accept agent or engine**

The Runner needs to work both with a simple FakeAgent (above)
and with the existing MultiAgentEngine. Since MultiAgentEngine
uses `execute_instance(instance, definition)`, the Runner
translates the session-based input into an engine execution.

```python
from ..core.instance import InstanceState, ProcessInstance

class Runner:
    def __init__(
        self,
        agent: Any = None,
        app_name: str = "",
        session_service: BaseSessionService | None = None,
        multi_agent_engine: Any = None,
    ) -> None:
        self._agent = agent
        self._app_name = app_name
        self.session_service = session_service or InMemorySessionService()
        self._multi_agent_engine = multi_agent_engine

    async def run_async(
        self,
        user_id: str,
        session_id: str,
        new_message: str,
    ) -> AsyncIterator[Event]:
        session = await self.session_service.create_session(
            self._app_name, user_id, session_id,
        )

        invocation_id = str(uuid.uuid4())

        user_event = Event(
            id=str(uuid.uuid4()),
            invocation_id=invocation_id,
            author="user",
            content={"text": new_message},
        )
        await self.session_service.append_event(session, user_event)
        yield user_event

        if self._multi_agent_engine is not None:
            from ..core.engine import ProcessDefinition
            from ..core.instance import ProcessInstance

            instance = ProcessInstance(
                id=session_id,
                definition_id=session_id,
                variables={"user_message": new_message},
            )
            definition = ProcessDefinition(
                key=session_id,
                definition_xml={"message": new_message, "_engine_type": "multi_agent"},
            )
            await self._multi_agent_engine.execute_instance(instance, definition)

            agent_event = Event(
                id=str(uuid.uuid4()),
                invocation_id=invocation_id,
                author="agent",
                content={"text": f"engine executed instance {instance.id}"},
            )
        elif self._agent is not None:
            input_data = AgentInput(
                agent_name="runner",
                message=new_message,
                context={"session_id": session_id, "app_name": self._app_name},
                metadata={"invocation_id": invocation_id},
            )
            output: AgentOutput = await self._agent.run(input_data)
            agent_event = Event(
                id=str(uuid.uuid4()),
                invocation_id=invocation_id,
                author="agent",
                content={"text": output.message or "", "payload": output.payload},
            )
        else:
            raise ValueError("Runner requires either agent or multi_agent_engine")

        await self.session_service.append_event(session, agent_event)
        yield agent_event
```

- [ ] **Step 3: Run all tests**

Run: `python3 -m pytest engines/session/tests/ engines/orchestration/tests/test_multi_agent/ -v`
Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add engines/orchestration/multi_agent/runner.py engines/orchestration/tests/test_multi_agent/test_runner.py
git commit -m "feat(runner): support MultiAgentEngine integration"
```

---

### Task 5: Run full test suite and verify nothing is broken

- [ ] **Step 1: Run all session and multi_agent tests**

Run: `python3 -m pytest engines/session/tests/ engines/orchestration/tests/test_multi_agent/ -v`
Expected: All tests PASS

- [ ] **Step 2: Run broader test suite to check for regressions**

Run: `python3 -m pytest engines/agent/tests/ engines/orchestration/tests/ -v --timeout=60`
Expected: All tests PASS (or pre-existing failures unchanged)

- [ ] **Step 3: Commit final state**

```bash
git add -A
git commit -m "chore: verify Phase 1 tests pass with no regressions"
```
