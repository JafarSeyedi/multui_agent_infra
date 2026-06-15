from __future__ import annotations

import uuid
from typing import Any, AsyncIterator

from engines.agent.models import AgentInput, AgentOutput
from engines.session.models import Event, EventActions
from engines.session.service import BaseSessionService, InMemorySessionService


class Runner:
    def __init__(
        self,
        agent: Any,
        app_name: str,
        session_service: BaseSessionService | None = None,
    ) -> None:
        self._agent = agent
        self._app_name = app_name
        self.session_service = session_service or InMemorySessionService()

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
            actions=EventActions(state_delta={}),
        )
        await self.session_service.append_event(session, agent_event)
        yield agent_event
